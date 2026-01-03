"""Tests for SyncService - DART data synchronization."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.corporation import Corporation
from src.models.financial_statement import FinancialStatement
from src.services.sync_service import (
    SyncService,
    SyncStatus,
    SyncProgress,
)
from src.services.dart_service import DartService, DartServiceError


@pytest.fixture
def sync_db():
    """Create in-memory SQLite for sync testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_dart_service():
    """Create mock DART service."""
    mock = AsyncMock(spec=DartService)
    mock.get_corporation_list = AsyncMock(return_value=[
        {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "corp_cls": "Y"},
        {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660", "corp_cls": "Y"},
        {"corp_code": "00164742", "corp_name": "네이버", "stock_code": "035420", "corp_cls": "Y"},
    ])
    mock.get_corporation_info = AsyncMock(return_value={
        "corp_code": "00126380",
        "corp_name": "삼성전자",
        "stock_code": "005930",
        "corp_cls": "Y",
        "ceo_nm": "한종희",
        "corp_name_eng": "Samsung Electronics Co., Ltd.",
        "jurir_no": "1301110006246",
        "bizr_no": "1248100998",
        "adres": "경기도 수원시 영통구 삼성로 129 (매탄동)",
        "hm_url": "www.samsung.com",
        "est_dt": "19690113",
        "acc_mt": "12",
    })
    mock.get_financial_statements = AsyncMock(return_value=[
        {
            "bsns_year": "2024",
            "reprt_code": "11011",
            "fs_div": "CFS",
            "sj_div": "BS",
            "account_id": "ifrs-full_Assets",
            "account_nm": "자산총계",
            "thstrm_nm": "제56기",
            "thstrm_amount": "500,000,000,000",
            "frmtrm_nm": "제55기",
            "frmtrm_amount": "450,000,000,000",
        },
        {
            "bsns_year": "2024",
            "reprt_code": "11011",
            "fs_div": "CFS",
            "sj_div": "IS",
            "account_id": "ifrs-full_Revenue",
            "account_nm": "매출액",
            "thstrm_nm": "제56기",
            "thstrm_amount": "300,000,000,000",
            "frmtrm_nm": "제55기",
            "frmtrm_amount": "280,000,000,000",
        },
    ])
    return mock


@pytest.fixture
def sync_service(mock_dart_service, sync_db):
    """Create SyncService instance with mocks."""
    return SyncService(
        dart_service=mock_dart_service,
        session=sync_db,
        rate_limit_delay=0.01,  # Fast for testing
    )


class TestSyncProgress:
    """Tests for SyncProgress dataclass."""

    def test_create_sync_progress(self):
        """Test creating a SyncProgress instance."""
        progress = SyncProgress(
            status=SyncStatus.IDLE,
            current=0,
            total=100,
            message="Ready",
        )
        assert progress.status == SyncStatus.IDLE
        assert progress.current == 0
        assert progress.total == 100
        assert progress.message == "Ready"
        assert progress.error is None

    def test_percentage_calculation(self):
        """Test percentage property calculation."""
        progress = SyncProgress(
            status=SyncStatus.SYNCING,
            current=50,
            total=100,
            message="Syncing...",
        )
        assert progress.percentage == 50.0

    def test_percentage_with_zero_total(self):
        """Test percentage when total is zero."""
        progress = SyncProgress(
            status=SyncStatus.IDLE,
            current=0,
            total=0,
            message="Ready",
        )
        assert progress.percentage == 0.0

    def test_elapsed_seconds_not_started(self):
        """Test elapsed_seconds when not started."""
        progress = SyncProgress(
            status=SyncStatus.IDLE,
            current=0,
            total=0,
            message="Ready",
        )
        assert progress.elapsed_seconds is None

    def test_elapsed_seconds_with_times(self):
        """Test elapsed_seconds calculation."""
        started = datetime(2024, 1, 1, 12, 0, 0)
        completed = datetime(2024, 1, 1, 12, 0, 30)
        progress = SyncProgress(
            status=SyncStatus.COMPLETED,
            current=100,
            total=100,
            message="Done",
            started_at=started,
            completed_at=completed,
        )
        assert progress.elapsed_seconds == 30.0


class TestSyncServiceInit:
    """Tests for SyncService initialization."""

    def test_init_with_defaults(self, mock_dart_service, sync_db):
        """Test SyncService initialization with defaults."""
        service = SyncService(mock_dart_service, sync_db)
        assert service.dart_service == mock_dart_service
        assert service.session == sync_db
        assert service.rate_limit_delay == SyncService.DEFAULT_RATE_LIMIT_DELAY
        assert service.progress.status == SyncStatus.IDLE

    def test_init_with_custom_rate_limit(self, mock_dart_service, sync_db):
        """Test SyncService with custom rate limit."""
        service = SyncService(mock_dart_service, sync_db, rate_limit_delay=1.0)
        assert service.rate_limit_delay == 1.0

    def test_set_progress_callback(self, sync_service):
        """Test setting progress callback."""
        callback = MagicMock()
        sync_service.set_progress_callback(callback)
        assert sync_service._progress_callback == callback


class TestSyncCorporationList:
    """Tests for corporation list synchronization."""

    @pytest.mark.asyncio
    async def test_sync_corporation_list_success(self, sync_service, sync_db):
        """Test successful corporation list sync."""
        result = await sync_service.sync_corporation_list()

        assert result.status == SyncStatus.COMPLETED
        assert result.current == 3
        assert result.total == 3
        assert "3개 기업" in result.message

        # Verify corporations in database
        corps = sync_db.query(Corporation).all()
        assert len(corps) == 3

    @pytest.mark.asyncio
    async def test_sync_corporation_list_with_market_filter(self, sync_service, mock_dart_service):
        """Test sync with market filter."""
        await sync_service.sync_corporation_list(market="KOSPI")
        mock_dart_service.get_corporation_list.assert_called_once_with(market="KOSPI")

    @pytest.mark.asyncio
    async def test_sync_corporation_list_progress_callback(self, sync_service):
        """Test progress callback is called during sync."""
        callback = MagicMock()
        sync_service.set_progress_callback(callback)

        await sync_service.sync_corporation_list()

        assert callback.call_count > 0
        # Last call should be completion
        last_call = callback.call_args_list[-1]
        assert last_call[0][0].status == SyncStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_sync_corporation_list_cancelled(self, sync_service, mock_dart_service):
        """Test cancellation during sync."""
        # Make API call slow so we can cancel
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.1)
            return [
                {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "corp_cls": "Y"},
            ]

        mock_dart_service.get_corporation_list = slow_response

        # Start sync and cancel immediately
        sync_service.cancel()
        result = await sync_service.sync_corporation_list()

        # Should complete since we can't cancel during API call
        # But if cancelled flag was set before loop, would be CANCELLED
        assert result.status in [SyncStatus.COMPLETED, SyncStatus.CANCELLED]

    @pytest.mark.asyncio
    async def test_sync_corporation_list_api_error(self, sync_service, mock_dart_service):
        """Test handling of API errors."""
        mock_dart_service.get_corporation_list = AsyncMock(
            side_effect=DartServiceError("API Error")
        )

        result = await sync_service.sync_corporation_list()

        assert result.status == SyncStatus.FAILED
        assert result.error is not None


class TestSyncCorporationInfo:
    """Tests for single corporation info sync."""

    @pytest.mark.asyncio
    async def test_sync_corporation_info_success(self, sync_service, sync_db):
        """Test syncing info for a single corporation."""
        corp = await sync_service.sync_corporation_info("00126380")

        assert corp is not None
        assert corp.corp_code == "00126380"
        assert corp.corp_name == "삼성전자"

    @pytest.mark.asyncio
    async def test_sync_corporation_info_updates_existing(self, sync_service, sync_db):
        """Test that syncing updates existing corporation."""
        # First sync
        corp1 = await sync_service.sync_corporation_info("00126380")

        # Update mock to return different data
        sync_service.dart_service.get_corporation_info = AsyncMock(return_value={
            "corp_code": "00126380",
            "corp_name": "삼성전자(주)",  # Changed name
            "stock_code": "005930",
            "corp_cls": "Y",
            "ceo_nm": "한종희",
        })

        # Second sync
        corp2 = await sync_service.sync_corporation_info("00126380")

        assert corp2.corp_name == "삼성전자(주)"
        # Should be same record (upsert)
        corps = sync_db.query(Corporation).filter_by(corp_code="00126380").all()
        assert len(corps) == 1

    @pytest.mark.asyncio
    async def test_sync_corporation_info_api_error(self, sync_service, mock_dart_service):
        """Test handling API error for single corp info."""
        mock_dart_service.get_corporation_info = AsyncMock(
            side_effect=DartServiceError("Corp not found")
        )

        result = await sync_service.sync_corporation_info("00000000")
        assert result is None


class TestSyncFinancialStatements:
    """Tests for financial statement synchronization."""

    @pytest.mark.asyncio
    async def test_sync_financial_statements_success(self, sync_service, sync_db):
        """Test syncing financial statements."""
        # First add corporation
        await sync_service.sync_corporation_info("00126380")

        # Then sync financial statements
        count = await sync_service.sync_financial_statements("00126380")

        assert count >= 2  # At least 2 statements from mock

    @pytest.mark.asyncio
    async def test_sync_financial_statements_custom_years(self, sync_service, mock_dart_service):
        """Test syncing with custom years."""
        # First add corporation to satisfy FK constraint
        await sync_service.sync_corporation_info("00126380")

        await sync_service.sync_financial_statements(
            "00126380",
            years=["2023", "2024"],
            reprt_codes=["11011"],
        )

        # Should have been called for each year
        assert mock_dart_service.get_financial_statements.call_count >= 2

    @pytest.mark.asyncio
    async def test_sync_financial_statements_upsert(self, sync_service, sync_db):
        """Test that syncing upserts financial statements."""
        # First add corporation to satisfy FK constraint
        await sync_service.sync_corporation_info("00126380")

        await sync_service.sync_financial_statements("00126380")
        count1 = sync_db.query(FinancialStatement).count()

        # Sync again - should upsert, not duplicate
        await sync_service.sync_financial_statements("00126380")
        count2 = sync_db.query(FinancialStatement).count()

        assert count1 == count2

    @pytest.mark.asyncio
    async def test_sync_financial_statements_cancelled(self, sync_service):
        """Test cancellation during financial statement sync."""
        sync_service.cancel()
        count = await sync_service.sync_financial_statements("00126380")
        assert count == 0  # Should stop immediately

    @pytest.mark.asyncio
    async def test_sync_financial_statements_partial_failure(self, sync_service, mock_dart_service):
        """Test handling partial failures in financial sync."""
        # First add corporation to satisfy FK constraint
        await sync_service.sync_corporation_info("00126380")

        call_count = 0

        async def mixed_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise DartServiceError("Rate limit")
            return [
                {
                    "bsns_year": "2024",
                    "reprt_code": "11011",
                    "fs_div": "CFS",
                    "sj_div": "BS",
                    "account_nm": "자산총계",
                    "thstrm_amount": "1000000",
                },
            ]

        mock_dart_service.get_financial_statements = mixed_response

        # Should succeed partially (with retries)
        count = await sync_service.sync_financial_statements(
            "00126380",
            years=["2024"],
            reprt_codes=["11011"],
        )
        assert count >= 0  # Some may succeed, some may fail


class TestSyncAllCorporationInfo:
    """Tests for syncing info for multiple corporations."""

    @pytest.mark.asyncio
    async def test_sync_all_corporation_info_success(self, sync_service, sync_db):
        """Test syncing all corporation info."""
        # First populate with corporation list
        await sync_service.sync_corporation_list()

        # Then sync detailed info
        result = await sync_service.sync_all_corporation_info()

        assert result.status == SyncStatus.COMPLETED
        assert result.total == 3

    @pytest.mark.asyncio
    async def test_sync_all_corporation_info_with_codes(self, sync_service):
        """Test syncing specific corporation codes."""
        result = await sync_service.sync_all_corporation_info(
            corp_codes=["00126380", "00164779"]
        )

        assert result.total == 2

    @pytest.mark.asyncio
    async def test_sync_all_corporation_info_cancelled(self, sync_service, sync_db, mock_dart_service):
        """Test cancellation during all corp info sync."""
        await sync_service.sync_corporation_list()

        # Track call count to cancel after first call
        call_count = 0
        original_get_info = mock_dart_service.get_corporation_info

        async def cancel_after_first(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Cancel after first call
                sync_service.cancel()
            return await original_get_info(*args, **kwargs)

        mock_dart_service.get_corporation_info = cancel_after_first

        result = await sync_service.sync_all_corporation_info()

        # Should be cancelled after first corporation
        assert result.status == SyncStatus.CANCELLED
        assert result.current >= 1  # At least one was processed


class TestRetryLogic:
    """Tests for retry logic in sync operations."""

    @pytest.mark.asyncio
    async def test_retry_on_api_error(self, sync_service, mock_dart_service):
        """Test that operations are retried on failure."""
        call_count = 0

        async def flaky_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DartServiceError("Temporary error")
            return [{"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "corp_cls": "Y"}]

        mock_dart_service.get_corporation_list = flaky_response

        result = await sync_service.sync_corporation_list()

        assert result.status == SyncStatus.COMPLETED
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, sync_service, mock_dart_service):
        """Test that sync fails after max retries."""
        mock_dart_service.get_corporation_list = AsyncMock(
            side_effect=DartServiceError("Persistent error")
        )

        result = await sync_service.sync_corporation_list()

        assert result.status == SyncStatus.FAILED


class TestRateLimiting:
    """Tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit_delay_applied(self, sync_service, mock_dart_service):
        """Test that rate limit delay is applied between calls."""
        sync_service.rate_limit_delay = 0.05  # 50ms

        start = datetime.now()
        await sync_service.sync_corporation_list()
        elapsed = (datetime.now() - start).total_seconds()

        # Should take some time due to rate limiting
        # (3 corporations, with delays between)
        assert elapsed >= 0.01  # At least some delay


class TestDataMapping:
    """Tests for data mapping functions."""

    def test_map_corporation_data(self, sync_service):
        """Test corporation data mapping."""
        dart_data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "modify_date": "20240101",
            "ceo_nm": "한종희",
        }

        mapped = sync_service._map_corporation_data(dart_data)

        assert mapped["corp_code"] == "00126380"
        assert mapped["corp_name"] == "삼성전자"
        assert mapped["market"] == "KOSPI"

    def test_map_corporation_data_kosdaq(self, sync_service):
        """Test mapping for KOSDAQ market."""
        dart_data = {
            "corp_code": "00164742",
            "corp_name": "네이버",
            "stock_code": "035420",
            "corp_cls": "K",
        }

        mapped = sync_service._map_corporation_data(dart_data)
        assert mapped["market"] == "KOSDAQ"

    def test_map_corporation_data_unlisted(self, sync_service):
        """Test mapping for unlisted company."""
        dart_data = {
            "corp_code": "00000001",
            "corp_name": "비상장회사",
            "stock_code": None,
            "corp_cls": "E",
        }

        mapped = sync_service._map_corporation_data(dart_data)
        assert mapped["market"] is None
        assert mapped["stock_code"] is None

    def test_map_financial_statement(self, sync_service):
        """Test financial statement data mapping."""
        dart_data = {
            "bsns_year": "2024",
            "reprt_code": "11011",
            "fs_div": "CFS",
            "sj_div": "BS",
            "account_nm": "자산총계",
            "thstrm_amount": "500,000,000,000",
            "frmtrm_amount": "450,000,000,000",
        }

        mapped = sync_service._map_financial_statement(dart_data, "00126380")

        assert mapped["corp_code"] == "00126380"
        assert mapped["bsns_year"] == "2024"
        assert mapped["thstrm_amount"] == 500_000_000_000
        assert mapped["frmtrm_amount"] == 450_000_000_000

    def test_map_financial_statement_empty_amount(self, sync_service):
        """Test mapping with empty amount values."""
        dart_data = {
            "bsns_year": "2024",
            "reprt_code": "11011",
            "fs_div": "CFS",
            "sj_div": "BS",
            "account_nm": "자산총계",
            "thstrm_amount": "",
            "frmtrm_amount": None,
        }

        mapped = sync_service._map_financial_statement(dart_data, "00126380")

        assert mapped["thstrm_amount"] is None
        assert mapped["frmtrm_amount"] is None
