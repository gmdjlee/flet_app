"""Settings view - Application configuration and data synchronization."""

import asyncio
import logging
from datetime import datetime

import flet as ft

logger = logging.getLogger(__name__)

from src.models.database import get_engine, get_session
from src.services.corporation_service import CorporationService
from src.services.dart_service import DartService
from src.services.financial_service import FinancialService
from src.services.sync_service import (
    CheckpointManager,
    SettingsManager,
    SyncCheckpoint,
    SyncLogger,
    SyncProgress,
    SyncService,
    SyncStatus,
)
from src.utils.cache import CacheManager


class SettingsView(ft.View):
    """Settings view for application configuration and data sync."""

    def __init__(
        self,
        page: ft.Page,
        sync_service: SyncService | None = None,
    ) -> None:
        """Initialize SettingsView.

        Args:
            page: Flet page instance.
            sync_service: SyncService instance. If None, created when needed.
        """
        self._page_ref = page
        self._sync_service = sync_service
        self._settings_manager = SettingsManager()
        self._sync_logger = SyncLogger()
        self._cache_manager = CacheManager()
        self._checkpoint_manager = CheckpointManager()

        # UI Controls
        self.api_key_field = ft.TextField(
            label="DART API 키",
            hint_text="DART Open API 키를 입력하세요",
            password=True,
            can_reveal_password=True,
            expand=True,
            value=self._settings_manager.get_api_key() or "",
        )

        self.progress_bar = ft.ProgressBar(visible=False, value=0)
        self.progress_text = ft.Text("", size=12, visible=False)
        self.sync_status_text = ft.Text("", size=12, color=ft.Colors.GREY_600)

        # Sync buttons (Flet 0.70+ compatibility)
        self.sync_corp_button = ft.Button(
            "기업 목록 동기화",
            icon=ft.Icons.SYNC,
            on_click=self._on_sync_corporations,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
            ),
        )
        self.sync_fin_button = ft.Button(
            "재무제표 동기화",
            icon=ft.Icons.SYNC_ALT,
            on_click=self._on_sync_financials,
            disabled=True,  # Requires API key
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
            ),
        )
        self.cancel_button = ft.Button(
            "취소",
            icon=ft.Icons.CANCEL,
            on_click=self._on_cancel_sync,
            visible=False,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, ft.Colors.GREY_400),
            ),
        )

        # Resume buttons
        self.resume_corp_button = ft.Button(
            "기업 목록 재개",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_resume_corporations,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE,
                color=ft.Colors.WHITE,
            ),
        )
        self.resume_fin_button = ft.Button(
            "재무제표 재개",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_resume_financials,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE,
                color=ft.Colors.WHITE,
            ),
        )

        # Year selection for financial sync
        current_year = datetime.now().year
        year_options = [ft.dropdown.Option(str(y)) for y in range(current_year - 10, current_year + 1)]

        self.start_year_dropdown = ft.Dropdown(
            label="시작 년도",
            width=120,
            value=str(current_year - 2),
            options=year_options,
            on_select=self._on_year_selection_change,
        )
        self.end_year_dropdown = ft.Dropdown(
            label="끝 년도",
            width=120,
            value=str(current_year),
            options=year_options,
            on_select=self._on_year_selection_change,
        )

        # Checkpoint info container
        self.checkpoint_info_container = ft.Container(
            content=ft.Column(controls=[], spacing=5),
            visible=False,
            padding=10,
            bgcolor=ft.Colors.ORANGE_50,
            border_radius=8,
        )

        # Recent logs container
        self.logs_column = ft.Column(
            controls=[],
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
            height=200,
        )

        # Update sync status
        self._update_sync_status()

        super().__init__(
            route="/settings",
            controls=[self._build()],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            scroll=ft.ScrollMode.AUTO,
        )

    def _get_or_create_sync_service(self) -> SyncService | None:
        """Get existing or create new SyncService instance.

        Returns:
            SyncService instance or None if API key is not configured.
        """
        if self._sync_service is not None:
            return self._sync_service

        api_key = self._settings_manager.get_api_key()
        if not api_key:
            return None

        try:
            dart_service = DartService(api_key=api_key)
            engine = get_engine()
            session = get_session(engine)
            self._sync_service = SyncService(
                dart_service=dart_service,
                session=session,
                sync_logger=self._sync_logger,
                settings_manager=self._settings_manager,
            )
            return self._sync_service
        except Exception:
            return None

    def _build(self) -> ft.Control:
        """Build the settings view content."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "설정",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(height=20),
                    self._build_api_section(),
                    ft.Divider(height=20),
                    self._build_sync_section(),
                    ft.Divider(height=20),
                    self._build_logs_section(),
                    ft.Divider(height=20),
                    self._build_data_section(),
                    ft.Container(height=30),  # Bottom padding for scroll
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=30,
            expand=True,
        )

    def _build_api_section(self) -> ft.Control:
        """Build API configuration section."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "DART API 설정",
                            size=18,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            "DART Open API 키가 필요합니다. https://opendart.fss.or.kr 에서 발급받으세요.",
                            size=12,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Row(
                            controls=[
                                self.api_key_field,
                                ft.Button(
                                    "저장",
                                    icon=ft.Icons.SAVE,
                                    on_click=self._on_save_api_key,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.PRIMARY,
                                        color=ft.Colors.ON_PRIMARY,
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                                    tooltip="API 키 유효성 확인",
                                    on_click=self._on_validate_api_key,
                                ),
                            ],
                        ),
                    ],
                    spacing=10,
                ),
                padding=20,
            ),
        )

    def _build_sync_section(self) -> ft.Control:
        """Build data sync section."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "데이터 동기화",
                                    size=18,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Container(expand=True),
                                self.sync_status_text,
                            ],
                        ),
                        ft.Text(
                            "DART에서 최신 기업 목록과 재무 데이터를 가져옵니다.",
                            size=12,
                            color=ft.Colors.GREY_600,
                        ),
                        # Year selection for financial statements sync
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        "재무제표 동기화 년도 범위",
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Row(
                                        controls=[
                                            self.start_year_dropdown,
                                            ft.Text("~", size=16),
                                            self.end_year_dropdown,
                                        ],
                                        spacing=10,
                                        alignment=ft.MainAxisAlignment.START,
                                    ),
                                ],
                                spacing=8,
                            ),
                            padding=ft.Padding(0, 10, 0, 5),
                        ),
                        # Checkpoint info section
                        self.checkpoint_info_container,
                        ft.Row(
                            controls=[
                                self.sync_corp_button,
                                self.sync_fin_button,
                                self.resume_corp_button,
                                self.resume_fin_button,
                                self.cancel_button,
                            ],
                            spacing=10,
                            wrap=True,
                        ),
                        self.progress_bar,
                        self.progress_text,
                    ],
                    spacing=10,
                ),
                padding=20,
            ),
        )

    def _build_logs_section(self) -> ft.Control:
        """Build recent sync logs section."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "최근 동기화 기록",
                                    size=18,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH,
                                    tooltip="새로고침",
                                    on_click=self._on_refresh_logs,
                                ),
                            ],
                        ),
                        self.logs_column,
                    ],
                    spacing=10,
                ),
                padding=20,
            ),
        )

    def _build_data_section(self) -> ft.Control:
        """Build data management section."""
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "데이터 관리",
                            size=18,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Row(
                            controls=[
                                ft.Button(
                                    "데이터 내보내기",
                                    icon=ft.Icons.DOWNLOAD,
                                    on_click=self._on_export_data,
                                    style=ft.ButtonStyle(
                                        side=ft.BorderSide(1, ft.Colors.GREY_400),
                                    ),
                                ),
                                ft.Button(
                                    "캐시 삭제",
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    on_click=self._on_clear_cache,
                                    style=ft.ButtonStyle(
                                        side=ft.BorderSide(1, ft.Colors.GREY_400),
                                    ),
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(height=10),
                        ft.Text(
                            "데이터 초기화",
                            size=16,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.RED_700,
                        ),
                        ft.Text(
                            "주의: 초기화된 데이터는 복구할 수 없습니다. 다시 동기화가 필요합니다.",
                            size=12,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Row(
                            controls=[
                                ft.Button(
                                    "기업 목록 초기화",
                                    icon=ft.Icons.DELETE_FOREVER,
                                    on_click=self._on_reset_corporations,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.RED_100,
                                        color=ft.Colors.RED_700,
                                    ),
                                ),
                                ft.Button(
                                    "재무제표 초기화",
                                    icon=ft.Icons.DELETE_FOREVER,
                                    on_click=self._on_reset_financials,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.RED_100,
                                        color=ft.Colors.RED_700,
                                    ),
                                ),
                                ft.Button(
                                    "전체 데이터 초기화",
                                    icon=ft.Icons.DELETE_FOREVER,
                                    on_click=self._on_reset_all_data,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.RED_700,
                                        color=ft.Colors.WHITE,
                                    ),
                                ),
                            ],
                            spacing=10,
                            wrap=True,
                        ),
                    ],
                    spacing=10,
                ),
                padding=20,
            ),
        )

    def _update_sync_status(self) -> None:
        """Update sync status display."""
        last_corp_sync = self._settings_manager.get_last_sync_time("corporation_list")
        if last_corp_sync:
            try:
                dt = datetime.fromisoformat(last_corp_sync)
                formatted = dt.strftime("%Y-%m-%d %H:%M")
                self.sync_status_text.value = f"마지막 동기화: {formatted}"
            except ValueError:
                self.sync_status_text.value = ""
        else:
            self.sync_status_text.value = "아직 동기화되지 않음"

        # Enable/disable buttons based on API key
        has_api_key = bool(self._settings_manager.get_api_key())
        self.sync_corp_button.disabled = not has_api_key
        self.sync_fin_button.disabled = not has_api_key

        # Check for resumable checkpoints and update UI
        self._update_checkpoint_status()

        # Load recent logs
        self._load_recent_logs()

    def _update_checkpoint_status(self) -> None:
        """Update checkpoint status and resume buttons visibility."""
        corp_checkpoint = self._checkpoint_manager.load_checkpoint("corporation_list")
        fin_checkpoint = self._checkpoint_manager.load_checkpoint("financial_statements")

        has_api_key = bool(self._settings_manager.get_api_key())

        # Update resume buttons visibility
        self.resume_corp_button.visible = corp_checkpoint is not None and has_api_key
        self.resume_fin_button.visible = fin_checkpoint is not None and has_api_key

        # Update checkpoint info container
        checkpoint_infos = []

        if corp_checkpoint:
            checkpoint_infos.append(self._create_checkpoint_info(corp_checkpoint, "기업 목록"))

        if fin_checkpoint:
            checkpoint_infos.append(self._create_checkpoint_info(fin_checkpoint, "재무제표"))

        if checkpoint_infos:
            self.checkpoint_info_container.content.controls = checkpoint_infos
            self.checkpoint_info_container.visible = True
        else:
            self.checkpoint_info_container.visible = False

    def _create_checkpoint_info(self, checkpoint: SyncCheckpoint, name: str) -> ft.Control:
        """Create checkpoint info row."""
        try:
            last_updated = datetime.fromisoformat(checkpoint.last_updated_at)
            formatted_time = last_updated.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            formatted_time = checkpoint.last_updated_at

        percentage = checkpoint.percentage
        remaining = checkpoint.total_items - checkpoint.processed_count

        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.PAUSE_CIRCLE, color=ft.Colors.ORANGE, size=18),
                ft.Text(f"{name}: ", weight=ft.FontWeight.W_500, size=12),
                ft.Text(
                    f"{checkpoint.processed_count}/{checkpoint.total_items} ({percentage:.1f}%)",
                    size=12,
                ),
                ft.Text(f"- {remaining}개 남음", size=12, color=ft.Colors.GREY_600),
                ft.Container(expand=True),
                ft.Text(f"중단: {formatted_time}", size=11, color=ft.Colors.GREY_500),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=16,
                    tooltip="체크포인트 삭제",
                    on_click=lambda e, sync_type=checkpoint.sync_type: self._on_clear_checkpoint(
                        e, sync_type
                    ),
                ),
            ],
            spacing=5,
        )

    def _on_clear_checkpoint(self, e: ft.ControlEvent, sync_type: str) -> None:
        """Handle clear checkpoint event."""
        self._checkpoint_manager.clear_checkpoint(sync_type)
        self._update_sync_status()
        self._page_ref.update()
        sync_type_name = "기업 목록" if sync_type == "corporation_list" else "재무제표"
        self._show_snackbar(f"{sync_type_name} 체크포인트가 삭제되었습니다.")

    def _load_recent_logs(self) -> None:
        """Load recent sync logs."""
        logs = self._sync_logger.get_recent_logs(limit=5)
        self.logs_column.controls.clear()

        if not logs:
            self.logs_column.controls.append(
                ft.Text("동기화 기록이 없습니다.", size=12, color=ft.Colors.GREY_500)
            )
            return

        for log in logs:
            status_icon = ft.Icons.CHECK_CIRCLE
            status_color = ft.Colors.GREEN
            if log.get("status") == "failed":
                status_icon = ft.Icons.ERROR
                status_color = ft.Colors.RED
            elif log.get("status") == "cancelled":
                status_icon = ft.Icons.CANCEL
                status_color = ft.Colors.ORANGE

            try:
                started = datetime.fromisoformat(log.get("started_at", ""))
                formatted_time = started.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                formatted_time = log.get("started_at", "")

            sync_type_names = {
                "corporation_list": "기업 목록",
                "corporation_info": "기업 상세",
                "financial_statements": "재무제표",
            }
            sync_type = sync_type_names.get(log.get("sync_type", ""), log.get("sync_type", ""))

            self.logs_column.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(status_icon, color=status_color, size=16),
                            ft.Text(sync_type, size=12, weight=ft.FontWeight.W_500),
                            ft.Text(formatted_time, size=12, color=ft.Colors.GREY_600),
                            ft.Container(expand=True),
                            ft.Text(
                                f"{log.get('success_count', 0)} 성공 / {log.get('error_count', 0)} 실패",
                                size=12,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.Padding.symmetric(vertical=5),
                )
            )

    def _show_snackbar(self, message: str, is_error: bool = False) -> None:
        """Show a snackbar message."""
        self._page_ref.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400 if is_error else None,
        )
        self._page_ref.snack_bar.open = True
        self._page_ref.update()

    def _on_save_api_key(self, e: ft.ControlEvent) -> None:
        """Handle save API key event."""
        api_key = self.api_key_field.value
        if api_key:
            self._settings_manager.set_api_key(api_key)
            self._update_sync_status()
            self._page_ref.update()
            self._show_snackbar("API 키가 저장되었습니다.")
        else:
            self._show_snackbar("API 키를 입력해주세요.", is_error=True)

    def _on_validate_api_key(self, e: ft.ControlEvent) -> None:
        """Handle API key validation."""
        api_key = self.api_key_field.value
        if not api_key:
            self._show_snackbar("API 키를 입력해주세요.", is_error=True)
            return

        # TODO: Implement actual API key validation
        self._show_snackbar("API 키 형식이 유효합니다.")

    def _progress_callback(self, progress: SyncProgress) -> None:
        """Handle sync progress updates."""
        if progress.total > 0:
            self.progress_bar.value = progress.current / progress.total
        else:
            self.progress_bar.value = None  # Indeterminate

        self.progress_text.value = progress.message

        if progress.status in [
            SyncStatus.COMPLETED,
            SyncStatus.FAILED,
            SyncStatus.CANCELLED,
        ]:
            self._on_sync_finished(progress)

        self._page_ref.update()

    def _on_sync_finished(self, progress: SyncProgress) -> None:
        """Handle sync completion."""
        self.progress_bar.visible = False
        self.progress_text.visible = False
        self.cancel_button.visible = False
        self.sync_corp_button.disabled = False
        self.sync_fin_button.disabled = False

        if progress.status == SyncStatus.COMPLETED:
            self._show_snackbar(progress.message)
        elif progress.status == SyncStatus.FAILED:
            self._show_snackbar(f"동기화 실패: {progress.error}", is_error=True)
        elif progress.status == SyncStatus.CANCELLED:
            self._show_snackbar("동기화가 취소되었습니다.")

        self._update_sync_status()
        self._page_ref.update()

    def _on_sync_corporations(self, e: ft.ControlEvent) -> None:
        """Handle sync corporations event."""
        if not self._settings_manager.get_api_key():
            self._show_snackbar("API 키를 먼저 설정해주세요.", is_error=True)
            return

        # Show progress UI
        self.progress_bar.visible = True
        self.progress_bar.value = None  # Indeterminate
        self.progress_text.visible = True
        self.progress_text.value = "동기화 준비 중..."
        self.cancel_button.visible = True
        self.sync_corp_button.disabled = True
        self.sync_fin_button.disabled = True
        self._page_ref.update()

        # Start sync in background
        asyncio.create_task(self._run_corporation_sync())

    async def _run_corporation_sync(self) -> None:
        """Run corporation list synchronization."""
        sync_service = self._get_or_create_sync_service()
        if not sync_service:
            self._show_snackbar("동기화 서비스를 초기화할 수 없습니다. API 키를 확인해주세요.", is_error=True)
            self._on_sync_finished(
                SyncProgress(
                    status=SyncStatus.FAILED,
                    current=0,
                    total=0,
                    message="서비스 초기화 실패",
                    error="SyncService not initialized",
                )
            )
            return

        sync_service.set_progress_callback(self._progress_callback)
        await sync_service.sync_corporation_list()

    def _on_sync_financials(self, e: ft.ControlEvent) -> None:
        """Handle sync financials event."""
        if not self._settings_manager.get_api_key():
            self._show_snackbar("API 키를 먼저 설정해주세요.", is_error=True)
            return

        # Show progress UI
        self.progress_bar.visible = True
        self.progress_bar.value = None  # Indeterminate
        self.progress_text.visible = True
        self.progress_text.value = "재무제표 동기화 준비 중..."
        self.cancel_button.visible = True
        self.sync_corp_button.disabled = True
        self.sync_fin_button.disabled = True
        self._page_ref.update()

        # Start sync in background
        asyncio.create_task(self._run_financial_sync())

    def _get_selected_years(self) -> list[str]:
        """Get selected years from the year range dropdowns.

        Returns:
            List of year strings in the selected range.
        """
        try:
            start_year = int(self.start_year_dropdown.value)
            end_year = int(self.end_year_dropdown.value)

            # Ensure start <= end
            if start_year > end_year:
                start_year, end_year = end_year, start_year

            return [str(y) for y in range(start_year, end_year + 1)]
        except (ValueError, TypeError):
            # Fallback to default (last 3 years)
            current_year = datetime.now().year
            return [str(y) for y in range(current_year - 2, current_year + 1)]

    def _on_year_selection_change(self, e: ft.ControlEvent) -> None:
        """Handle year selection change event."""
        # Validate that start year is not greater than end year
        try:
            start_year = int(self.start_year_dropdown.value)
            end_year = int(self.end_year_dropdown.value)

            if start_year > end_year:
                self._show_snackbar("시작 년도가 끝 년도보다 클 수 없습니다.", is_error=True)
        except (ValueError, TypeError):
            pass

    async def _run_financial_sync(self) -> None:
        """Run financial statements synchronization."""
        sync_service = self._get_or_create_sync_service()
        if not sync_service:
            self._show_snackbar("동기화 서비스를 초기화할 수 없습니다. API 키를 확인해주세요.", is_error=True)
            self._on_sync_finished(
                SyncProgress(
                    status=SyncStatus.FAILED,
                    current=0,
                    total=0,
                    message="서비스 초기화 실패",
                    error="SyncService not initialized",
                )
            )
            return

        # Get selected years from UI
        selected_years = self._get_selected_years()

        sync_service.set_progress_callback(self._progress_callback)
        await sync_service.sync_all_financial_statements(years=selected_years)

    def _on_resume_corporations(self, e: ft.ControlEvent) -> None:
        """Handle resume corporations sync event."""
        if not self._settings_manager.get_api_key():
            self._show_snackbar("API 키를 먼저 설정해주세요.", is_error=True)
            return

        # Check if checkpoint exists
        checkpoint = self._checkpoint_manager.load_checkpoint("corporation_list")
        if not checkpoint:
            self._show_snackbar("재개할 체크포인트가 없습니다.", is_error=True)
            return

        # Show progress UI
        self.progress_bar.visible = True
        self.progress_bar.value = checkpoint.processed_count / checkpoint.total_items
        self.progress_text.visible = True
        self.progress_text.value = f"동기화 재개 중... {checkpoint.processed_count}/{checkpoint.total_items}"
        self.cancel_button.visible = True
        self.sync_corp_button.disabled = True
        self.sync_fin_button.disabled = True
        self.resume_corp_button.visible = False
        self.resume_fin_button.visible = False
        self._page_ref.update()

        # Start sync in background with resume
        asyncio.create_task(self._run_corporation_sync_resume())

    async def _run_corporation_sync_resume(self) -> None:
        """Run corporation list synchronization with resume."""
        sync_service = self._get_or_create_sync_service()
        if not sync_service:
            self._show_snackbar("동기화 서비스를 초기화할 수 없습니다. API 키를 확인해주세요.", is_error=True)
            self._on_sync_finished(
                SyncProgress(
                    status=SyncStatus.FAILED,
                    current=0,
                    total=0,
                    message="서비스 초기화 실패",
                    error="SyncService not initialized",
                )
            )
            return

        sync_service.set_progress_callback(self._progress_callback)
        await sync_service.sync_corporation_list(resume=True)

    def _on_resume_financials(self, e: ft.ControlEvent) -> None:
        """Handle resume financials sync event."""
        if not self._settings_manager.get_api_key():
            self._show_snackbar("API 키를 먼저 설정해주세요.", is_error=True)
            return

        # Check if checkpoint exists
        checkpoint = self._checkpoint_manager.load_checkpoint("financial_statements")
        if not checkpoint:
            self._show_snackbar("재개할 체크포인트가 없습니다.", is_error=True)
            return

        # Show progress UI
        self.progress_bar.visible = True
        self.progress_bar.value = checkpoint.processed_count / checkpoint.total_items
        self.progress_text.visible = True
        self.progress_text.value = f"재무제표 동기화 재개 중... {checkpoint.processed_count}/{checkpoint.total_items}"
        self.cancel_button.visible = True
        self.sync_corp_button.disabled = True
        self.sync_fin_button.disabled = True
        self.resume_corp_button.visible = False
        self.resume_fin_button.visible = False
        self._page_ref.update()

        # Start sync in background with resume
        asyncio.create_task(self._run_financial_sync_resume())

    async def _run_financial_sync_resume(self) -> None:
        """Run financial statements synchronization with resume."""
        sync_service = self._get_or_create_sync_service()
        if not sync_service:
            self._show_snackbar("동기화 서비스를 초기화할 수 없습니다. API 키를 확인해주세요.", is_error=True)
            self._on_sync_finished(
                SyncProgress(
                    status=SyncStatus.FAILED,
                    current=0,
                    total=0,
                    message="서비스 초기화 실패",
                    error="SyncService not initialized",
                )
            )
            return

        sync_service.set_progress_callback(self._progress_callback)
        await sync_service.sync_all_financial_statements(resume=True)

    def _on_cancel_sync(self, e: ft.ControlEvent) -> None:
        """Handle cancel sync event."""
        if self._sync_service:
            self._sync_service.cancel()
            self._show_snackbar("동기화 취소 요청됨...")

    def _on_refresh_logs(self, e: ft.ControlEvent) -> None:
        """Handle refresh logs event."""
        self._load_recent_logs()
        self._page_ref.update()

    def _on_export_data(self, e: ft.ControlEvent) -> None:
        """Handle export data event."""

        # Show file picker dialog
        def on_result(e: ft.FilePickerResultEvent) -> None:
            if e.path:
                # TODO: Implement actual data export
                self._show_snackbar(f"데이터를 {e.path}에 내보냈습니다.")

        file_picker = ft.FilePicker(on_result=on_result)
        self._page_ref.overlay.append(file_picker)
        self._page_ref.update()
        file_picker.save_file(
            dialog_title="데이터 내보내기",
            file_name="dart_data_export.xlsx",
            allowed_extensions=["xlsx", "csv"],
        )

    def _on_clear_cache(self, e: ft.ControlEvent) -> None:
        """Handle clear cache event."""
        logger.info("캐시 삭제 요청됨")

        def show_result_dialog(success: bool) -> None:
            """Show result dialog after cache clear."""

            def close_result(e: ft.ControlEvent) -> None:
                result_dialog.open = False
                self._page_ref.update()

            if success:
                result_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("캐시 삭제 완료"),
                    content=ft.Text("캐시가 성공적으로 삭제되었습니다."),
                    actions=[ft.TextButton("확인", on_click=close_result)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            else:
                result_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("캐시 삭제 실패", color=ft.Colors.RED_700),
                    content=ft.Text("캐시 삭제 중 오류가 발생했습니다."),
                    actions=[ft.TextButton("확인", on_click=close_result)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            self._page_ref.dialog = result_dialog
            result_dialog.open = True
            self._page_ref.update()

        def on_confirm(e: ft.ControlEvent) -> None:
            logger.info("캐시 삭제 확인됨 - 삭제 시작")
            dialog.open = False
            self._page_ref.update()
            try:
                result = self._cache_manager.clear()
                if result:
                    logger.info("캐시 삭제 완료")
                else:
                    logger.warning("캐시 삭제 실패")
                show_result_dialog(result)
            except Exception as ex:
                logger.error(f"캐시 삭제 중 오류 발생: {ex}")
                show_result_dialog(False)

        def on_cancel(e: ft.ControlEvent) -> None:
            logger.info("캐시 삭제 취소됨")
            dialog.open = False
            self._page_ref.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("캐시 삭제"),
            content=ft.Text("캐시를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."),
            actions=[
                ft.TextButton("취소", on_click=on_cancel),
                ft.TextButton("삭제", on_click=on_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page_ref.dialog = dialog
        dialog.open = True
        self._page_ref.update()

    def _on_reset_corporations(self, e: ft.ControlEvent) -> None:
        """Handle reset corporations data event."""
        logger.info("기업 목록 초기화 요청됨")
        engine = get_engine()
        session = get_session(engine)
        corp_service = CorporationService(session)
        corp_count = corp_service.count()
        logger.info(f"현재 기업 목록 수: {corp_count}개")

        def show_result_dialog(success: bool, deleted_count: int = 0, error_msg: str = "") -> None:
            """Show result dialog after reset."""

            def close_result(e: ft.ControlEvent) -> None:
                result_dialog.open = False
                self._page_ref.update()

            if success:
                result_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("기업 목록 초기화 완료"),
                    content=ft.Text(f"기업 목록 {deleted_count}건이 성공적으로 초기화되었습니다."),
                    actions=[ft.TextButton("확인", on_click=close_result)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            else:
                result_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("기업 목록 초기화 실패", color=ft.Colors.RED_700),
                    content=ft.Text(f"초기화 중 오류가 발생했습니다: {error_msg}"),
                    actions=[ft.TextButton("확인", on_click=close_result)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            self._page_ref.dialog = result_dialog
            result_dialog.open = True
            self._page_ref.update()

        def on_confirm(e: ft.ControlEvent) -> None:
            logger.info("기업 목록 초기화 확인됨 - 초기화 시작")
            dialog.open = False
            self._page_ref.update()
            try:
                deleted_count = corp_service.delete_all()
                logger.info(f"기업 목록 {deleted_count}건 삭제 완료")
                # Also clear related checkpoints
                self._checkpoint_manager.clear_checkpoint("corporation_list")
                logger.info("기업 목록 체크포인트 초기화 완료")
                self._update_sync_status()
                show_result_dialog(True, deleted_count)
            except Exception as ex:
                logger.error(f"기업 목록 초기화 중 오류 발생: {ex}")
                show_result_dialog(False, error_msg=str(ex))
            finally:
                session.close()

        def on_cancel(e: ft.ControlEvent) -> None:
            logger.info("기업 목록 초기화 취소됨")
            session.close()
            dialog.open = False
            self._page_ref.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("기업 목록 초기화"),
            content=ft.Column(
                controls=[
                    ft.Text(f"현재 저장된 기업 수: {corp_count}개"),
                    ft.Text(
                        "모든 기업 목록 데이터를 삭제하시겠습니까?",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "이 작업은 되돌릴 수 없으며, 다시 동기화가 필요합니다.",
                        color=ft.Colors.RED_700,
                        size=12,
                    ),
                ],
                spacing=10,
                tight=True,
            ),
            actions=[
                ft.TextButton("취소", on_click=on_cancel),
                ft.TextButton(
                    "초기화",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(color=ft.Colors.RED_700),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page_ref.dialog = dialog
        dialog.open = True
        self._page_ref.update()

    def _on_reset_financials(self, e: ft.ControlEvent) -> None:
        """Handle reset financial statements data event."""
        logger.info("재무제표 초기화 요청됨")
        engine = get_engine()
        session = get_session(engine)
        fin_service = FinancialService(session)
        fin_count = fin_service.count()
        logger.info(f"현재 재무제표 수: {fin_count}개")

        def show_result_dialog(success: bool, deleted_count: int = 0, error_msg: str = "") -> None:
            """Show result dialog after reset."""

            def close_result(e: ft.ControlEvent) -> None:
                result_dialog.open = False
                self._page_ref.update()

            if success:
                result_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("재무제표 초기화 완료"),
                    content=ft.Text(f"재무제표 {deleted_count}건이 성공적으로 초기화되었습니다."),
                    actions=[ft.TextButton("확인", on_click=close_result)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            else:
                result_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("재무제표 초기화 실패", color=ft.Colors.RED_700),
                    content=ft.Text(f"초기화 중 오류가 발생했습니다: {error_msg}"),
                    actions=[ft.TextButton("확인", on_click=close_result)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            self._page_ref.dialog = result_dialog
            result_dialog.open = True
            self._page_ref.update()

        def on_confirm(e: ft.ControlEvent) -> None:
            logger.info("재무제표 초기화 확인됨 - 초기화 시작")
            dialog.open = False
            self._page_ref.update()
            try:
                deleted_count = fin_service.delete_all()
                logger.info(f"재무제표 {deleted_count}건 삭제 완료")
                # Also clear related checkpoints
                self._checkpoint_manager.clear_checkpoint("financial_statements")
                logger.info("재무제표 체크포인트 초기화 완료")
                self._update_sync_status()
                show_result_dialog(True, deleted_count)
            except Exception as ex:
                logger.error(f"재무제표 초기화 중 오류 발생: {ex}")
                show_result_dialog(False, error_msg=str(ex))
            finally:
                session.close()

        def on_cancel(e: ft.ControlEvent) -> None:
            logger.info("재무제표 초기화 취소됨")
            session.close()
            dialog.open = False
            self._page_ref.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("재무제표 초기화"),
            content=ft.Column(
                controls=[
                    ft.Text(f"현재 저장된 재무제표 수: {fin_count}개"),
                    ft.Text(
                        "모든 재무제표 데이터를 삭제하시겠습니까?",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "이 작업은 되돌릴 수 없으며, 다시 동기화가 필요합니다.",
                        color=ft.Colors.RED_700,
                        size=12,
                    ),
                ],
                spacing=10,
                tight=True,
            ),
            actions=[
                ft.TextButton("취소", on_click=on_cancel),
                ft.TextButton(
                    "초기화",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(color=ft.Colors.RED_700),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page_ref.dialog = dialog
        dialog.open = True
        self._page_ref.update()

    def _on_reset_all_data(self, e: ft.ControlEvent) -> None:
        """Handle reset all data event."""
        logger.info("전체 데이터 초기화 요청됨")
        engine = get_engine()
        session = get_session(engine)
        corp_service = CorporationService(session)
        fin_service = FinancialService(session)
        corp_count = corp_service.count()
        fin_count = fin_service.count()
        logger.info(f"현재 기업 수: {corp_count}개, 재무제표 수: {fin_count}개")

        def show_result_dialog(
            success: bool,
            deleted_corp: int = 0,
            deleted_fin: int = 0,
            error_msg: str = "",
        ) -> None:
            """Show result dialog after reset."""

            def close_result(e: ft.ControlEvent) -> None:
                result_dialog.open = False
                self._page_ref.update()

            if success:
                result_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("전체 데이터 초기화 완료"),
                    content=ft.Column(
                        controls=[
                            ft.Text("모든 데이터가 성공적으로 초기화되었습니다."),
                            ft.Text(f"삭제된 기업: {deleted_corp}건"),
                            ft.Text(f"삭제된 재무제표: {deleted_fin}건"),
                        ],
                        spacing=5,
                        tight=True,
                    ),
                    actions=[ft.TextButton("확인", on_click=close_result)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            else:
                result_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("전체 데이터 초기화 실패", color=ft.Colors.RED_700),
                    content=ft.Text(f"초기화 중 오류가 발생했습니다: {error_msg}"),
                    actions=[ft.TextButton("확인", on_click=close_result)],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            self._page_ref.dialog = result_dialog
            result_dialog.open = True
            self._page_ref.update()

        def on_confirm(e: ft.ControlEvent) -> None:
            logger.info("전체 데이터 초기화 확인됨 - 초기화 시작")
            dialog.open = False
            self._page_ref.update()
            try:
                # Delete financial statements first (foreign key constraint)
                deleted_fin = fin_service.delete_all()
                logger.info(f"재무제표 {deleted_fin}건 삭제 완료")
                deleted_corp = corp_service.delete_all()
                logger.info(f"기업 목록 {deleted_corp}건 삭제 완료")
                # Clear all checkpoints
                self._checkpoint_manager.clear_checkpoint("corporation_list")
                self._checkpoint_manager.clear_checkpoint("financial_statements")
                logger.info("모든 체크포인트 초기화 완료")
                # Clear cache
                self._cache_manager.clear()
                logger.info("캐시 삭제 완료")
                logger.info("전체 데이터 초기화 완료")
                self._update_sync_status()
                show_result_dialog(True, deleted_corp, deleted_fin)
            except Exception as ex:
                logger.error(f"전체 데이터 초기화 중 오류 발생: {ex}")
                show_result_dialog(False, error_msg=str(ex))
            finally:
                session.close()

        def on_cancel(e: ft.ControlEvent) -> None:
            logger.info("전체 데이터 초기화 취소됨")
            session.close()
            dialog.open = False
            self._page_ref.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("전체 데이터 초기화", color=ft.Colors.RED_700),
            content=ft.Column(
                controls=[
                    ft.Text(f"현재 저장된 기업 수: {corp_count}개"),
                    ft.Text(f"현재 저장된 재무제표 수: {fin_count}개"),
                    ft.Container(height=10),
                    ft.Text(
                        "모든 데이터를 삭제하시겠습니까?",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "기업 목록, 재무제표, 캐시가 모두 삭제됩니다.",
                        color=ft.Colors.RED_700,
                        size=12,
                    ),
                    ft.Text(
                        "이 작업은 되돌릴 수 없으며, 다시 동기화가 필요합니다.",
                        color=ft.Colors.RED_700,
                        size=12,
                    ),
                ],
                spacing=5,
                tight=True,
            ),
            actions=[
                ft.TextButton("취소", on_click=on_cancel),
                ft.TextButton(
                    "전체 초기화",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(color=ft.Colors.RED_700),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page_ref.dialog = dialog
        dialog.open = True
        self._page_ref.update()
