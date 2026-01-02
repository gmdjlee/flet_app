"""Corporations view - Company list and search."""

import flet as ft


class CorporationsView(ft.View):
    """Corporations view displaying company list and search."""

    def __init__(self, page: ft.Page) -> None:
        """Initialize CorporationsView.

        Args:
            page: Flet page instance
        """
        self.page = page
        self.current_page = 1
        self.items_per_page = 20
        self.search_field = ft.TextField(
            hint_text="기업명 또는 종목코드로 검색",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_submit=self._on_search,
        )
        super().__init__(
            route="/corporations",
            controls=[self._build()],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

    def _build(self) -> ft.Control:
        """Build the corporations view content."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "기업 목록",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(height=10),
                    self._build_search_bar(),
                    ft.Divider(height=10),
                    self._build_filter_chips(),
                    ft.Divider(height=10),
                    self._build_corporation_list(),
                    self._build_pagination(),
                ],
                spacing=5,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=30,
            expand=True,
        )

    def _build_search_bar(self) -> ft.Control:
        """Build the search bar."""
        return ft.Row(
            controls=[
                self.search_field,
                ft.IconButton(
                    icon=ft.Icons.SEARCH,
                    tooltip="검색",
                    on_click=self._on_search,
                ),
            ],
        )

    def _build_filter_chips(self) -> ft.Control:
        """Build filter chips for market selection."""
        return ft.Row(
            controls=[
                ft.Chip(
                    label=ft.Text("전체"),
                    selected=True,
                    on_select=lambda e: self._on_filter_change("ALL"),
                ),
                ft.Chip(
                    label=ft.Text("KOSPI"),
                    on_select=lambda e: self._on_filter_change("KOSPI"),
                ),
                ft.Chip(
                    label=ft.Text("KOSDAQ"),
                    on_select=lambda e: self._on_filter_change("KOSDAQ"),
                ),
            ],
            spacing=10,
        )

    def _build_corporation_list(self) -> ft.Control:
        """Build the corporation list (placeholder)."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "기업 데이터를 불러오려면 설정에서 DART API 키를 등록하고 동기화하세요.",
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=50,
            alignment=ft.alignment.center,
            expand=True,
        )

    def _build_pagination(self) -> ft.Control:
        """Build pagination controls."""
        return ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    tooltip="이전",
                    on_click=self._prev_page,
                    disabled=self.current_page <= 1,
                ),
                ft.Text(f"페이지 {self.current_page}"),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    tooltip="다음",
                    on_click=self._next_page,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _on_search(self, e: ft.ControlEvent) -> None:
        """Handle search event."""
        search_text = self.search_field.value
        # TODO: Implement search logic
        print(f"Searching for: {search_text}")

    def _on_filter_change(self, market: str) -> None:
        """Handle filter change event."""
        # TODO: Implement filter logic
        print(f"Filter changed to: {market}")

    def _prev_page(self, e: ft.ControlEvent) -> None:
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.page.update()

    def _next_page(self, e: ft.ControlEvent) -> None:
        """Go to next page."""
        self.current_page += 1
        self.page.update()
