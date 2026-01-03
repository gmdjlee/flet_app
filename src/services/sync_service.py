"""Synchronization service for syncing DART data to local SQLite database."""

import asyncio
import json
import logging
import os
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from src.models.corporation import Corporation
from src.models.financial_statement import FinancialStatement
from src.services.corporation_service import CorporationService
from src.services.dart_service import DartService, DartServiceError

logger = logging.getLogger(__name__)

# Default data directory for logs and settings
DATA_DIR = Path.home() / ".dart-db-flet" / "data"
LOGS_DIR = DATA_DIR / "logs"
SETTINGS_FILE = DATA_DIR / "settings.json"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"

# Checkpoint settings
CHECKPOINT_SAVE_INTERVAL = 50  # Save checkpoint every N items


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


@dataclass
class SyncLogEntry:
    """Data class for a single sync log entry."""

    timestamp: str
    level: str  # INFO, WARNING, ERROR
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncLog:
    """Data class for complete sync log."""

    sync_type: str  # corporation_list, corporation_info, financial_statements
    started_at: str
    completed_at: str | None = None
    status: str = "running"
    total_items: int = 0
    processed_items: int = 0
    success_count: int = 0
    error_count: int = 0
    entries: list[SyncLogEntry] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def add_entry(
        self,
        level: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add a log entry."""
        self.entries.append(
            SyncLogEntry(
                timestamp=datetime.now().isoformat(),
                level=level,
                message=message,
                details=details or {},
            )
        )

    def add_error(
        self,
        message: str,
        item_id: str | None = None,
        error_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add an error record."""
        self.error_count += 1
        self.errors.append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "item_id": item_id,
                "error_type": error_type,
                "details": details or {},
            }
        )
        self.add_entry("ERROR", message, {"item_id": item_id, "error_type": error_type})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sync_type": self.sync_type,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "entries": [asdict(e) for e in self.entries],
            "errors": self.errors,
        }


@dataclass
class SyncCheckpoint:
    """Data class for sync checkpoint to enable resume functionality."""

    sync_type: str  # corporation_list, financial_statements
    started_at: str  # ISO format timestamp
    last_updated_at: str  # ISO format timestamp
    total_items: int  # Total number of items to process
    processed_count: int  # Number of items already processed
    processed_items: list[str]  # List of processed item IDs (corp_codes)
    remaining_items: list[str]  # List of remaining item IDs to process
    sync_params: dict[str, Any] = field(default_factory=dict)  # Additional sync parameters

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_count / self.total_items) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sync_type": self.sync_type,
            "started_at": self.started_at,
            "last_updated_at": self.last_updated_at,
            "total_items": self.total_items,
            "processed_count": self.processed_count,
            "processed_items": self.processed_items,
            "remaining_items": self.remaining_items,
            "sync_params": self.sync_params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SyncCheckpoint":
        """Create SyncCheckpoint from dictionary."""
        return cls(
            sync_type=data["sync_type"],
            started_at=data["started_at"],
            last_updated_at=data["last_updated_at"],
            total_items=data["total_items"],
            processed_count=data["processed_count"],
            processed_items=data.get("processed_items", []),
            remaining_items=data.get("remaining_items", []),
            sync_params=data.get("sync_params", {}),
        )


class CheckpointManager:
    """Manager for sync checkpoints to enable resume functionality."""

    def __init__(self, checkpoint_dir: Path | None = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files.
        """
        self.checkpoint_dir = checkpoint_dir or CHECKPOINT_DIR
        self._ensure_checkpoint_dir()

    def _ensure_checkpoint_dir(self) -> None:
        """Ensure checkpoint directory exists."""
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_path(self, sync_type: str) -> Path:
        """Get checkpoint file path for a sync type."""
        return self.checkpoint_dir / f"checkpoint_{sync_type}.json"

    def save_checkpoint(self, checkpoint: SyncCheckpoint) -> Path:
        """Save checkpoint to file.

        Args:
            checkpoint: SyncCheckpoint instance to save.

        Returns:
            Path to saved checkpoint file.
        """
        self._ensure_checkpoint_dir()
        checkpoint.last_updated_at = datetime.now().isoformat()
        filepath = self._get_checkpoint_path(checkpoint.sync_type)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, ensure_ascii=False, indent=2)

        logger.debug(f"Checkpoint saved: {filepath}")
        return filepath

    def load_checkpoint(self, sync_type: str) -> SyncCheckpoint | None:
        """Load checkpoint from file.

        Args:
            sync_type: Type of sync to load checkpoint for.

        Returns:
            SyncCheckpoint instance or None if not found.
        """
        filepath = self._get_checkpoint_path(sync_type)
        if not filepath.exists():
            return None

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
                return SyncCheckpoint.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning(f"Failed to load checkpoint {filepath}: {e}")
            return None

    def has_checkpoint(self, sync_type: str) -> bool:
        """Check if checkpoint exists for a sync type.

        Args:
            sync_type: Type of sync to check.

        Returns:
            True if checkpoint exists.
        """
        return self._get_checkpoint_path(sync_type).exists()

    def clear_checkpoint(self, sync_type: str) -> bool:
        """Clear checkpoint for a sync type.

        Args:
            sync_type: Type of sync to clear checkpoint for.

        Returns:
            True if checkpoint was cleared.
        """
        filepath = self._get_checkpoint_path(sync_type)
        if filepath.exists():
            try:
                filepath.unlink()
                logger.debug(f"Checkpoint cleared: {filepath}")
                return True
            except OSError as e:
                logger.warning(f"Failed to clear checkpoint {filepath}: {e}")
                return False
        return False

    def get_all_checkpoints(self) -> list[SyncCheckpoint]:
        """Get all available checkpoints.

        Returns:
            List of SyncCheckpoint instances.
        """
        self._ensure_checkpoint_dir()
        checkpoints = []

        for filepath in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                    checkpoints.append(SyncCheckpoint.from_dict(data))
            except (json.JSONDecodeError, OSError, KeyError) as e:
                logger.warning(f"Failed to load checkpoint {filepath}: {e}")

        return checkpoints


class SyncLogger:
    """Logger for sync operations that saves to file."""

    def __init__(self, logs_dir: Path | None = None):
        """Initialize sync logger.

        Args:
            logs_dir: Directory to store log files.
        """
        self.logs_dir = logs_dir or LOGS_DIR
        self._ensure_logs_dir()

    def _ensure_logs_dir(self) -> None:
        """Ensure logs directory exists."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def save_log(self, log: SyncLog) -> Path:
        """Save sync log to file.

        Args:
            log: SyncLog instance to save.

        Returns:
            Path to saved log file.
        """
        self._ensure_logs_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # Include microseconds
        filename = f"sync_{log.sync_type}_{timestamp}.json"
        filepath = self.logs_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log.to_dict(), f, ensure_ascii=False, indent=2)

        return filepath

    def get_recent_logs(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent sync logs.

        Args:
            limit: Maximum number of logs to return.

        Returns:
            List of log dictionaries.
        """
        self._ensure_logs_dir()
        log_files = sorted(
            self.logs_dir.glob("sync_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        logs = []
        for filepath in log_files[:limit]:
            try:
                with open(filepath, encoding="utf-8") as f:
                    log_data = json.load(f)
                    log_data["filepath"] = str(filepath)
                    logs.append(log_data)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to read log file {filepath}: {e}")

        return logs

    def get_log(self, filepath: str) -> dict[str, Any] | None:
        """Get a specific sync log by filepath.

        Args:
            filepath: Path to log file.

        Returns:
            Log dictionary or None if not found.
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, FileNotFoundError):
            return None


class SettingsManager:
    """Manager for application settings including API key."""

    def __init__(self, settings_file: Path | None = None):
        """Initialize settings manager.

        Args:
            settings_file: Path to settings file.
        """
        self.settings_file = settings_file or SETTINGS_FILE
        self._ensure_settings_dir()

    def _ensure_settings_dir(self) -> None:
        """Ensure settings directory exists."""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_settings(self) -> dict[str, Any]:
        """Load settings from file."""
        if not self.settings_file.exists():
            return {}
        try:
            with open(self.settings_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_settings(self, settings: dict[str, Any]) -> None:
        """Save settings to file."""
        self._ensure_settings_dir()
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def get_api_key(self) -> str | None:
        """Get DART API key.

        Returns:
            API key or None if not set.
        """
        # First check environment variable
        env_key = os.environ.get("DART_API_KEY")
        if env_key:
            return env_key

        # Then check settings file
        settings = self._load_settings()
        return settings.get("dart_api_key")

    def set_api_key(self, api_key: str) -> None:
        """Set DART API key.

        Args:
            api_key: DART API key to save.
        """
        settings = self._load_settings()
        settings["dart_api_key"] = api_key
        self._save_settings(settings)

    def get_sync_settings(self) -> dict[str, Any]:
        """Get sync settings.

        Returns:
            Sync settings dictionary.
        """
        settings = self._load_settings()
        return settings.get(
            "sync",
            {
                "rate_limit_delay": 0.5,
                "max_retries": 3,
                "auto_sync_on_start": False,
            },
        )

    def set_sync_settings(self, sync_settings: dict[str, Any]) -> None:
        """Set sync settings.

        Args:
            sync_settings: Sync settings to save.
        """
        settings = self._load_settings()
        settings["sync"] = sync_settings
        self._save_settings(settings)

    def get_last_sync_time(self, sync_type: str) -> str | None:
        """Get last sync time for a sync type.

        Args:
            sync_type: Type of sync (e.g., 'corporation_list').

        Returns:
            ISO format timestamp or None.
        """
        settings = self._load_settings()
        return settings.get("last_sync", {}).get(sync_type)

    def set_last_sync_time(self, sync_type: str, timestamp: datetime | None = None) -> None:
        """Set last sync time for a sync type.

        Args:
            sync_type: Type of sync.
            timestamp: Timestamp to set. Defaults to now.
        """
        settings = self._load_settings()
        if "last_sync" not in settings:
            settings["last_sync"] = {}
        settings["last_sync"][sync_type] = (timestamp or datetime.now()).isoformat()
        self._save_settings(settings)


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
        sync_logger: SyncLogger | None = None,
        settings_manager: SettingsManager | None = None,
        checkpoint_manager: CheckpointManager | None = None,
    ):
        """Initialize sync service.

        Args:
            dart_service: DART API service instance.
            session: SQLAlchemy database session.
            rate_limit_delay: Delay between API calls in seconds.
            sync_logger: SyncLogger instance for logging sync operations.
            settings_manager: SettingsManager instance for settings.
            checkpoint_manager: CheckpointManager instance for resume functionality.
        """
        self.dart_service = dart_service
        self.session = session
        self.corp_service = CorporationService(session)
        self.rate_limit_delay = rate_limit_delay or self.DEFAULT_RATE_LIMIT_DELAY
        self.sync_logger = sync_logger or SyncLogger()
        self.settings_manager = settings_manager or SettingsManager()
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()

        self._progress = SyncProgress(
            status=SyncStatus.IDLE,
            current=0,
            total=0,
            message="",
        )
        self._cancelled = False
        self._progress_callback: Callable[[SyncProgress], None] | None = None
        self._current_log: SyncLog | None = None
        self._current_checkpoint: SyncCheckpoint | None = None

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

    def _start_sync_log(self, sync_type: str) -> SyncLog:
        """Start a new sync log.

        Args:
            sync_type: Type of sync operation.

        Returns:
            New SyncLog instance.
        """
        self._current_log = SyncLog(
            sync_type=sync_type,
            started_at=datetime.now().isoformat(),
        )
        self._current_log.add_entry("INFO", f"{sync_type} 동기화 시작")
        return self._current_log

    def _finish_sync_log(self, status: str) -> None:
        """Finish current sync log and save.

        Args:
            status: Final status (completed, failed, cancelled).
        """
        if self._current_log:
            self._current_log.completed_at = datetime.now().isoformat()
            self._current_log.status = status
            self._current_log.add_entry(
                "INFO" if status == "completed" else "WARNING",
                f"동기화 {status}: {self._current_log.success_count} 성공, {self._current_log.error_count} 실패",
            )
            self.sync_logger.save_log(self._current_log)
            self.settings_manager.set_last_sync_time(self._current_log.sync_type)

    async def sync_corporation_list(
        self,
        market: str | None = None,
        resume: bool = False,
    ) -> SyncProgress:
        """Sync corporation list from DART to local database.

        Args:
            market: Optional market filter (KOSPI, KOSDAQ, etc.)
            resume: If True, resume from last checkpoint.

        Returns:
            Final SyncProgress object.
        """
        self._cancelled = False
        sync_type = "corporation_list"

        # Check for existing checkpoint if resume is requested
        checkpoint = None
        processed_corp_codes: set[str] = set()

        if resume:
            checkpoint = self.checkpoint_manager.load_checkpoint(sync_type)
            if checkpoint:
                processed_corp_codes = set(checkpoint.processed_items)
                logger.info(
                    f"Resuming corporation sync from checkpoint: "
                    f"{checkpoint.processed_count}/{checkpoint.total_items}"
                )

        self._progress = SyncProgress(
            status=SyncStatus.SYNCING,
            current=checkpoint.processed_count if checkpoint else 0,
            total=checkpoint.total_items if checkpoint else 0,
            message="기업 목록 가져오는 중..." if not checkpoint else "동기화 재개 중...",
            started_at=datetime.fromisoformat(checkpoint.started_at) if checkpoint else datetime.now(),
        )
        self._update_progress()

        # Start logging
        sync_log = self._start_sync_log(sync_type)
        if checkpoint:
            sync_log.add_entry("INFO", f"체크포인트에서 재개: {checkpoint.processed_count}/{checkpoint.total_items}")

        try:
            # Fetch corporation list from DART
            corps = await self._with_retry(
                self.dart_service.get_corporation_list,
                market=market,
            )

            total = len(corps)
            sync_log.total_items = total

            # Filter out already processed items if resuming
            if checkpoint and processed_corp_codes:
                corps_to_process = [c for c in corps if c.get("corp_code") not in processed_corp_codes]
                synced = checkpoint.processed_count
                sync_log.add_entry(
                    "INFO",
                    f"{total}개 기업 중 {len(corps_to_process)}개 남음 (재개)",
                )
            else:
                corps_to_process = corps
                synced = 0
                sync_log.add_entry("INFO", f"{total}개 기업 목록 수신")

            self._update_progress(total=total, message=f"{total}개 기업 동기화 중...")

            # Initialize or update checkpoint
            self._current_checkpoint = SyncCheckpoint(
                sync_type=sync_type,
                started_at=checkpoint.started_at if checkpoint else datetime.now().isoformat(),
                last_updated_at=datetime.now().isoformat(),
                total_items=total,
                processed_count=synced,
                processed_items=list(processed_corp_codes),
                remaining_items=[c.get("corp_code", "") for c in corps_to_process],
                sync_params={"market": market},
            )

            for i, corp_data in enumerate(corps_to_process):
                if self._cancelled:
                    # Save checkpoint on cancel
                    self._current_checkpoint.processed_count = synced
                    self.checkpoint_manager.save_checkpoint(self._current_checkpoint)
                    sync_log.processed_items = synced
                    self._finish_sync_log("cancelled")
                    self._update_progress(
                        status=SyncStatus.CANCELLED,
                        message=f"동기화가 취소되었습니다. ({synced}/{total} 완료, 재개 가능)",
                    )
                    return self._progress

                corp_code = corp_data.get("corp_code", "")
                try:
                    # Map DART API fields to our model
                    corp_dict = self._map_corporation_data(corp_data)

                    # Upsert corporation
                    self.corp_service.upsert(corp_dict)
                    synced += 1
                    sync_log.success_count += 1

                    # Update checkpoint
                    self._current_checkpoint.processed_count = synced
                    self._current_checkpoint.processed_items.append(corp_code)
                    if corp_code in self._current_checkpoint.remaining_items:
                        self._current_checkpoint.remaining_items.remove(corp_code)

                except Exception as e:
                    sync_log.add_error(
                        str(e),
                        item_id=corp_code,
                        error_type=type(e).__name__,
                    )
                    logger.warning(f"Failed to sync corporation {corp_code}: {e}")

                sync_log.processed_items = synced
                self._update_progress(
                    current=synced,
                    message=f"동기화 중... {synced}/{total}",
                )

                # Save checkpoint periodically
                if (i + 1) % CHECKPOINT_SAVE_INTERVAL == 0:
                    self.checkpoint_manager.save_checkpoint(self._current_checkpoint)

                # Rate limiting
                if i < len(corps_to_process) - 1:
                    await asyncio.sleep(self.rate_limit_delay / 10)  # Faster for list

            self._progress.completed_at = datetime.now()
            self._finish_sync_log("completed")

            # Clear checkpoint on successful completion
            self.checkpoint_manager.clear_checkpoint(sync_type)
            self._current_checkpoint = None

            self._update_progress(
                status=SyncStatus.COMPLETED,
                message=f"{synced}개 기업 동기화 완료",
            )

            logger.info(f"Corporation sync completed: {synced} corporations")
            return self._progress

        except Exception as e:
            logger.error(f"Corporation sync failed: {e}")

            # Save checkpoint on failure for resume
            if self._current_checkpoint:
                self.checkpoint_manager.save_checkpoint(self._current_checkpoint)

            sync_log.add_error(str(e), error_type=type(e).__name__)
            self._finish_sync_log("failed")
            self._update_progress(
                status=SyncStatus.FAILED,
                error=str(e),
                message=f"동기화 실패 (재개 가능: {self._current_checkpoint.processed_count if self._current_checkpoint else 0}개 완료)",
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

    async def sync_all_financial_statements(
        self,
        corp_codes: list[str] | None = None,
        years: list[str] | None = None,
        reprt_codes: list[str] | None = None,
        resume: bool = False,
    ) -> SyncProgress:
        """Sync financial statements for multiple corporations.

        Args:
            corp_codes: List of corp_codes to sync. If None, syncs all listed corporations.
            years: List of business years to sync. Defaults to last 3 years.
            reprt_codes: List of report codes. Defaults to annual report only.
            resume: If True, resume from last checkpoint.

        Returns:
            Final SyncProgress object.
        """
        self._cancelled = False
        sync_type = "financial_statements"

        # Check for existing checkpoint if resume is requested
        checkpoint = None
        processed_corp_codes: set[str] = set()

        if resume:
            checkpoint = self.checkpoint_manager.load_checkpoint(sync_type)
            if checkpoint:
                processed_corp_codes = set(checkpoint.processed_items)
                logger.info(
                    f"Resuming financial statements sync from checkpoint: "
                    f"{checkpoint.processed_count}/{checkpoint.total_items}"
                )

        self._progress = SyncProgress(
            status=SyncStatus.SYNCING,
            current=checkpoint.processed_count if checkpoint else 0,
            total=checkpoint.total_items if checkpoint else 0,
            message="재무제표 동기화 준비 중..." if not checkpoint else "동기화 재개 중...",
            started_at=datetime.fromisoformat(checkpoint.started_at) if checkpoint else datetime.now(),
        )
        self._update_progress()

        # Start logging
        sync_log = self._start_sync_log(sync_type)
        if checkpoint:
            sync_log.add_entry("INFO", f"체크포인트에서 재개: {checkpoint.processed_count}/{checkpoint.total_items}")

        try:
            if corp_codes is None:
                # Get only listed corporations (with stock_code)
                corps = (
                    self.session.query(Corporation)
                    .filter(Corporation.stock_code.isnot(None))
                    .filter(Corporation.stock_code != "")
                    .all()
                )
                corp_codes = [c.corp_code for c in corps]

            if not corp_codes:
                self._update_progress(
                    status=SyncStatus.FAILED,
                    error="동기화할 기업이 없습니다. 먼저 기업 목록을 동기화해주세요.",
                    message="동기화 실패",
                )
                sync_log.add_error("No corporations to sync")
                self._finish_sync_log("failed")
                return self._progress

            total = len(corp_codes)
            sync_log.total_items = total

            # Filter out already processed items if resuming
            if checkpoint and processed_corp_codes:
                corps_to_process = [c for c in corp_codes if c not in processed_corp_codes]
                synced_corps = checkpoint.processed_count
                sync_log.add_entry(
                    "INFO",
                    f"{total}개 기업 중 {len(corps_to_process)}개 남음 (재개)",
                )
            else:
                corps_to_process = corp_codes
                synced_corps = 0
                sync_log.add_entry("INFO", f"{total}개 기업 재무제표 동기화 시작")

            self._update_progress(total=total, message=f"{total}개 기업 재무제표 동기화 중...")

            # Initialize or update checkpoint
            self._current_checkpoint = SyncCheckpoint(
                sync_type=sync_type,
                started_at=checkpoint.started_at if checkpoint else datetime.now().isoformat(),
                last_updated_at=datetime.now().isoformat(),
                total_items=total,
                processed_count=synced_corps,
                processed_items=list(processed_corp_codes),
                remaining_items=corps_to_process.copy(),
                sync_params={"years": years, "reprt_codes": reprt_codes},
            )

            total_statements = 0

            for i, corp_code in enumerate(corps_to_process):
                if self._cancelled:
                    # Save checkpoint on cancel
                    self._current_checkpoint.processed_count = synced_corps
                    self.checkpoint_manager.save_checkpoint(self._current_checkpoint)
                    sync_log.processed_items = synced_corps
                    self._finish_sync_log("cancelled")
                    self._update_progress(
                        status=SyncStatus.CANCELLED,
                        message=f"동기화가 취소되었습니다. ({synced_corps}/{total} 완료, 재개 가능)",
                    )
                    return self._progress

                try:
                    count = await self.sync_financial_statements(
                        corp_code=corp_code,
                        years=years,
                        reprt_codes=reprt_codes,
                    )
                    total_statements += count
                    synced_corps += 1
                    sync_log.success_count += 1

                    # Update checkpoint
                    self._current_checkpoint.processed_count = synced_corps
                    self._current_checkpoint.processed_items.append(corp_code)
                    if corp_code in self._current_checkpoint.remaining_items:
                        self._current_checkpoint.remaining_items.remove(corp_code)

                except Exception as e:
                    sync_log.add_error(
                        str(e),
                        item_id=corp_code,
                        error_type=type(e).__name__,
                    )
                    logger.warning(f"Failed to sync financial statements for {corp_code}: {e}")

                sync_log.processed_items = synced_corps
                self._update_progress(
                    current=synced_corps,
                    message=f"재무제표 동기화 중... {synced_corps}/{total} (항목 {total_statements}개)",
                )

                # Save checkpoint periodically
                if (i + 1) % CHECKPOINT_SAVE_INTERVAL == 0:
                    self.checkpoint_manager.save_checkpoint(self._current_checkpoint)

            self._progress.completed_at = datetime.now()
            self._finish_sync_log("completed")

            # Clear checkpoint on successful completion
            self.checkpoint_manager.clear_checkpoint(sync_type)
            self._current_checkpoint = None

            self._update_progress(
                status=SyncStatus.COMPLETED,
                message=f"{synced_corps}개 기업, {total_statements}개 재무제표 동기화 완료",
            )

            logger.info(
                f"Financial statements sync completed: {synced_corps} corps, {total_statements} statements"
            )
            return self._progress

        except Exception as e:
            logger.error(f"Financial statements sync failed: {e}")

            # Save checkpoint on failure for resume
            if self._current_checkpoint:
                self.checkpoint_manager.save_checkpoint(self._current_checkpoint)

            sync_log.add_error(str(e), error_type=type(e).__name__)
            self._finish_sync_log("failed")
            self._update_progress(
                status=SyncStatus.FAILED,
                error=str(e),
                message=f"동기화 실패 (재개 가능: {self._current_checkpoint.processed_count if self._current_checkpoint else 0}개 완료)",
            )
            return self._progress

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
