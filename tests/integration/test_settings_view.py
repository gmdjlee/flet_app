"""Integration tests for SettingsView."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import flet as ft
from src.views.settings_view import SettingsView
from src.services.sync_service import (
    SyncService,
    SyncStatus,
    SyncProgress,
    SyncLogger,
    SettingsManager,
    SyncLog,
)


@pytest.fixture
def mock_page():
    """Create mock Flet page."""
    page = MagicMock(spec=ft.Page)
    page.update = MagicMock()
    page.snack_bar = None
    page.dialog = None
    page.overlay = []
    return page


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def settings_manager(temp_data_dir):
    """Create SettingsManager with temp directory."""
    settings_file = temp_data_dir / "settings.json"
    return SettingsManager(settings_file=settings_file)


@pytest.fixture
def sync_logger(temp_data_dir):
    """Create SyncLogger with temp directory."""
    logs_dir = temp_data_dir / "logs"
    return SyncLogger(logs_dir=logs_dir)


@pytest.fixture
def mock_sync_service():
    """Create mock SyncService."""
    service = MagicMock(spec=SyncService)
    service.progress = SyncProgress(
        status=SyncStatus.IDLE,
        current=0,
        total=0,
        message="",
    )
    service.sync_corporation_list = AsyncMock(return_value=SyncProgress(
        status=SyncStatus.COMPLETED,
        current=100,
        total=100,
        message="100개 기업 동기화 완료",
    ))
    return service


class TestSettingsViewInit:
    """Tests for SettingsView initialization."""

    def test_init_creates_view(self, mock_page):
        """Test that SettingsView initializes correctly."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            assert view.route == "/settings"
            assert len(view.controls) == 1  # Main container

    def test_init_with_sync_service(self, mock_page, mock_sync_service):
        """Test initialization with SyncService."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page, sync_service=mock_sync_service)

            assert view._sync_service == mock_sync_service

    def test_init_loads_api_key(self, mock_page):
        """Test that saved API key is loaded."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value="test_api_key"), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            assert view.api_key_field.value == "test_api_key"


class TestSettingsManagerIntegration:
    """Tests for SettingsManager integration."""

    def test_save_api_key(self, settings_manager):
        """Test saving API key."""
        settings_manager.set_api_key("test_key_123")
        assert settings_manager.get_api_key() == "test_key_123"

    def test_get_api_key_from_env(self, settings_manager, monkeypatch):
        """Test getting API key from environment."""
        monkeypatch.setenv("DART_API_KEY", "env_key_456")
        assert settings_manager.get_api_key() == "env_key_456"

    def test_sync_settings(self, settings_manager):
        """Test sync settings."""
        settings = {
            "rate_limit_delay": 1.0,
            "max_retries": 5,
            "auto_sync_on_start": True,
        }
        settings_manager.set_sync_settings(settings)
        loaded = settings_manager.get_sync_settings()
        assert loaded["rate_limit_delay"] == 1.0
        assert loaded["max_retries"] == 5

    def test_last_sync_time(self, settings_manager):
        """Test last sync time tracking."""
        now = datetime.now()
        settings_manager.set_last_sync_time("corporation_list", now)
        loaded = settings_manager.get_last_sync_time("corporation_list")
        assert loaded == now.isoformat()


class TestSyncLoggerIntegration:
    """Tests for SyncLogger integration."""

    def test_save_and_load_log(self, sync_logger):
        """Test saving and loading sync log."""
        log = SyncLog(
            sync_type="corporation_list",
            started_at=datetime.now().isoformat(),
            status="completed",
            total_items=100,
            processed_items=100,
            success_count=98,
            error_count=2,
        )
        log.add_entry("INFO", "Test log entry")

        filepath = sync_logger.save_log(log)
        assert filepath.exists()

        logs = sync_logger.get_recent_logs(limit=1)
        assert len(logs) == 1
        assert logs[0]["sync_type"] == "corporation_list"
        assert logs[0]["success_count"] == 98

    def test_get_recent_logs_empty(self, sync_logger):
        """Test getting logs when none exist."""
        logs = sync_logger.get_recent_logs()
        assert logs == []

    def test_get_recent_logs_limit(self, sync_logger):
        """Test log retrieval limit."""
        import time
        for i in range(5):
            log = SyncLog(
                sync_type="corporation_list",
                started_at=datetime.now().isoformat(),
                status="completed",
            )
            sync_logger.save_log(log)
            time.sleep(0.01)  # Small delay to ensure unique timestamps

        logs = sync_logger.get_recent_logs(limit=3)
        assert len(logs) == 3


class TestAPIKeySection:
    """Tests for API key section."""

    def test_save_api_key_click(self, mock_page):
        """Test save API key button click."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SettingsManager, "set_api_key") as mock_set_key, \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)
            view.api_key_field.value = "new_api_key"

            # Simulate button click
            mock_event = MagicMock()
            view._on_save_api_key(mock_event)

            mock_set_key.assert_called_once_with("new_api_key")
            assert mock_page.snack_bar is not None

    def test_save_empty_api_key(self, mock_page):
        """Test saving empty API key shows error."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)
            view.api_key_field.value = ""

            mock_event = MagicMock()
            view._on_save_api_key(mock_event)

            # Should show error snackbar
            assert mock_page.snack_bar is not None


class TestSyncSection:
    """Tests for sync section."""

    def test_sync_buttons_disabled_without_api_key(self, mock_page):
        """Test sync buttons are disabled without API key."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            assert view.sync_corp_button.disabled is True
            assert view.sync_fin_button.disabled is True

    def test_sync_buttons_enabled_with_api_key(self, mock_page):
        """Test sync buttons are enabled with API key."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value="test_key"), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            assert view.sync_corp_button.disabled is False

    def test_sync_without_api_key_shows_error(self, mock_page):
        """Test starting sync without API key shows error."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            mock_event = MagicMock()
            view._on_sync_corporations(mock_event)

            # Should show error snackbar
            assert mock_page.snack_bar is not None


class TestProgressCallback:
    """Tests for progress callback handling."""

    def test_progress_callback_updates_ui(self, mock_page):
        """Test progress callback updates UI elements."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value="test_key"), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            progress = SyncProgress(
                status=SyncStatus.SYNCING,
                current=50,
                total=100,
                message="동기화 중... 50/100",
            )
            view._progress_callback(progress)

            assert view.progress_bar.value == 0.5
            assert view.progress_text.value == "동기화 중... 50/100"

    def test_progress_callback_on_completion(self, mock_page):
        """Test progress callback handles completion."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value="test_key"), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SettingsManager, "set_last_sync_time"), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            progress = SyncProgress(
                status=SyncStatus.COMPLETED,
                current=100,
                total=100,
                message="100개 기업 동기화 완료",
            )
            view._progress_callback(progress)

            assert view.progress_bar.visible is False
            assert view.cancel_button.visible is False


class TestCacheSection:
    """Tests for cache management section."""

    def test_clear_cache_shows_dialog(self, mock_page):
        """Test clear cache shows confirmation dialog."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            mock_event = MagicMock()
            view._on_clear_cache(mock_event)

            assert mock_page.dialog is not None
            assert mock_page.dialog.open is True


class TestSyncStatusDisplay:
    """Tests for sync status display."""

    def test_displays_last_sync_time(self, mock_page):
        """Test last sync time is displayed."""
        last_sync = "2024-01-15T10:30:00"
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value="key"), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=last_sync), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            assert "2024-01-15" in view.sync_status_text.value

    def test_displays_no_sync_message(self, mock_page):
        """Test 'not synced' message when never synced."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            assert "동기화되지 않음" in view.sync_status_text.value


class TestRecentLogsSection:
    """Tests for recent logs section."""

    def test_displays_recent_logs(self, mock_page):
        """Test recent logs are displayed."""
        logs = [
            {
                "sync_type": "corporation_list",
                "started_at": "2024-01-15T10:30:00",
                "status": "completed",
                "success_count": 100,
                "error_count": 0,
            },
        ]
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=logs):
            view = SettingsView(mock_page)

            assert len(view.logs_column.controls) == 1

    def test_displays_empty_logs_message(self, mock_page):
        """Test empty logs message."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]):
            view = SettingsView(mock_page)

            assert len(view.logs_column.controls) == 1
            # Check it's the "no logs" message
            assert isinstance(view.logs_column.controls[0], ft.Text)

    def test_refresh_logs(self, mock_page):
        """Test refresh logs button."""
        with patch.object(SettingsManager, "__init__", return_value=None), \
             patch.object(SettingsManager, "get_api_key", return_value=None), \
             patch.object(SettingsManager, "get_last_sync_time", return_value=None), \
             patch.object(SyncLogger, "__init__", return_value=None), \
             patch.object(SyncLogger, "get_recent_logs", return_value=[]) as mock_get_logs:
            view = SettingsView(mock_page)

            mock_event = MagicMock()
            view._on_refresh_logs(mock_event)

            # Should call get_recent_logs again
            assert mock_get_logs.call_count >= 2  # Once in init, once on refresh
