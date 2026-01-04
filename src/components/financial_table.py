"""Financial Table component for displaying financial statements."""

from collections.abc import Callable

import flet as ft

from src.models.financial_statement import FinancialStatement
from src.utils.formatters import format_amount_short, format_growth, get_growth_color


class FinancialTable(ft.Container):
    """Table component for displaying financial statements.

    Displays financial statement data in a DataTable format with
    account names and multi-year values.

    Attributes:
        statements: List of FinancialStatement objects to display.
        show_yoy: Whether to show year-over-year changes.
    """

    def __init__(
        self,
        statements: list[FinancialStatement] | None = None,
        show_yoy: bool = True,
        on_row_click: Callable[[FinancialStatement], None] | None = None,
    ) -> None:
        """Initialize FinancialTable.

        Args:
            statements: List of financial statements to display.
            show_yoy: Whether to show YoY change column.
            on_row_click: Callback when row is clicked.
        """
        self.statements = statements or []
        self.show_yoy = show_yoy
        self.on_row_click = on_row_click

        super().__init__(
            content=self._build(),
            expand=True,
        )

    def _build(self) -> ft.Control:
        """Build the financial table.

        Returns:
            DataTable or empty state container.
        """
        if not self.statements:
            return self._build_empty_state()

        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.DataTable(
                        columns=self._build_columns(),
                        rows=self._build_rows(),
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                        horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_200),
                        heading_row_color=ft.Colors.GREY_100,
                        data_row_min_height=40,
                        data_row_max_height=50,
                        column_spacing=20,
                    ),
                    expand=True,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_empty_state(self) -> ft.Control:
        """Build empty state display.

        Returns:
            Container with empty message.
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.TABLE_CHART_OUTLINED,
                        size=48,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Text(
                        "재무제표 데이터가 없습니다",
                        color=ft.Colors.GREY_500,
                        size=14,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=30,
            alignment=ft.alignment.center,
        )

    def _build_columns(self) -> list[ft.DataColumn]:
        """Build table columns.

        Returns:
            List of DataColumn objects.
        """
        columns = [
            ft.DataColumn(
                ft.Text("계정명", weight=ft.FontWeight.BOLD),
            ),
            ft.DataColumn(
                ft.Text("당기", weight=ft.FontWeight.BOLD),
                numeric=True,
            ),
            ft.DataColumn(
                ft.Text("전기", weight=ft.FontWeight.BOLD),
                numeric=True,
            ),
            ft.DataColumn(
                ft.Text("전전기", weight=ft.FontWeight.BOLD),
                numeric=True,
            ),
        ]

        if self.show_yoy:
            columns.append(
                ft.DataColumn(
                    ft.Text("YoY", weight=ft.FontWeight.BOLD),
                    numeric=True,
                    tooltip="전년 대비 증감률",
                )
            )

        return columns

    def get_columns(self) -> list[ft.DataColumn]:
        """Get table columns (for testing).

        Returns:
            List of DataColumn objects.
        """
        return self._build_columns()

    def _build_rows(self) -> list[ft.DataRow]:
        """Build table rows.

        Returns:
            List of DataRow objects.
        """
        rows = []

        for stmt in self.statements:
            cells = [
                # Account name cell
                ft.DataCell(
                    ft.Text(
                        stmt.account_nm,
                        weight=ft.FontWeight.W_500 if self._is_total_row(stmt) else None,
                    )
                ),
                # Current term
                ft.DataCell(
                    ft.Text(
                        format_amount_short(stmt.thstrm_amount),
                        text_align=ft.TextAlign.RIGHT,
                    )
                ),
                # Prior term
                ft.DataCell(
                    ft.Text(
                        format_amount_short(stmt.frmtrm_amount),
                        text_align=ft.TextAlign.RIGHT,
                    )
                ),
                # Before prior term
                ft.DataCell(
                    ft.Text(
                        format_amount_short(stmt.bfefrmtrm_amount),
                        text_align=ft.TextAlign.RIGHT,
                    )
                ),
            ]

            # YoY change column
            if self.show_yoy:
                yoy = self._calculate_yoy(stmt)
                yoy_color = get_growth_color(yoy)
                cells.append(
                    ft.DataCell(
                        ft.Text(
                            format_growth(yoy),
                            color=yoy_color,
                            text_align=ft.TextAlign.RIGHT,
                            weight=ft.FontWeight.W_500,
                        )
                    )
                )

            row = ft.DataRow(
                cells=cells,
                on_select_change=(
                    lambda e, s=stmt: self._on_row_select(s) if self.on_row_click else None
                ),
                color=ft.Colors.BLUE_50 if self._is_total_row(stmt) else None,
            )
            rows.append(row)

        return rows

    def _is_total_row(self, stmt: FinancialStatement) -> bool:
        """Check if statement is a total/summary row.

        Args:
            stmt: Financial statement.

        Returns:
            True if this is a total row.
        """
        total_keywords = ["총계", "합계", "계"]
        return any(kw in stmt.account_nm for kw in total_keywords)

    def _calculate_yoy(self, stmt: FinancialStatement) -> float | None:
        """Calculate year-over-year change.

        Args:
            stmt: Financial statement.

        Returns:
            YoY change as percentage.
        """
        current = stmt.thstrm_amount
        prior = stmt.frmtrm_amount

        if current is None or prior is None or prior == 0:
            return None

        return ((current - prior) / abs(prior)) * 100

    def _on_row_select(self, statement: FinancialStatement) -> None:
        """Handle row selection.

        Args:
            statement: Selected financial statement.
        """
        if self.on_row_click:
            self.on_row_click(statement)

    def update_data(self, statements: list[FinancialStatement]) -> None:
        """Update table with new data.

        Args:
            statements: New list of financial statements.
        """
        self.statements = statements
        self.content = self._build()


class FinancialSummaryCard(ft.Container):
    """Card component displaying financial summary metrics."""

    def __init__(
        self,
        title: str,
        value: int | float | None,
        subtitle: str | None = None,
        icon: str | None = None,
        change: float | None = None,
        format_type: str = "amount",
    ) -> None:
        """Initialize summary card.

        Args:
            title: Card title.
            value: Main value to display.
            subtitle: Optional subtitle.
            icon: Optional icon name.
            change: Optional change percentage.
            format_type: "amount" or "percentage".
        """
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.icon = icon
        self.change = change
        self.format_type = format_type

        super().__init__(
            content=self._build(),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
        )

    def _build(self) -> ft.Control:
        """Build the card content.

        Returns:
            Card layout.
        """
        # Format value
        if self.value is None:
            display_value = "-"
        elif self.format_type == "percentage":
            display_value = f"{self.value:.2f}%"
        else:
            display_value = format_amount_short(self.value)

        # Build change indicator
        change_row = []
        if self.change is not None:
            change_color = get_growth_color(self.change)
            change_text = format_growth(self.change)
            change_row = [
                ft.Container(height=5),
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.ARROW_UPWARD if self.change >= 0 else ft.Icons.ARROW_DOWNWARD,
                            size=14,
                            color=change_color,
                        ),
                        ft.Text(
                            change_text,
                            color=change_color,
                            size=12,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=2,
                ),
            ]

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(
                            self.icon or ft.Icons.ANALYTICS,
                            color=ft.Colors.BLUE_400,
                            size=20,
                        ),
                        ft.Text(
                            self.title,
                            size=12,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                    spacing=5,
                ),
                ft.Container(height=5),
                ft.Text(
                    display_value,
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),
                *change_row,
                *(
                    [
                        ft.Text(
                            self.subtitle,
                            size=11,
                            color=ft.Colors.GREY_500,
                        )
                    ]
                    if self.subtitle
                    else []
                ),
            ],
            spacing=0,
        )


class RatioIndicator(ft.Container):
    """Indicator component for displaying financial ratios."""

    def __init__(
        self,
        name: str,
        value: float | None,
        status: str | None = None,
        status_color: str | None = None,
        description: str | None = None,
    ) -> None:
        """Initialize ratio indicator.

        Args:
            name: Ratio name (Korean).
            value: Ratio value as percentage.
            status: Status text (양호/보통/주의).
            status_color: Status color.
            description: Optional description.
        """
        self.name = name
        self.value = value
        self.status = status
        self.status_color = status_color or "grey"
        self.description = description

        super().__init__(
            content=self._build(),
            padding=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
        )

    def _build(self) -> ft.Control:
        """Build the indicator.

        Returns:
            Indicator layout.
        """
        value_text = f"{self.value:.2f}%" if self.value is not None else "-"

        status_chip = []
        if self.status:
            status_chip = [
                ft.Container(
                    content=ft.Text(
                        self.status,
                        size=10,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500,
                    ),
                    bgcolor=self.status_color,
                    padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                    border_radius=10,
                ),
            ]

        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            self.name,
                            size=13,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            value_text,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                *status_chip,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
