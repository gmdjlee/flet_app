"""Settings view - Application configuration."""

import flet as ft


class SettingsView(ft.View):
    """Settings view for application configuration."""

    def __init__(self, page: ft.Page) -> None:
        """Initialize SettingsView.

        Args:
            page: Flet page instance
        """
        self.page = page
        self.api_key_field = ft.TextField(
            label="DART API 키",
            hint_text="DART Open API 키를 입력하세요",
            password=True,
            can_reveal_password=True,
            expand=True,
        )
        super().__init__(
            route="/settings",
            controls=[self._build()],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

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
                    self._build_data_section(),
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
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
                                ft.ElevatedButton(
                                    text="저장",
                                    icon=ft.Icons.SAVE,
                                    on_click=self._on_save_api_key,
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
                        ft.Text(
                            "데이터 동기화",
                            size=18,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            "DART에서 최신 기업 목록과 재무 데이터를 가져옵니다.",
                            size=12,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    text="기업 목록 동기화",
                                    icon=ft.Icons.SYNC,
                                    on_click=self._on_sync_corporations,
                                ),
                                ft.ElevatedButton(
                                    text="재무제표 동기화",
                                    icon=ft.Icons.SYNC_ALT,
                                    on_click=self._on_sync_financials,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.ProgressBar(visible=False),
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
                                ft.OutlinedButton(
                                    text="데이터 내보내기",
                                    icon=ft.Icons.DOWNLOAD,
                                    on_click=self._on_export_data,
                                ),
                                ft.OutlinedButton(
                                    text="캐시 삭제",
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    on_click=self._on_clear_cache,
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

    def _on_save_api_key(self, e: ft.ControlEvent) -> None:
        """Handle save API key event."""
        api_key = self.api_key_field.value
        if api_key:
            # TODO: Save API key securely
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("API 키가 저장되었습니다."),
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _on_sync_corporations(self, e: ft.ControlEvent) -> None:
        """Handle sync corporations event."""
        # TODO: Implement corporation sync
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("기업 목록 동기화를 시작합니다..."),
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_sync_financials(self, e: ft.ControlEvent) -> None:
        """Handle sync financials event."""
        # TODO: Implement financial sync
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("재무제표 동기화를 시작합니다..."),
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_export_data(self, e: ft.ControlEvent) -> None:
        """Handle export data event."""
        # TODO: Implement data export
        pass

    def _on_clear_cache(self, e: ft.ControlEvent) -> None:
        """Handle clear cache event."""
        # TODO: Implement cache clearing
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("캐시가 삭제되었습니다."),
        )
        self.page.snack_bar.open = True
        self.page.update()
