"""Compare View - Corporation comparison functionality."""

from datetime import datetime
from typing import Any

import flet as ft
from sqlalchemy.orm import Session

from src.components.chart_components import BarChart, HealthScoreGauge
from src.models.corporation import Corporation
from src.models.database import get_engine, get_session
from src.services.compare_service import CompareService
from src.services.corporation_service import CorporationService
from src.utils.formatters import format_amount_short
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CompareView(ft.View):
    """Compare view for comparing multiple corporations.

    Allows selection of up to 5 corporations and displays
    comparison tables and charts.

    Attributes:
        selected_corporations: List of selected corporation codes.
        selected_year: Selected year for comparison.
        current_chart_type: Current chart type displayed.
    """

    def __init__(
        self,
        page: ft.Page,
        session: Session | None = None,
    ) -> None:
        """Initialize CompareView.

        Args:
            page: Flet page instance.
            session: Database session (optional).
        """
        self._page_ref = page
        self._session = session

        # State
        self.selected_corporations: list[str] = []
        self.selected_year = str(datetime.now().year - 1)
        self.current_chart_type = "revenue"
        self.is_loading = False

        # Services
        self._compare_service: CompareService | None = None
        self._corp_service: CorporationService | None = None

        # Corporations list
        self.corporations: list[Corporation] = []

        # UI Components
        self.search_bar = self._build_search_bar()
        self.selected_chips_row = ft.Row(wrap=True, spacing=8)
        self.comparison_table = ft.Container()
        self.chart_section = ft.Container()
        self.chart_type_selector = self._build_chart_type_selector()
        self.metric_selector = self._build_metric_selector()
        self.year_selector = self._build_year_selector()

        # Action buttons
        self.save_button = ft.IconButton(
            icon=ft.Icons.SAVE,
            tooltip="비교 세트 저장",
            on_click=self._on_save_click,
        )
        self.load_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="비교 세트 불러오기",
            on_click=self._on_load_click,
        )
        self.export_button = ft.IconButton(
            icon=ft.Icons.DOWNLOAD,
            tooltip="Excel로 내보내기",
            on_click=self._on_export_click,
        )

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(width=30, height=30, stroke_width=3, visible=False)

        # Build view
        super().__init__(
            route="/compare",
            controls=[self._build()],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        # Load corporations
        self._load_corporations()

    @property
    def session(self) -> Session:
        """Get or create database session."""
        if self._session is None:
            engine = get_engine()
            self._session = get_session(engine)
        return self._session

    @property
    def compare_service(self) -> CompareService:
        """Get CompareService instance."""
        if self._compare_service is None:
            self._compare_service = CompareService(self.session)
        return self._compare_service

    @property
    def corp_service(self) -> CorporationService:
        """Get CorporationService instance."""
        if self._corp_service is None:
            self._corp_service = CorporationService(self.session)
        return self._corp_service

    def _build(self) -> ft.Control:
        """Build the compare view.

        Returns:
            Main container with all content.
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    self._build_header(),
                    ft.Divider(),
                    # Controls row
                    ft.Row(
                        controls=[
                            self.search_bar,
                            ft.Container(width=10),
                            self.year_selector,
                            ft.Container(expand=True),
                            self.save_button,
                            self.load_button,
                            self.export_button,
                            self.loading_indicator,
                        ],
                        wrap=True,
                        spacing=10,
                    ),
                    ft.Container(height=10),
                    # Selected corporations chips
                    self.selected_chips_row,
                    ft.Container(height=20),
                    # Comparison table
                    ft.Text("비교 테이블", size=16, weight=ft.FontWeight.BOLD),
                    self.comparison_table,
                    ft.Container(height=30),
                    # Chart section
                    ft.Row(
                        controls=[
                            ft.Text("비교 차트", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            self.chart_type_selector,
                        ],
                    ),
                    self.chart_section,
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True,
        )

    def _build_header(self) -> ft.Control:
        """Build header section."""
        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.COMPARE_ARROWS, size=28, color=ft.Colors.BLUE),
                ft.Container(width=10),
                ft.Column(
                    controls=[
                        ft.Text(
                            "기업 비교",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "최대 5개 기업을 선택하여 재무 지표를 비교합니다",
                            size=14,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                    spacing=2,
                ),
            ],
        )

    def _build_search_bar(self) -> ft.Control:
        """Build corporation search bar."""
        return ft.Dropdown(
            label="기업 추가",
            hint_text="비교할 기업 선택",
            width=300,
            on_change=self._on_corp_selected,
        )

    def _build_chart_type_selector(self) -> ft.Control:
        """Build chart type selector."""
        return ft.Dropdown(
            label="차트 유형",
            value="revenue",
            width=150,
            options=[
                ft.dropdown.Option(key="revenue", text="매출액"),
                ft.dropdown.Option(key="operating_income", text="영업이익"),
                ft.dropdown.Option(key="net_income", text="순이익"),
                ft.dropdown.Option(key="profitability", text="수익성"),
                ft.dropdown.Option(key="ratios", text="재무비율"),
            ],
            on_change=self._on_chart_type_change,
        )

    def _build_metric_selector(self) -> ft.Control:
        """Build metric selector dropdown."""
        return ft.Dropdown(
            label="지표",
            value="revenue",
            width=150,
            options=[
                ft.dropdown.Option(key="revenue", text="매출액"),
                ft.dropdown.Option(key="operating_income", text="영업이익"),
                ft.dropdown.Option(key="net_income", text="순이익"),
                ft.dropdown.Option(key="total_assets", text="총자산"),
                ft.dropdown.Option(key="debt_ratio", text="부채비율"),
                ft.dropdown.Option(key="roe", text="ROE"),
                ft.dropdown.Option(key="operating_margin", text="영업이익률"),
            ],
            on_change=self._on_metric_change,
        )

    def _build_year_selector(self) -> ft.Control:
        """Build year selector dropdown."""
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 1, current_year - 6, -1)]

        return ft.Dropdown(
            label="연도",
            value=self.selected_year,
            width=120,
            options=[ft.dropdown.Option(key=y, text=y) for y in years],
            on_change=self._on_year_change,
        )

    def _load_corporations(self) -> None:
        """Load corporations for dropdown."""
        try:
            self.corporations = self.corp_service.list_all(page_size=500)

            self.search_bar.options = [
                ft.dropdown.Option(
                    key=corp.corp_code,
                    text=f"{corp.corp_name} ({corp.stock_code or '-'})",
                )
                for corp in self.corporations
            ]

        except Exception as e:
            print(f"Error loading corporations: {e}")

    def add_corporation(self, corp_code: str) -> bool:
        """Add a corporation to comparison.

        Args:
            corp_code: Corporation code to add.

        Returns:
            True if added successfully.
        """
        result = self.compare_service.add_corporation(corp_code)
        if result:
            self.selected_corporations = self.compare_service.get_selected_corporations()
            self._update_selected_chips()
            self._update_comparison_table()
            self._update_chart()
        return result

    def remove_corporation(self, corp_code: str) -> bool:
        """Remove a corporation from comparison.

        Args:
            corp_code: Corporation code to remove.

        Returns:
            True if removed successfully.
        """
        result = self.compare_service.remove_corporation(corp_code)
        if result:
            self.selected_corporations = self.compare_service.get_selected_corporations()
            self._update_selected_chips()
            self._update_comparison_table()
            self._update_chart()
        return result

    def clear_corporations(self) -> None:
        """Clear all selected corporations."""
        self.compare_service.clear_corporations()
        self.selected_corporations = []
        self._update_selected_chips()
        self._update_comparison_table()
        self._update_chart()

    def can_remove_corporation(self, corp_code: str) -> bool:
        """Check if corporation can be removed.

        Args:
            corp_code: Corporation code to check.

        Returns:
            True if can be removed.
        """
        return corp_code in self.selected_corporations

    def get_selected_chips(self) -> list[ft.Control]:
        """Get selected corporation chips.

        Returns:
            List of chip controls.
        """
        chips = []
        details = self.compare_service.get_corporation_details()

        for detail in details:
            chip = ft.Chip(
                label=ft.Text(detail["corp_name"]),
                delete_icon=ft.Icons.CLOSE,
                on_delete=lambda e, code=detail["corp_code"]: self._on_chip_delete(code),
            )
            chips.append(chip)

        return chips

    def _update_selected_chips(self) -> None:
        """Update selected corporations chip display."""
        chips = self.get_selected_chips()

        # Add clear all button if there are chips
        if chips:
            chips.append(
                ft.TextButton(
                    "모두 지우기",
                    on_click=lambda _: self.clear_corporations(),
                )
            )

        self.selected_chips_row.controls = chips

        try:
            self.selected_chips_row.update()
        except Exception:
            pass

    def build_comparison_table(self) -> ft.Control:
        """Build comparison table.

        Returns:
            Comparison table control.
        """
        if not self.selected_corporations:
            return self._build_empty_table()

        table_data = self.compare_service.get_comparison_table_data(self.selected_year)

        if not table_data:
            return self._build_empty_table()

        # Build columns
        columns = [
            ft.DataColumn(ft.Text("기업명", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("매출액", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("영업이익", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("자산총계", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("부채비율", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("ROE", weight=ft.FontWeight.BOLD)),
        ]

        # Build rows
        rows = []
        for data in table_data:
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(data.get("corp_name", "-"), weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(format_amount_short(data.get("revenue")))),
                    ft.DataCell(ft.Text(format_amount_short(data.get("operating_income")))),
                    ft.DataCell(ft.Text(format_amount_short(data.get("total_assets")))),
                    ft.DataCell(
                        ft.Text(
                            f"{data.get('debt_ratio', 0):.1f}%" if data.get("debt_ratio") else "-"
                        )
                    ),
                    ft.DataCell(ft.Text(f"{data.get('roe', 0):.1f}%" if data.get("roe") else "-")),
                ]
            )
            rows.append(row)

        return ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            column_spacing=30,
            heading_row_height=50,
            data_row_min_height=45,
        )

    def _build_empty_table(self) -> ft.Control:
        """Build empty table state."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.TABLE_CHART_OUTLINED,
                        size=48,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Text(
                        "기업을 선택하세요",
                        size=14,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        "상단에서 비교할 기업을 추가하면 비교 테이블이 표시됩니다",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.alignment.center,
            padding=40,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )

    def _update_comparison_table(self) -> None:
        """Update comparison table display."""
        self.comparison_table.content = self.build_comparison_table()
        try:
            self.comparison_table.update()
        except Exception:
            pass

    def get_table_columns(self) -> list[str]:
        """Get table column names.

        Returns:
            List of column names.
        """
        return ["기업명", "매출액", "영업이익", "자산총계", "부채비율", "ROE"]

    def get_table_rows(self) -> list[dict[str, Any]]:
        """Get table row data.

        Returns:
            List of row data dictionaries.
        """
        return self.compare_service.get_comparison_table_data(self.selected_year)

    def build_comparison_chart(self) -> ft.Control:
        """Build comparison chart.

        Returns:
            Chart control.
        """
        if not self.selected_corporations:
            return self._build_empty_chart()

        if self.current_chart_type == "profitability":
            return self._build_profitability_chart()
        elif self.current_chart_type == "ratios":
            return self._build_ratios_chart()
        else:
            return self._build_metric_chart(self.current_chart_type)

    def _build_metric_chart(self, metric: str) -> ft.Control:
        """Build single metric comparison chart."""
        chart_data = self.compare_service.get_comparison_chart_data(metric, self.selected_year)

        metric_names = {
            "revenue": "매출액",
            "operating_income": "영업이익",
            "net_income": "순이익",
            "total_assets": "총자산",
        }

        # Prepare data for bar chart
        data_points = []
        for label, value in zip(chart_data["labels"], chart_data["values"], strict=False):
            if value is not None:
                # Convert to appropriate unit
                if metric in ["revenue", "operating_income", "net_income", "total_assets"]:
                    value_display = value / 1_000_000_000_000  # 조 단위
                else:
                    value_display = value
                data_points.append({"label": label, "value": value_display})

        chart = BarChart(
            data_points=data_points,
            title=f"{metric_names.get(metric, metric)} 비교 ({self.selected_year}년, 단위: 조원)",
            height=350,
        )

        # Add ranking display
        ranking = self.get_ranking_for_metric(metric)
        ranking_text = " > ".join([f"{r['rank']}. {r['corp_name']}" for r in ranking[:5]])

        return ft.Column(
            controls=[
                chart,
                ft.Container(height=10),
                ft.Text(f"순위: {ranking_text}", size=12, color=ft.Colors.GREY_600),
            ],
            spacing=10,
        )

    def _build_profitability_chart(self) -> ft.Control:
        """Build profitability comparison chart."""
        ratio_data = self.compare_service.get_ratio_comparison(
            ["operating_margin", "net_margin"], self.selected_year
        )

        labels = ratio_data["operating_margin"]["labels"]
        datasets = [
            {
                "name": "영업이익률",
                "values": [v or 0 for v in ratio_data["operating_margin"]["values"]],
                "color": "#1f77b4",
            },
            {
                "name": "순이익률",
                "values": [v or 0 for v in ratio_data["net_margin"]["values"]],
                "color": "#ff7f0e",
            },
        ]

        chart = BarChart(
            labels=labels,
            datasets=datasets,
            title=f"수익성 비교 ({self.selected_year}년, %)",
            height=350,
        )

        return chart

    def _build_ratios_chart(self) -> ft.Control:
        """Build financial ratios comparison chart."""
        ratio_data = self.compare_service.get_ratio_comparison(
            ["debt_ratio", "roe", "roa"], self.selected_year
        )

        labels = ratio_data["debt_ratio"]["labels"]
        datasets = [
            {
                "name": "부채비율",
                "values": [v or 0 for v in ratio_data["debt_ratio"]["values"]],
                "color": "#d62728",
            },
            {
                "name": "ROE",
                "values": [v or 0 for v in ratio_data["roe"]["values"]],
                "color": "#2ca02c",
            },
            {
                "name": "ROA",
                "values": [v or 0 for v in ratio_data["roa"]["values"]],
                "color": "#9467bd",
            },
        ]

        chart = BarChart(
            labels=labels,
            datasets=datasets,
            title=f"재무비율 비교 ({self.selected_year}년, %)",
            height=350,
        )

        # Add health score comparison
        health_scores = self.compare_service.get_health_score_comparison(self.selected_year)

        health_cards = []
        for score in health_scores:
            health_cards.append(
                ft.Container(
                    content=HealthScoreGauge(
                        score=score["overall_score"],
                        grade=score["grade"],
                        label=score["corp_name"],
                    ),
                    col={"xs": 6, "sm": 4, "md": 3},
                )
            )

        return ft.Column(
            controls=[
                chart,
                ft.Container(height=20),
                ft.Text("재무 건전성 비교", size=14, weight=ft.FontWeight.BOLD),
                ft.ResponsiveRow(controls=health_cards, spacing=10, run_spacing=10),
            ],
            spacing=10,
        )

    def _build_empty_chart(self) -> ft.Control:
        """Build empty chart state."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.BAR_CHART_OUTLINED,
                        size=48,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Text(
                        "비교 차트",
                        size=14,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        "2개 이상의 기업을 선택하면 비교 차트가 표시됩니다",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.alignment.center,
            padding=40,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )

    def _update_chart(self) -> None:
        """Update chart display."""
        self.chart_section.content = self.build_comparison_chart()
        try:
            self.chart_section.update()
        except Exception:
            pass

    def get_available_metrics(self) -> list[str]:
        """Get list of available metrics.

        Returns:
            List of metric keys.
        """
        return [
            "revenue",
            "operating_income",
            "net_income",
            "total_assets",
            "debt_ratio",
            "roe",
            "operating_margin",
        ]

    def get_ranking_for_metric(self, metric: str) -> list[dict[str, Any]]:
        """Get ranking for a metric.

        Args:
            metric: Metric to rank by.

        Returns:
            List of ranked corporations.
        """
        ascending = metric == "debt_ratio"  # Lower is better for debt ratio
        return self.compare_service.rank_by_metric(metric, self.selected_year, ascending=ascending)

    def get_export_options(self) -> list[str]:
        """Get available export options.

        Returns:
            List of export format keys.
        """
        return ["excel", "csv"]

    def get_layout_mode(self) -> str:
        """Get current layout mode based on screen width.

        Returns:
            'wide' or 'narrow'.
        """
        if self._page_ref and hasattr(self._page_ref, "width"):
            return "wide" if self._page_ref.width >= 900 else "narrow"
        return "wide"

    def set_year(self, year: str) -> None:
        """Set selected year.

        Args:
            year: Year to set.
        """
        self.selected_year = year
        self._update_comparison_table()
        self._update_chart()

    def set_chart_type(self, chart_type: str) -> None:
        """Set chart type.

        Args:
            chart_type: Chart type to set.
        """
        self.current_chart_type = chart_type
        self._update_chart()

    def save_comparison(self, name: str) -> bool:
        """Save current comparison set.

        Args:
            name: Name for the set.

        Returns:
            True if saved successfully.
        """
        return self.compare_service.save_comparison_set(name)

    def load_comparison(self, name: str) -> bool:
        """Load a saved comparison set.

        Args:
            name: Name of the set to load.

        Returns:
            True if loaded successfully.
        """
        result = self.compare_service.load_comparison_set(name)
        if result:
            self.selected_corporations = self.compare_service.get_selected_corporations()
            self._update_selected_chips()
            self._update_comparison_table()
            self._update_chart()
        return result

    # Event handlers
    def _on_corp_selected(self, e: ft.ControlEvent) -> None:
        """Handle corporation selection."""
        corp_code = e.control.value
        if corp_code:
            self.add_corporation(corp_code)
            e.control.value = None  # Reset dropdown
            try:
                e.control.update()
            except Exception:
                pass

    def _on_chip_delete(self, corp_code: str) -> None:
        """Handle chip delete."""
        self.remove_corporation(corp_code)

    def _on_year_change(self, e: ft.ControlEvent) -> None:
        """Handle year change."""
        year = e.control.value
        if year:
            self.set_year(year)

    def _on_chart_type_change(self, e: ft.ControlEvent) -> None:
        """Handle chart type change."""
        chart_type = e.control.value
        if chart_type:
            self.set_chart_type(chart_type)

    def _on_metric_change(self, e: ft.ControlEvent) -> None:
        """Handle metric change."""
        metric = e.control.value
        if metric:
            self.current_chart_type = metric
            self._update_chart()

    def _on_save_click(self, e: ft.ControlEvent) -> None:
        """Handle save button click."""
        if not self.selected_corporations:
            return

        # Show save dialog
        def save_set(e):
            name = name_field.value
            if name:
                self.save_comparison(name)
                dialog.open = False
                self._page_ref.update()

        name_field = ft.TextField(label="세트 이름", autofocus=True)
        dialog = ft.AlertDialog(
            title=ft.Text("비교 세트 저장"),
            content=name_field,
            actions=[
                ft.TextButton("취소", on_click=lambda e: self._close_dialog(dialog)),
                ft.TextButton("저장", on_click=save_set),
            ],
        )

        self._page_ref.overlay.append(dialog)
        dialog.open = True
        self._page_ref.update()

    def _on_load_click(self, e: ft.ControlEvent) -> None:
        """Handle load button click."""
        saved_sets = self.compare_service.get_saved_comparison_sets()

        if not saved_sets:
            # Show message
            self._show_snackbar("저장된 세트가 없습니다")
            return

        # Show load dialog
        set_list = ft.ListView(
            controls=[
                ft.ListTile(
                    title=ft.Text(name),
                    on_click=lambda e, n=name: self._load_and_close(n, dialog),
                )
                for name in saved_sets
            ],
            height=200,
        )

        dialog = ft.AlertDialog(
            title=ft.Text("비교 세트 불러오기"),
            content=set_list,
            actions=[
                ft.TextButton("취소", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )

        self._page_ref.overlay.append(dialog)
        dialog.open = True
        self._page_ref.update()

    def _load_and_close(self, name: str, dialog: ft.AlertDialog) -> None:
        """Load set and close dialog."""
        self.load_comparison(name)
        dialog.open = False
        self._page_ref.update()

    def _close_dialog(self, dialog: ft.AlertDialog) -> None:
        """Close dialog."""
        dialog.open = False
        self._page_ref.update()

    def _on_export_click(self, e: ft.ControlEvent) -> None:
        """Handle export button click."""
        if not self.selected_corporations:
            self._show_snackbar("내보낼 데이터가 없습니다")
            return

        # Export functionality - simplified for now
        self._show_snackbar("Excel 내보내기 기능 준비 중")

    def _show_snackbar(self, message: str) -> None:
        """Show snackbar message."""
        if self._page_ref:
            self._page_ref.snack_bar = ft.SnackBar(content=ft.Text(message))
            self._page_ref.snack_bar.open = True
            self._page_ref.update()
