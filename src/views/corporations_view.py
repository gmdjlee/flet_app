"""Corporations view - Company list and search."""

from collections.abc import Callable

import flet as ft
from sqlalchemy.orm import Session

from src.components.corporation_card import CorporationCard, CorporationListTile
from src.components.search_bar import SearchBar
from src.models.corporation import Corporation
from src.models.database import get_engine, get_session
from src.services.corporation_service import CorporationService


class CorporationsView(ft.View):
    """Corporations view displaying company list and search.

    Provides search, filtering, pagination, and responsive layout
    for browsing corporations.

    Attributes:
        page: Flet page instance.
        session: Database session.
        current_page: Current pagination page.
        items_per_page: Number of items per page.
        selected_market: Currently selected market filter.
        search_query: Current search query.
        corporations: List of loaded corporations.
        total_count: Total count of matching corporations.
        is_loading: Loading state flag.
        grid_columns: Number of grid columns (responsive).
    """

    def __init__(
        self,
        page: ft.Page,
        session: Session | None = None,
        on_corporation_select: Callable[[Corporation], None] | None = None,
    ) -> None:
        """Initialize CorporationsView.

        Args:
            page: Flet page instance.
            session: Database session (optional, creates new if not provided).
            on_corporation_select: Callback when corporation is selected.
        """
        self._page_ref = page
        self._session = session
        self.on_corporation_select = on_corporation_select

        # Pagination state
        self.current_page = 1
        self.items_per_page = 20
        self.total_count = 0
        self.total_pages = 1

        # Filter state
        self.selected_market = "ALL"
        self.search_query = ""

        # Data
        self.corporations: list[Corporation] = []

        # Loading state
        self.is_loading = False
        self.loading_indicator = ft.ProgressRing(
            width=40,
            height=40,
            stroke_width=4,
            visible=False,
        )

        # Responsive layout
        self.grid_columns = self._calculate_grid_columns()

        # Create search bar
        self.search_bar = SearchBar(
            on_search=self._on_search,
            on_change=self._on_search_change,
        )

        # Filter chips
        self.filter_chips: dict[str, ft.Chip] = {}

        # Corporation list container
        self.corporation_list_container = ft.Container(expand=True)

        # Pagination text
        self.pagination_text = ft.Text(f"페이지 {self.current_page}")

        # Build the view
        super().__init__(
            route="/corporations",
            controls=[self._build()],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        # Load initial data
        self._load_corporations()

    @property
    def session(self) -> Session:
        """Get or create database session."""
        if self._session is None:
            engine = get_engine()
            self._session = get_session(engine)
        return self._session

    def _calculate_grid_columns(self) -> int:
        """Calculate number of grid columns based on page width.

        Returns:
            Number of columns for the grid layout.
        """
        try:
            width = self._page_ref.width or 1200
        except (AttributeError, TypeError):
            width = 1200

        if width >= 1200:
            return 4
        elif width >= 900:
            return 3
        elif width >= 600:
            return 2
        else:
            return 1

    def _build(self) -> ft.Control:
        """Build the corporations view content.

        Returns:
            Main content container.
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Row(
                        controls=[
                            ft.Text(
                                "기업 목록",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Container(expand=True),
                            self.loading_indicator,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=10),
                    # Search bar
                    self.search_bar,
                    ft.Container(height=10),
                    # Filter chips
                    self._build_filter_chips(),
                    ft.Container(height=10),
                    # Statistics row
                    self._build_stats_row(),
                    ft.Divider(height=10),
                    # Corporation list
                    self.corporation_list_container,
                    # Pagination
                    self._build_pagination(),
                ],
                spacing=5,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=30,
            expand=True,
        )

    def _build_filter_chips(self) -> ft.Control:
        """Build filter chips for market selection.

        Returns:
            Row containing filter chips.
        """
        markets = [
            ("ALL", "전체"),
            ("KOSPI", "KOSPI"),
            ("KOSDAQ", "KOSDAQ"),
            ("KONEX", "KONEX"),
        ]

        chips = []
        for market_code, label in markets:
            chip = ft.Chip(
                label=ft.Text(label),
                selected=self.selected_market == market_code,
                on_select=lambda e, m=market_code: self._on_filter_change(m),
            )
            self.filter_chips[market_code] = chip
            chips.append(chip)

        return ft.Row(controls=chips, spacing=10, wrap=True)

    def _build_stats_row(self) -> ft.Control:
        """Build statistics row.

        Returns:
            Row containing statistics.
        """
        self.stats_text = ft.Text(
            f"총 {self.total_count}개 기업",
            size=14,
            color=ft.Colors.GREY_600,
        )
        return ft.Row(
            controls=[
                self.stats_text,
                ft.Container(expand=True),
                ft.Text(
                    f"{self.items_per_page}개씩 보기",
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
            ],
        )

    def _build_pagination(self) -> ft.Control:
        """Build pagination controls.

        Returns:
            Row containing pagination controls.
        """
        self.prev_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            tooltip="이전",
            on_click=self._prev_page,
            disabled=self.current_page <= 1,
        )

        self.next_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            tooltip="다음",
            on_click=self._next_page,
            disabled=self.current_page >= self.total_pages,
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    self.prev_button,
                    ft.Container(width=10),
                    self.pagination_text,
                    ft.Container(width=10),
                    self.next_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=0, right=0, top=20, bottom=20),
        )

    def _build_corporation_list(self) -> ft.Control:
        """Build the corporation list display.

        Returns:
            Container with corporation cards or empty state.
        """
        if not self.corporations:
            return self._build_empty_state()

        # Use list view for narrow screens, grid for wide screens
        if self.grid_columns <= 1:
            return self._build_list_view()
        else:
            return self._build_grid_view()

    def _build_list_view(self) -> ft.Control:
        """Build list view for narrow screens.

        Returns:
            Column with list tiles.
        """
        tiles = []
        for corp in self.corporations:
            tile = CorporationListTile(
                corporation=corp,
                on_click=self._on_corporation_click,
            )
            tiles.append(tile)

        return ft.Column(
            controls=tiles,
            spacing=2,
        )

    def _build_grid_view(self) -> ft.Control:
        """Build grid view for wide screens.

        Returns:
            ResponsiveRow with corporation cards.
        """
        cards = []
        for corp in self.corporations:
            card = CorporationCard(
                corporation=corp,
                on_click=self._on_corporation_click,
            )
            # Responsive column sizing
            col_size = 12 // self.grid_columns
            cards.append(
                ft.Container(
                    content=card,
                    col={"xs": 12, "sm": 6, "md": 4, "lg": col_size},
                    padding=5,
                )
            )

        return ft.ResponsiveRow(
            controls=cards,
            spacing=10,
            run_spacing=10,
        )

    def _build_empty_state(self) -> ft.Control:
        """Build empty state display.

        Returns:
            Container with empty state message.
        """
        if self.search_query or self.selected_market != "ALL":
            message = "검색 결과가 없습니다."
            icon = ft.Icons.SEARCH_OFF
        else:
            message = "기업 데이터를 불러오려면 설정에서 DART API 키를 등록하고 동기화하세요."
            icon = ft.Icons.CLOUD_DOWNLOAD_OUTLINED

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icon,
                        size=64,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        message,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=50,
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
        )

    def _load_corporations(self) -> None:
        """Load corporations from database."""
        self._set_loading(True)

        try:
            service = CorporationService(self.session)

            # Get total count
            if self.search_query:
                # Search mode - get count by searching
                all_results = service.search_by_multiple_fields(
                    self.search_query, page=1, page_size=10000
                )
                if self.selected_market != "ALL":
                    all_results = [c for c in all_results if c.market == self.selected_market]
                self.total_count = len(all_results)
            elif self.selected_market != "ALL":
                # Filter by market - count all in that market
                all_in_market = service.list_by_market(
                    self.selected_market, page=1, page_size=10000
                )
                self.total_count = len(all_in_market)
            else:
                self.total_count = service.count()

            # Calculate total pages
            self.total_pages = max(
                1, (self.total_count + self.items_per_page - 1) // self.items_per_page
            )

            # Ensure current page is valid
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages

            # Load corporations for current page
            if self.search_query:
                results = service.search_by_multiple_fields(
                    self.search_query,
                    page=self.current_page,
                    page_size=self.items_per_page,
                )
                if self.selected_market != "ALL":
                    results = [c for c in results if c.market == self.selected_market]
                self.corporations = results
            elif self.selected_market != "ALL":
                self.corporations = service.list_by_market(
                    self.selected_market,
                    page=self.current_page,
                    page_size=self.items_per_page,
                )
            else:
                self.corporations = service.list_all(
                    page=self.current_page,
                    page_size=self.items_per_page,
                )

        except Exception as e:
            print(f"Error loading corporations: {e}")
            self.corporations = []
            self.total_count = 0
            self.total_pages = 1
        finally:
            self._set_loading(False)
            self._update_display()

    def _set_loading(self, is_loading: bool) -> None:
        """Set loading state.

        Args:
            is_loading: Whether loading is in progress.
        """
        self.is_loading = is_loading
        self.loading_indicator.visible = is_loading
        if self._page_ref:
            try:
                self.loading_indicator.update()
            except Exception:
                pass

    def _update_display(self) -> None:
        """Update the display after data changes."""
        # Update grid columns based on current width
        self.grid_columns = self._calculate_grid_columns()

        # Update corporation list
        self.corporation_list_container.content = self._build_corporation_list()

        # Update pagination
        self.pagination_text.value = f"페이지 {self.current_page} / {self.total_pages}"
        self.prev_button.disabled = self.current_page <= 1
        self.next_button.disabled = self.current_page >= self.total_pages

        # Update stats
        self.stats_text.value = f"총 {self.total_count}개 기업"

        # Update filter chips selection
        for market_code, chip in self.filter_chips.items():
            chip.selected = market_code == self.selected_market

        # Update page
        if self._page_ref:
            try:
                self._page_ref.update()
            except Exception:
                pass

    def _on_search(self, query: str) -> None:
        """Handle search submission.

        Args:
            query: Search query string.
        """
        self.search_query = query.strip()
        self.current_page = 1  # Reset to first page
        self._load_corporations()

    def _on_search_change(self, query: str) -> None:
        """Handle search text change (for live filtering).

        Args:
            query: Current search query.
        """
        # Optional: implement live search with debounce
        pass

    def _perform_search(self) -> None:
        """Perform search with current query."""
        self._load_corporations()

    def _on_filter_change(self, market: str) -> None:
        """Handle filter change event.

        Args:
            market: Market code to filter by.
        """
        self.selected_market = market
        self.current_page = 1  # Reset to first page
        self._load_corporations()

    def _prev_page(self, e: ft.ControlEvent | None) -> None:
        """Go to previous page.

        Args:
            e: Control event.
        """
        if self.current_page > 1:
            self.current_page -= 1
            self._load_corporations()

    def _next_page(self, e: ft.ControlEvent | None) -> None:
        """Go to next page.

        Args:
            e: Control event.
        """
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._load_corporations()

    def _on_corporation_click(self, corporation: Corporation) -> None:
        """Handle corporation card/tile click.

        Args:
            corporation: Selected corporation.
        """
        if self.on_corporation_select:
            self.on_corporation_select(corporation)
        else:
            # Navigate to detail view (placeholder)
            print(f"Selected: {corporation.corp_name} ({corporation.corp_code})")
            # self.page.go(f"/corporations/{corporation.corp_code}")

    def refresh(self) -> None:
        """Refresh the corporation list."""
        self._load_corporations()
