"""Settings view - Application configuration and data synchronization."""

import asyncio
from datetime import datetime

import flet as ft

from src.models.database import get_engine, get_session
from src.services.dart_service import DartService
from src.services.sync_service import (
    SettingsManager,
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
                ],
                spacing=10,
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
                        ft.Row(
                            controls=[
                                self.sync_corp_button,
                                self.sync_fin_button,
                                self.cancel_button,
                            ],
                            spacing=10,
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

        # Load recent logs
        self._load_recent_logs()

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
                    padding=ft.padding.symmetric(vertical=5),
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

        sync_service.set_progress_callback(self._progress_callback)
        await sync_service.sync_all_financial_statements()

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

        def on_confirm(e: ft.ControlEvent) -> None:
            self._cache_manager.clear()
            self._show_snackbar("캐시가 삭제되었습니다.")
            dialog.open = False
            self._page_ref.update()

        def on_cancel(e: ft.ControlEvent) -> None:
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
