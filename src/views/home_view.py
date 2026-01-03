"""Home view - Dashboard main page."""

import flet as ft


class HomeView(ft.View):
    """Home view displaying the main dashboard."""

    def __init__(self, page: ft.Page) -> None:
        """Initialize HomeView.

        Args:
            page: Flet page instance
        """
        self._page_ref = page
        super().__init__(
            route="/",
            controls=[self._build()],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

    def _build(self) -> ft.Control:
        """Build the home view content."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "DART-DB",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "한국 상장기업 전자공시 데이터 분석",
                        size=16,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Divider(height=20),
                    self._build_stats_row(),
                    ft.Divider(height=20),
                    self._build_quick_actions(),
                ],
                spacing=10,
            ),
            padding=30,
        )

    def _build_stats_row(self) -> ft.Control:
        """Build the statistics row."""
        return ft.ResponsiveRow(
            controls=[
                self._stat_card("등록 기업", "0", ft.Icons.BUSINESS, col=4),
                self._stat_card("수집 공시", "0", ft.Icons.DESCRIPTION, col=4),
                self._stat_card("재무제표", "0", ft.Icons.TABLE_CHART, col=4),
            ],
        )

    def _stat_card(self, title: str, value: str, icon: str, col: int = 4) -> ft.Control:
        """Create a statistics card.

        Args:
            title: Card title
            value: Statistical value to display
            icon: Icon name
            col: Column span for responsive layout

        Returns:
            Card control
        """
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(icon, size=24, color=ft.Colors.BLUE_400),
                                    ft.Text(title, size=14, color=ft.Colors.GREY_600),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            ft.Text(
                                value,
                                size=28,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=20,
                ),
            ),
            col={"sm": 12, "md": col, "lg": col},
        )

    def _build_quick_actions(self) -> ft.Control:
        """Build quick action buttons."""
        return ft.Column(
            controls=[
                ft.Text(
                    "빠른 작업",
                    size=18,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Row(
                    controls=[
                        ft.Button(
                            "기업 검색",
                            icon=ft.Icons.SEARCH,
                            on_click=lambda _: self._page_ref.go("/corporations"),
                        ),
                        ft.Button(
                            "데이터 동기화",
                            icon=ft.Icons.SYNC,
                            on_click=lambda _: self._page_ref.go("/settings"),
                        ),
                    ],
                    spacing=10,
                ),
            ],
            spacing=10,
        )
