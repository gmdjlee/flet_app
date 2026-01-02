"""SearchBar component for searching corporations."""

from collections.abc import Callable

import flet as ft


class SearchBar(ft.Container):
    """Search bar component with autocomplete and recent searches.

    Attributes:
        search_field: The text input field for search.
        recent_searches: List of recent search queries.
        on_search: Callback function when search is performed.
        max_recent: Maximum number of recent searches to store.
    """

    def __init__(
        self,
        on_search: Callable[[str], None] | None = None,
        on_change: Callable[[str], None] | None = None,
        hint_text: str = "기업명 또는 종목코드로 검색",
        max_recent: int = 5,
        **kwargs,
    ) -> None:
        """Initialize SearchBar.

        Args:
            on_search: Callback when search is submitted.
            on_change: Callback when search text changes.
            hint_text: Placeholder text for the search field.
            max_recent: Maximum number of recent searches to store.
            **kwargs: Additional container properties.
        """
        self.on_search_callback = on_search
        self.on_change_callback = on_change
        self.max_recent = max_recent
        self.recent_searches: list[str] = []

        # Create search field
        self.search_field = ft.TextField(
            hint_text=hint_text,
            prefix_icon=ft.Icons.SEARCH,
            suffix=ft.IconButton(
                icon=ft.Icons.CLEAR,
                icon_size=18,
                tooltip="지우기",
                on_click=self._on_clear,
            ),
            on_submit=self._on_submit,
            on_change=self._on_change,
            expand=True,
            border_radius=25,
            content_padding=ft.Padding(left=20, right=20, top=5, bottom=5),
        )

        # Search button
        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH,
            tooltip="검색",
            on_click=self._on_submit,
            icon_color=ft.Colors.PRIMARY,
        )

        # Build the component
        super().__init__(
            content=ft.Row(
                controls=[
                    self.search_field,
                    self.search_button,
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            **kwargs,
        )

    def _on_submit(self, e: ft.ControlEvent | None) -> None:
        """Handle search submission.

        Args:
            e: Control event (can be None).
        """
        query = self.search_field.value or ""
        query = query.strip()

        if query:
            self.add_recent_search(query)

        if self.on_search_callback:
            self.on_search_callback(query)

    def _on_change(self, e: ft.ControlEvent) -> None:
        """Handle text change event.

        Args:
            e: Control event.
        """
        if self.on_change_callback:
            self.on_change_callback(e.control.value or "")

    def _on_clear(self, e: ft.ControlEvent | None) -> None:
        """Clear the search field.

        Args:
            e: Control event (can be None).
        """
        self.search_field.value = ""
        try:
            if self.search_field.page:
                self.search_field.update()
        except RuntimeError:
            pass  # Control not yet added to page

        # Trigger search with empty query to reset
        if self.on_search_callback:
            self.on_search_callback("")

    def add_recent_search(self, query: str) -> None:
        """Add a query to recent searches.

        Args:
            query: Search query to add.
        """
        query = query.strip()
        if not query:
            return

        # Remove if already exists (to move to front)
        if query in self.recent_searches:
            self.recent_searches.remove(query)

        # Add to front
        self.recent_searches.insert(0, query)

        # Trim to max size
        if len(self.recent_searches) > self.max_recent:
            self.recent_searches = self.recent_searches[: self.max_recent]

    def clear_recent_searches(self) -> None:
        """Clear all recent searches."""
        self.recent_searches.clear()

    def get_value(self) -> str:
        """Get the current search field value.

        Returns:
            Current value of the search field.
        """
        return self.search_field.value or ""

    def set_value(self, value: str) -> None:
        """Set the search field value.

        Args:
            value: Value to set.
        """
        self.search_field.value = value
        if self.search_field.page:
            self.search_field.update()

    def build_recent_dropdown(self) -> ft.PopupMenuButton | None:
        """Build a dropdown showing recent searches.

        Returns:
            PopupMenuButton with recent searches or None if empty.
        """
        if not self.recent_searches:
            return None

        items = []
        for query in self.recent_searches:
            items.append(
                ft.PopupMenuItem(
                    text=query,
                    on_click=lambda e, q=query: self._select_recent(q),
                )
            )

        items.append(ft.PopupMenuItem())  # Divider
        items.append(
            ft.PopupMenuItem(
                text="검색 기록 삭제",
                icon=ft.Icons.DELETE_OUTLINE,
                on_click=lambda e: self.clear_recent_searches(),
            )
        )

        return ft.PopupMenuButton(
            icon=ft.Icons.HISTORY,
            tooltip="최근 검색",
            items=items,
        )

    def _select_recent(self, query: str) -> None:
        """Select a recent search query.

        Args:
            query: Query to select.
        """
        self.set_value(query)
        if self.on_search_callback:
            self.on_search_callback(query)
