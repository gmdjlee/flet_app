"""Synchronization service for syncing DART data to local SQLite database."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from src.models.corporation import Corporation
from src.models.financial_statement import FinancialStatement
from src.services.corporation_service import CorporationService
from src.services.dart_service import DartService, DartServiceError

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Synchronization status enum."""

    IDLE = "idle"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SyncProgress:
    """Data class for tracking sync progress."""

    status: SyncStatus
    current: int
    total: int
    message: str
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100

    @property
    def elapsed_seconds(self) -> float | None:
        """Calculate elapsed time in seconds."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()


class SyncService:
    """Service for synchronizing DART data with local SQLite database.

    Provides methods to sync corporation lists, company info, and
    financial statements from DART API to local storage.

    Attributes:
        dart_service: DART API service instance.
        session: SQLAlchemy database session.
        corp_service: Corporation service instance.
    """

    # Rate limiting settings
    DEFAULT_RATE_LIMIT_DELAY = 0.5  # seconds between API calls
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0  # base delay for exponential backoff

    def __init__(
        self,
        dart_service: DartService,
        session: Session,
        rate_limit_delay: float | None = None,
    ):
        """Initialize sync service.

        Args:
            dart_service: DART API service instance.
            session: SQLAlchemy database session.
            rate_limit_delay: Delay between API calls in seconds.
        """
        self.dart_service = dart_service
        self.session = session
        self.corp_service = CorporationService(session)
        self.rate_limit_delay = rate_limit_delay or self.DEFAULT_RATE_LIMIT_DELAY

        self._progress = SyncProgress(
            status=SyncStatus.IDLE,
            current=0,
            total=0,
            message="",
        )
        self._cancelled = False
        self._progress_callback: Callable[[SyncProgress], None] | None = None

    @property
    def progress(self) -> SyncProgress:
        """Get current sync progress."""
        return self._progress

    def set_progress_callback(self, callback: Callable[[SyncProgress], None] | None) -> None:
        """Set callback function for progress updates.

        Args:
            callback: Function to call with progress updates.
        """
        self._progress_callback = callback

    def cancel(self) -> None:
        """Cancel ongoing synchronization."""
        self._cancelled = True

    def _update_progress(
        self,
        current: int | None = None,
        total: int | None = None,
        message: str | None = None,
        status: SyncStatus | None = None,
        error: str | None = None,
    ) -> None:
        """Update sync progress and notify callback."""
        if current is not None:
            self._progress.current = current
        if total is not None:
            self._progress.total = total
        if message is not None:
            self._progress.message = message
        if status is not None:
            self._progress.status = status
        if error is not None:
            self._progress.error = error

        if self._progress_callback:
            self._progress_callback(self._progress)

    async def _with_retry(
        self,
        operation: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """Execute operation with retry logic.

        Args:
            operation: Async callable to execute.
            *args: Positional arguments for operation.
            **kwargs: Keyword arguments for operation.

        Returns:
            Operation result.

        Raises:
            DartServiceError: If all retries fail.
        """
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                return await operation(*args, **kwargs)
            except DartServiceError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_BASE_DELAY * (2**attempt)
                    logger.warning(f"Retry {attempt + 1}/{self.MAX_RETRIES} after {delay}s: {e}")
                    await asyncio.sleep(delay)

        raise last_error or DartServiceError("Unknown error")

    async def sync_corporation_list(
        self,
        market: str | None = None,
    ) -> SyncProgress:
        """Sync corporation list from DART to local database.

        Args:
            market: Optional market filter (KOSPI, KOSDAQ, etc.)

        Returns:
            Final SyncProgress object.
        """
        self._cancelled = False
        self._progress = SyncProgress(
            status=SyncStatus.SYNCING,
            current=0,
            total=0,
            message="기업 목록 가져오는 중...",
            started_at=datetime.now(),
        )
        self._update_progress()

        try:
            # Fetch corporation list from DART
            corps = await self._with_retry(
                self.dart_service.get_corporation_list,
                market=market,
            )

            total = len(corps)
            self._update_progress(total=total, message=f"{total}개 기업 동기화 중...")

            synced = 0
            for i, corp_data in enumerate(corps):
                if self._cancelled:
                    self._update_progress(
                        status=SyncStatus.CANCELLED,
                        message="동기화가 취소되었습니다.",
                    )
                    return self._progress

                # Map DART API fields to our model
                corp_dict = self._map_corporation_data(corp_data)

                # Upsert corporation
                self.corp_service.upsert(corp_dict)
                synced += 1

                self._update_progress(
                    current=synced,
                    message=f"동기화 중... {synced}/{total}",
                )

                # Rate limiting
                if i < total - 1:
                    await asyncio.sleep(self.rate_limit_delay / 10)  # Faster for list

            self._progress.completed_at = datetime.now()
            self._update_progress(
                status=SyncStatus.COMPLETED,
                message=f"{synced}개 기업 동기화 완료",
            )

            logger.info(f"Corporation sync completed: {synced} corporations")
            return self._progress

        except Exception as e:
            logger.error(f"Corporation sync failed: {e}")
            self._update_progress(
                status=SyncStatus.FAILED,
                error=str(e),
                message="동기화 실패",
            )
            return self._progress

    async def sync_corporation_info(
        self,
        corp_code: str,
    ) -> Corporation | None:
        """Sync detailed info for a single corporation.

        Args:
            corp_code: DART corporation code.

        Returns:
            Updated Corporation instance or None on failure.
        """
        try:
            info = await self._with_retry(
                self.dart_service.get_corporation_info,
                corp_code,
            )

            # Map and upsert
            corp_dict = self._map_corporation_data(info)
            corp = self.corp_service.upsert(corp_dict)

            await asyncio.sleep(self.rate_limit_delay)
            return corp

        except DartServiceError as e:
            logger.error(f"Failed to sync corporation info {corp_code}: {e}")
            return None

    async def sync_financial_statements(
        self,
        corp_code: str,
        years: list[str] | None = None,
        reprt_codes: list[str] | None = None,
    ) -> int:
        """Sync financial statements for a corporation.

        Args:
            corp_code: DART corporation code.
            years: List of business years to sync. Defaults to last 3 years.
            reprt_codes: List of report codes. Defaults to annual report only.

        Returns:
            Number of statements synced.
        """
        if years is None:
            current_year = datetime.now().year
            years = [str(y) for y in range(current_year - 2, current_year + 1)]

        if reprt_codes is None:
            reprt_codes = ["11011"]  # Annual report only

        synced = 0

        for year in years:
            for reprt_code in reprt_codes:
                if self._cancelled:
                    return synced

                try:
                    statements = await self._with_retry(
                        self.dart_service.get_financial_statements,
                        corp_code=corp_code,
                        bsns_year=year,
                        reprt_code=reprt_code,
                    )

                    for stmt_data in statements:
                        stmt = self._map_financial_statement(stmt_data, corp_code)
                        self._upsert_financial_statement(stmt)
                        synced += 1

                    await asyncio.sleep(self.rate_limit_delay)

                except DartServiceError as e:
                    logger.warning(
                        f"Failed to sync financial statements for "
                        f"{corp_code}/{year}/{reprt_code}: {e}"
                    )
                    continue

        return synced

    async def sync_all_corporation_info(
        self,
        corp_codes: list[str] | None = None,
    ) -> SyncProgress:
        """Sync detailed info for multiple corporations.

        Args:
            corp_codes: List of corp_codes to sync. If None, syncs all.

        Returns:
            Final SyncProgress object.
        """
        self._cancelled = False
        self._progress = SyncProgress(
            status=SyncStatus.SYNCING,
            current=0,
            total=0,
            message="기업 상세 정보 동기화 중...",
            started_at=datetime.now(),
        )

        try:
            if corp_codes is None:
                # Get all corporations from database
                corps = self.session.query(Corporation).all()
                corp_codes = [c.corp_code for c in corps]

            total = len(corp_codes)
            self._update_progress(total=total)

            synced = 0
            for corp_code in corp_codes:
                if self._cancelled:
                    self._update_progress(
                        status=SyncStatus.CANCELLED,
                        message="동기화가 취소되었습니다.",
                    )
                    return self._progress

                result = await self.sync_corporation_info(corp_code)
                if result:
                    synced += 1

                self._update_progress(
                    current=synced,
                    message=f"상세 정보 동기화 중... {synced}/{total}",
                )

            self._progress.completed_at = datetime.now()
            self._update_progress(
                status=SyncStatus.COMPLETED,
                message=f"{synced}개 기업 상세 정보 동기화 완료",
            )

            return self._progress

        except Exception as e:
            logger.error(f"Corporation info sync failed: {e}")
            self._update_progress(
                status=SyncStatus.FAILED,
                error=str(e),
                message="동기화 실패",
            )
            return self._progress

    def _map_corporation_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map DART API corporation data to model fields.

        Args:
            data: Raw DART API response data.

        Returns:
            Mapped dictionary for Corporation model.
        """
        # DART API field mapping
        corp_cls = data.get("corp_cls", "E")
        market_map = {"Y": "KOSPI", "K": "KOSDAQ", "N": "KONEX", "E": None}

        return {
            "corp_code": data.get("corp_code"),
            "corp_name": data.get("corp_name"),
            "stock_code": data.get("stock_code") or None,
            "corp_cls": corp_cls,
            "market": market_map.get(corp_cls),
            "modify_date": data.get("modify_date"),
            "ceo_nm": data.get("ceo_nm"),
            "corp_name_eng": data.get("corp_name_eng"),
            "jurir_no": data.get("jurir_no"),
            "bizr_no": data.get("bizr_no"),
            "adres": data.get("adres"),
            "hm_url": data.get("hm_url"),
            "ir_url": data.get("ir_url"),
            "phn_no": data.get("phn_no"),
            "fax_no": data.get("fax_no"),
            "induty_code": data.get("induty_code"),
            "est_dt": data.get("est_dt"),
            "acc_mt": data.get("acc_mt"),
        }

    def _map_financial_statement(self, data: dict[str, Any], corp_code: str) -> dict[str, Any]:
        """Map DART API financial statement data to model fields.

        Args:
            data: Raw DART API response data.
            corp_code: Corporation code.

        Returns:
            Mapped dictionary for FinancialStatement model.
        """

        def parse_amount(value: Any) -> int | None:
            """Parse amount string to integer."""
            if value is None or value == "":
                return None
            try:
                # Remove commas and convert
                return int(str(value).replace(",", ""))
            except (ValueError, TypeError):
                return None

        return {
            "corp_code": corp_code,
            "bsns_year": data.get("bsns_year"),
            "reprt_code": data.get("reprt_code"),
            "fs_div": data.get("fs_div"),
            "sj_div": data.get("sj_div"),
            "account_id": data.get("account_id"),
            "account_nm": data.get("account_nm"),
            "account_detail": data.get("account_detail"),
            "thstrm_nm": data.get("thstrm_nm"),
            "thstrm_amount": parse_amount(data.get("thstrm_amount")),
            "frmtrm_nm": data.get("frmtrm_nm"),
            "frmtrm_amount": parse_amount(data.get("frmtrm_amount")),
            "bfefrmtrm_nm": data.get("bfefrmtrm_nm"),
            "bfefrmtrm_amount": parse_amount(data.get("bfefrmtrm_amount")),
            "ord": data.get("ord"),
            "currency": data.get("currency", "KRW"),
        }

    def _upsert_financial_statement(self, data: dict[str, Any]) -> FinancialStatement:
        """Upsert a financial statement record.

        Args:
            data: Financial statement data dictionary.

        Returns:
            Created or updated FinancialStatement instance.
        """
        # Find existing by composite key
        existing = (
            self.session.query(FinancialStatement)
            .filter_by(
                corp_code=data["corp_code"],
                bsns_year=data["bsns_year"],
                reprt_code=data["reprt_code"],
                fs_div=data["fs_div"],
                sj_div=data["sj_div"],
                account_nm=data["account_nm"],
            )
            .first()
        )

        if existing:
            # Update existing
            for key, value in data.items():
                if hasattr(existing, key) and key != "id":
                    setattr(existing, key, value)
            self.session.commit()
            return existing
        else:
            # Create new
            stmt = FinancialStatement(**data)
            self.session.add(stmt)
            self.session.commit()
            self.session.refresh(stmt)
            return stmt
