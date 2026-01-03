"""Chart components for financial data visualization.

Note: Flet 0.80+ does not include built-in chart components.
These are simplified text-based visualizations as placeholders.
For full chart support, consider using matplotlib or plotly with file export.
"""

from typing import Any

import flet as ft

# Default chart colors
CHART_COLORS = [
    "#1f77b4",  # Blue
    "#ff7f0e",  # Orange
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#8c564b",  # Brown
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
]


class LineChart:
    """Line chart component for trend visualization.

    Uses text-based representation since Flet 0.80+ doesn't include charts.
    """

    def __init__(
        self,
        data_points: list[dict[str, Any]] | None = None,
        data_series: list[dict[str, Any]] | None = None,
        title: str = "",
        show_tooltip: bool = True,
        animate: bool = True,
        show_legend: bool = True,
        height: int = 300,
        width: int | None = None,
    ) -> None:
        """Initialize line chart."""
        self.data_points = data_points or []
        self.data_series = data_series or []
        self.title = title
        self.show_tooltip = show_tooltip
        self.animate = animate
        self.show_legend = show_legend
        self.height = height
        self.width = width

    def build(self) -> ft.Control:
        """Build the line chart control."""
        controls = []

        if self.title:
            controls.append(
                ft.Text(
                    self.title,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                )
            )

        # Create data table for chart data
        if self.data_series:
            # Get x-axis labels from first series
            x_labels = []
            if self.data_series[0].get("data"):
                x_labels = [str(p.get("x", "")) for p in self.data_series[0]["data"]]

            # Build table columns
            columns = [ft.DataColumn(ft.Text("연도"))]
            for series in self.data_series:
                columns.append(ft.DataColumn(ft.Text(series.get("name", ""))))

            # Build table rows
            rows = []
            for i, label in enumerate(x_labels):
                cells = [ft.DataCell(ft.Text(str(label)))]
                for series in self.data_series:
                    data = series.get("data", [])
                    value = data[i].get("y", 0) if i < len(data) else 0
                    value_str = f"{value:,.0f}" if value else "-"
                    cells.append(ft.DataCell(ft.Text(value_str)))
                rows.append(ft.DataRow(cells=cells))

            controls.append(
                ft.DataTable(
                    columns=columns,
                    rows=rows,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    column_spacing=20,
                )
            )

        elif self.data_points:
            # Single series
            rows = []
            for point in self.data_points:
                x_val = point.get("x", "")
                y_val = point.get("y", 0)
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(x_val))),
                            ft.DataCell(ft.Text(f"{y_val:,.0f}" if y_val else "-")),
                        ]
                    )
                )

            controls.append(
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("기간")),
                        ft.DataColumn(ft.Text("값")),
                    ],
                    rows=rows,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                )
            )

        # Legend
        if self.show_legend and self.data_series:
            legend_items = []
            for i, series in enumerate(self.data_series):
                color = series.get("color", CHART_COLORS[i % len(CHART_COLORS)])
                name = series.get("name", f"Series {i + 1}")
                legend_items.append(
                    ft.Row(
                        [
                            ft.Container(
                                width=12,
                                height=12,
                                bgcolor=color,
                                border_radius=2,
                            ),
                            ft.Text(name, size=12),
                        ],
                        spacing=4,
                    )
                )

            controls.append(
                ft.Row(
                    legend_items,
                    wrap=True,
                    spacing=16,
                )
            )

        return ft.Container(
            content=ft.Column(controls, spacing=8),
            height=self.height if len(controls) > 1 else None,
        )


class BarChart:
    """Bar chart component for comparison visualization.

    Uses text-based representation since Flet 0.80+ doesn't include charts.
    """

    def __init__(
        self,
        data_points: list[dict[str, Any]] | None = None,
        labels: list[str] | None = None,
        datasets: list[dict[str, Any]] | None = None,
        title: str = "",
        show_tooltip: bool = True,
        animate: bool = True,
        horizontal: bool = False,
        height: int = 300,
        width: int | None = None,
    ) -> None:
        """Initialize bar chart."""
        self.data_points = data_points or []
        self.labels = labels or []
        self.datasets = datasets or []
        self.title = title
        self.show_tooltip = show_tooltip
        self.animate = animate
        self.horizontal = horizontal
        self.height = height
        self.width = width

    def build(self) -> ft.Control:
        """Build the bar chart control."""
        controls = []

        if self.title:
            controls.append(
                ft.Text(
                    self.title,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                )
            )

        # Build data table
        if self.datasets and self.labels:
            columns = [ft.DataColumn(ft.Text("항목"))]
            for dataset in self.datasets:
                columns.append(ft.DataColumn(ft.Text(dataset.get("name", ""))))

            rows = []
            for i, label in enumerate(self.labels):
                cells = [ft.DataCell(ft.Text(str(label)))]
                for dataset in self.datasets:
                    values = dataset.get("values", [])
                    value = values[i] if i < len(values) else 0
                    value_str = f"{value:,.1f}" if value else "-"
                    cells.append(ft.DataCell(ft.Text(value_str)))
                rows.append(ft.DataRow(cells=cells))

            controls.append(
                ft.DataTable(
                    columns=columns,
                    rows=rows,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    column_spacing=20,
                )
            )

        elif self.data_points:
            rows = []
            for point in self.data_points:
                label = point.get("label", "")
                value = point.get("value", 0)
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(label))),
                            ft.DataCell(ft.Text(f"{value:,.0f}" if value else "-")),
                        ]
                    )
                )

            controls.append(
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("항목")),
                        ft.DataColumn(ft.Text("값")),
                    ],
                    rows=rows,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                )
            )

        # Legend for grouped charts
        if self.datasets:
            legend_items = []
            for i, dataset in enumerate(self.datasets):
                color = dataset.get("color", CHART_COLORS[i % len(CHART_COLORS)])
                name = dataset.get("name", f"Dataset {i + 1}")
                legend_items.append(
                    ft.Row(
                        [
                            ft.Container(
                                width=12,
                                height=12,
                                bgcolor=color,
                                border_radius=2,
                            ),
                            ft.Text(name, size=12),
                        ],
                        spacing=4,
                    )
                )

            controls.append(
                ft.Row(
                    legend_items,
                    wrap=True,
                    spacing=16,
                )
            )

        return ft.Container(
            content=ft.Column(controls, spacing=8),
            height=self.height if len(controls) > 1 else None,
        )


class MetricCard:
    """Metric display card for KPI visualization."""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        change: float | None = None,
        change_label: str = "전년 대비",
        icon: str | None = None,
        color: str | None = None,
    ) -> None:
        """Initialize metric card."""
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.change = change
        self.change_label = change_label
        self.icon_name = icon
        self.color = color or ft.Colors.BLUE

    def build(self) -> ft.Control:
        """Build the metric card."""
        change_control = None
        if self.change is not None:
            if self.change > 0:
                change_color = ft.Colors.GREEN
                change_icon = ft.Icons.ARROW_UPWARD
                change_text = f"+{self.change:.1f}%"
            elif self.change < 0:
                change_color = ft.Colors.RED
                change_icon = ft.Icons.ARROW_DOWNWARD
                change_text = f"{self.change:.1f}%"
            else:
                change_color = ft.Colors.GREY
                change_icon = ft.Icons.REMOVE
                change_text = "0.0%"

            change_control = ft.Row(
                [
                    ft.Icon(change_icon, size=14, color=change_color),
                    ft.Text(change_text, size=12, color=change_color),
                    ft.Text(self.change_label, size=10, color=ft.Colors.GREY),
                ],
                spacing=4,
            )

        content = [
            ft.Text(self.title, size=12, color=ft.Colors.GREY_700),
            ft.Text(self.value, size=24, weight=ft.FontWeight.BOLD),
        ]

        if self.subtitle:
            content.append(ft.Text(self.subtitle, size=10, color=ft.Colors.GREY_500))

        if change_control:
            content.append(change_control)

        header = None
        if self.icon_name:
            header = ft.Container(
                content=ft.Icon(self.icon_name, size=20, color=self.color),
                bgcolor=ft.Colors.with_opacity(0.1, self.color),
                border_radius=8,
                padding=8,
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([header] if header else [], alignment=ft.MainAxisAlignment.END),
                    ft.Column(content, spacing=4),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            padding=16,
            expand=True,
        )


class CAGRDisplay:
    """CAGR display component with visual indicator."""

    def __init__(
        self,
        label: str,
        cagr: float | None,
        period: str = "",
    ) -> None:
        """Initialize CAGR display."""
        self.label = label
        self.cagr = cagr
        self.period = period

    def build(self) -> ft.Control:
        """Build CAGR display."""
        if self.cagr is None:
            value_text = "-"
            color = ft.Colors.GREY
        elif self.cagr > 0:
            value_text = f"+{self.cagr:.1f}%"
            color = ft.Colors.GREEN
        elif self.cagr < 0:
            value_text = f"{self.cagr:.1f}%"
            color = ft.Colors.RED
        else:
            value_text = "0.0%"
            color = ft.Colors.GREY

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(self.label, size=12, color=ft.Colors.GREY_700),
                    ft.Text(value_text, size=28, weight=ft.FontWeight.BOLD, color=color),
                    (
                        ft.Text(self.period, size=10, color=ft.Colors.GREY_500)
                        if self.period
                        else ft.Container()
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            bgcolor=ft.Colors.with_opacity(0.05, color),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, color)),
            border_radius=8,
            padding=16,
            alignment=ft.alignment.center,
        )


class HealthScoreGauge:
    """Financial health score gauge display."""

    def __init__(
        self,
        score: float,
        grade: str = "",
        label: str = "재무 건전성",
    ) -> None:
        """Initialize health score gauge."""
        self.score = score
        self.grade = grade
        self.label = label

    def build(self) -> ft.Control:
        """Build health score gauge."""
        if self.score >= 80:
            color = ft.Colors.GREEN
        elif self.score >= 60:
            color = ft.Colors.ORANGE
        elif self.score >= 40:
            color = ft.Colors.AMBER
        else:
            color = ft.Colors.RED

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(self.label, size=12, color=ft.Colors.GREY_700),
                    ft.Stack(
                        [
                            ft.Container(
                                content=ft.ProgressRing(
                                    value=self.score / 100,
                                    stroke_width=8,
                                    color=color,
                                    bgcolor=ft.Colors.GREY_200,
                                ),
                                width=100,
                                height=100,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"{self.score:.0f}",
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        (
                                            ft.Text(
                                                self.grade,
                                                size=14,
                                                color=color,
                                                weight=ft.FontWeight.BOLD,
                                            )
                                            if self.grade
                                            else ft.Container()
                                        ),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=0,
                                ),
                                width=100,
                                height=100,
                                alignment=ft.alignment.center,
                            ),
                        ],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=16,
        )
