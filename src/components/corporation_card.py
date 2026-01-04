"""CorporationCard component for displaying corporation info."""

from collections.abc import Callable

import flet as ft

from src.models.corporation import Corporation


class CorporationCard(ft.Card):
    """Card component displaying corporation information.

    Displays corporation name, stock code, market type, and other
    relevant information in a card format.

    Attributes:
        corporation: The corporation data to display.
        on_click_callback: Callback function when card is clicked.
        market_badge: Badge showing the market type.
    """

    # Market badge colors
    MARKET_COLORS = {
        "KOSPI": ft.Colors.BLUE,
        "KOSDAQ": ft.Colors.GREEN,
        "KONEX": ft.Colors.ORANGE,
        "Y": ft.Colors.BLUE,
        "K": ft.Colors.GREEN,
        "N": ft.Colors.ORANGE,
    }

    def __init__(
        self,
        corporation: Corporation,
        on_click: Callable[[Corporation], None] | None = None,
        **kwargs,
    ) -> None:
        """Initialize CorporationCard.

        Args:
            corporation: Corporation data to display.
            on_click: Callback when card is clicked.
            **kwargs: Additional card properties.
        """
        self.corporation = corporation
        self.on_click_callback = on_click

        # Create market badge
        self.market_badge = self._create_market_badge()

        # Build card content
        content = self._build_content()

        super().__init__(
            content=ft.Container(
                content=content,
                padding=15,
                on_click=self._on_click,
                ink=True,
            ),
            elevation=2,
            **kwargs,
        )

    def _create_market_badge(self) -> ft.Container:
        """Create a badge showing the market type.

        Returns:
            Container with market badge.
        """
        market = self.corporation.market or self.corporation.corp_cls
        market_display = self.corporation.market_display

        color = self.MARKET_COLORS.get(market, ft.Colors.GREY)

        return ft.Container(
            content=ft.Text(
                market_display,
                size=11,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
            ),
            bgcolor=color,
            border_radius=4,
            padding=ft.Padding(left=8, right=8, top=2, bottom=2),
        )

    def _build_content(self) -> ft.Control:
        """Build the card content layout.

        Returns:
            Card content control.
        """
        # Stock code display
        stock_code_text = self.corporation.stock_code or "-"

        # CEO name if available
        ceo_row = None
        if self.corporation.ceo_nm:
            ceo_row = ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.PERSON_OUTLINE,
                        size=14,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        self.corporation.ceo_nm,
                        size=12,
                        color=ft.Colors.GREY_600,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=5,
            )

        # Build main content
        content_controls = [
            # Header row with name and badge
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            self.corporation.corp_name,
                            size=16,
                            weight=ft.FontWeight.W_600,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        expand=True,
                    ),
                    self.market_badge,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(height=8),
            # Stock code row
            ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.TAG,
                        size=14,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        f"종목코드: {stock_code_text}",
                        size=13,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                spacing=5,
            ),
        ]

        # Add CEO row if available
        if ceo_row:
            content_controls.append(ceo_row)

        return ft.Column(
            controls=content_controls,
            spacing=4,
            tight=True,
        )

    def _on_click(self, e: ft.ControlEvent) -> None:
        """Handle card click event.

        Args:
            e: Control event.
        """
        if self.on_click_callback:
            self.on_click_callback(self.corporation)


class CorporationListTile(ft.ListTile):
    """List tile version of corporation card for compact display.

    Attributes:
        corporation: The corporation data to display.
        on_click_callback: Callback function when tile is clicked.
    """

    MARKET_COLORS = CorporationCard.MARKET_COLORS

    def __init__(
        self,
        corporation: Corporation,
        on_click: Callable[[Corporation], None] | None = None,
        **kwargs,
    ) -> None:
        """Initialize CorporationListTile.

        Args:
            corporation: Corporation data to display.
            on_click: Callback when tile is clicked.
            **kwargs: Additional tile properties.
        """
        self.corporation = corporation
        self.on_click_callback = on_click

        # Market badge
        market = corporation.market or corporation.corp_cls
        market_display = corporation.market_display
        badge_color = self.MARKET_COLORS.get(market, ft.Colors.GREY)

        # Stock code
        stock_code = corporation.stock_code or "-"

        super().__init__(
            leading=ft.Container(
                content=ft.Text(
                    market_display[:1],
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                width=36,
                height=36,
                bgcolor=badge_color,
                border_radius=18,
                alignment=ft.alignment.center,
            ),
            title=ft.Text(
                corporation.corp_name,
                weight=ft.FontWeight.W_500,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            subtitle=ft.Text(
                f"{stock_code} • {market_display}",
                size=12,
                color=ft.Colors.GREY_600,
            ),
            trailing=ft.Icon(
                ft.Icons.CHEVRON_RIGHT,
                color=ft.Colors.GREY_400,
            ),
            on_click=self._on_click,
            **kwargs,
        )

    def _on_click(self, e: ft.ControlEvent) -> None:
        """Handle tile click event.

        Args:
            e: Control event.
        """
        if self.on_click_callback:
            self.on_click_callback(self.corporation)
