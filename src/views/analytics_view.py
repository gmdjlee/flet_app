"""Analytics View - Financial analysis and chart visualization."""

import flet as ft
from sqlalchemy.orm import Session

from src.components.chart_components import (
    BarChart,
    CAGRDisplay,
    HealthScoreGauge,
    LineChart,
    MetricCard,
)
from src.models.corporation import Corporation
from src.models.database import get_engine, get_session
from src.services.analysis_service import AnalysisService
from src.services.corporation_service import CorporationService
from src.services.financial_service import FinancialService
from src.utils.formatters import format_amount_short


class AnalyticsView(ft.View):
    """Analytics view for financial analysis and visualization.

    Displays charts, CAGR calculations, growth trends, and financial
    health metrics for selected corporations.

    Attributes:
        current_corp_code: Currently selected corporation code.
        selected_corp: Currently selected corporation.
        analysis_type: Current analysis type (revenue, profitability, ratios).
        is_loading: Loading state flag.
    """

    def __init__(
        self,
        page: ft.Page,
        session: Session | None = None,
    ) -> None:
        """Initialize AnalyticsView.

        Args:
            page: Flet page instance.
            session: Database session (optional).
        """
        self._page_ref = page
        self._session = session

        # Data
        self.current_corp_code: str = ""
        self.selected_corp: Corporation | None = None
        self.corporations: list[Corporation] = []
        self.available_years: list[str] = []

        # State
        self.is_loading = False
        self.analysis_type = "revenue"
        self.year_range: tuple[str, str] = ("", "")

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(
            width=30,
            height=30,
            stroke_width=3,
            visible=False,
        )

        # Corporation selector
        self.corp_dropdown = ft.Dropdown(
            label="기업 선택",
            width=300,
            on_select=self._on_corporation_change,
        )
        self.corporation_selector = self.corp_dropdown

        # Analysis type selector - using Dropdown instead of SegmentedButton for Flet 0.70+ compatibility
        self.chart_type_selector = ft.Dropdown(
            label="분석 유형",
            value="revenue",
            width=200,
            options=[
                ft.dropdown.Option(key="revenue", text="매출/이익"),
                ft.dropdown.Option(key="profitability", text="수익성"),
                ft.dropdown.Option(key="ratios", text="재무비율"),
                ft.dropdown.Option(key="growth", text="성장률"),
            ],
            on_select=self._on_analysis_type_change,
        )
        self.analysis_type_selector = self.chart_type_selector

        # Chart containers
        self.chart_container = ft.Container(expand=True)
        self.charts = self.chart_container
        self.trend_chart = None
        self.growth_chart = None
        self.ratio_chart = None

        # Summary cards row
        self.summary_cards = ft.ResponsiveRow(spacing=10, run_spacing=10)
        self.metrics_row = self.summary_cards

        # CAGR display
        self.cagr_display = ft.ResponsiveRow(spacing=10, run_spacing=10)

        # Empty state
        self.empty_state = self._build_empty_state()

        # Build view
        super().__init__(
            route="/analytics",
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

    def _build(self) -> ft.Control:
        """Build the analytics view.

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
                            self.corp_dropdown,
                            ft.Container(width=20),
                            self.chart_type_selector,
                            ft.Container(expand=True),
                            self.loading_indicator,
                        ],
                        wrap=True,
                        spacing=10,
                    ),
                    ft.Container(height=20),
                    # Main content
                    self.chart_container,
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True,
        )

    def _build_header(self) -> ft.Control:
        """Build header section.

        Returns:
            Header row.
        """
        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.ANALYTICS, size=28, color=ft.Colors.BLUE),
                ft.Container(width=10),
                ft.Column(
                    controls=[
                        ft.Text(
                            "재무 분석",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "차트 및 성장률 분석",
                            size=14,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                    spacing=2,
                ),
            ],
        )

    def _build_empty_state(self) -> ft.Control:
        """Build empty state content.

        Returns:
            Empty state container.
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.INSERT_CHART_OUTLINED,
                        size=64,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Text(
                        "기업을 선택하세요",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        "상단 드롭다운에서 분석할 기업을 선택하면 차트가 표시됩니다",
                        size=14,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
            padding=50,
        )

    def show_empty_state(self) -> None:
        """Show empty state."""
        self.chart_container.content = self.empty_state
        if self._page_ref:
            try:
                self._page_ref.update()
            except Exception:
                pass

    def _load_corporations(self) -> None:
        """Load corporations for dropdown."""
        try:
            corp_service = CorporationService(self.session)
            self.corporations = corp_service.list_all(page_size=500)

            self.corp_dropdown.options = [
                ft.dropdown.Option(
                    key=corp.corp_code,
                    text=f"{corp.corp_name} ({corp.stock_code or '-'})",
                )
                for corp in self.corporations
            ]

        except Exception as e:
            print(f"Error loading corporations: {e}")

    def load_corporation_data(self, corp_code: str) -> None:
        """Load data for selected corporation.

        Args:
            corp_code: DART corporation code.
        """
        self.current_corp_code = corp_code
        self._set_loading(True)

        try:
            # Load corporation
            corp_service = CorporationService(self.session)
            self.selected_corp = corp_service.get_by_corp_code(corp_code)

            if not self.selected_corp:
                self.show_empty_state()
                return

            # Load available years
            fin_service = FinancialService(self.session)
            self.available_years = fin_service.get_available_years(corp_code)

            if not self.available_years:
                self.chart_container.content = self._build_no_data_state()
                return

            # Set year range
            self.year_range = (
                min(self.available_years),
                max(self.available_years),
            )

            # Update charts
            self._update_charts()

        except Exception as e:
            print(f"Error loading corporation data: {e}")
            self.chart_container.content = self._build_error_state(str(e))

        finally:
            self._set_loading(False)

    def _update_charts(self) -> None:
        """Update chart display based on current analysis type."""
        if not self.current_corp_code or not self.available_years:
            self.show_empty_state()
            return

        analysis_service = AnalysisService(self.session)

        if self.analysis_type == "revenue":
            self._build_revenue_charts(analysis_service)
        elif self.analysis_type == "profitability":
            self._build_profitability_charts(analysis_service)
        elif self.analysis_type == "ratios":
            self._build_ratios_charts(analysis_service)
        elif self.analysis_type == "growth":
            self._build_growth_charts(analysis_service)

        if self._page_ref:
            try:
                self._page_ref.update()
            except Exception:
                pass

    def _build_revenue_charts(self, analysis_service: AnalysisService) -> None:
        """Build revenue and profit charts."""
        chart_data = analysis_service.get_chart_data(
            self.current_corp_code,
            "revenue",
        )

        # Prepare data series for line chart
        data_series = []
        for dataset in chart_data["datasets"]:
            data_points = []
            for label, value in zip(chart_data["labels"], dataset["data"], strict=False):
                if value is not None:
                    # Convert to 조 단위 for display
                    value_cho = value / 1_000_000_000_000
                    data_points.append({"x": label, "y": value_cho})

            if data_points:
                data_series.append(
                    {
                        "name": dataset["name"],
                        "data": data_points,
                        "color": dataset.get("color"),
                    }
                )

        trend_chart = LineChart(
            data_series=data_series,
            title="매출액 / 영업이익 / 당기순이익 추이 (단위: 조원)",
            show_tooltip=True,
            animate=True,
            show_legend=True,
            height=350,
        )
        self.trend_chart = trend_chart

        # Build summary cards
        latest_year = max(self.available_years)

        fin_service = FinancialService(self.session)
        fin_summary = fin_service.get_financial_summary(
            self.current_corp_code,
            latest_year,
        )

        # Calculate CAGRs
        cagrs = self._calculate_cagrs(analysis_service)

        # Build content
        self.chart_container.content = ft.Column(
            controls=[
                # Summary cards
                self._build_summary_row(fin_summary, fin_service, latest_year),
                ft.Container(height=20),
                # CAGR display
                self._build_cagr_row(cagrs),
                ft.Container(height=20),
                # Chart
                trend_chart,
            ],
            spacing=10,
        )

    def _build_profitability_charts(self, analysis_service: AnalysisService) -> None:
        """Build profitability margin charts."""
        chart_data = analysis_service.get_chart_data(
            self.current_corp_code,
            "profitability",
        )

        # Prepare data series
        data_series = []
        for dataset in chart_data["datasets"]:
            data_points = []
            for label, value in zip(chart_data["labels"], dataset["data"], strict=False):
                if value is not None:
                    data_points.append({"x": label, "y": value})

            if data_points:
                data_series.append(
                    {
                        "name": dataset["name"],
                        "data": data_points,
                        "color": dataset.get("color"),
                    }
                )

        profitability_chart = LineChart(
            data_series=data_series,
            title="수익성 지표 추이 (%)",
            show_tooltip=True,
            animate=True,
            show_legend=True,
            height=350,
        )

        # Also create bar chart for comparison
        bar_chart = BarChart(
            labels=chart_data["labels"],
            datasets=[
                {
                    "name": ds["name"],
                    "values": [v or 0 for v in ds["data"]],
                    "color": ds.get("color"),
                }
                for ds in chart_data["datasets"]
            ],
            title="연도별 수익성 비교 (%)",
            height=300,
        )

        self.chart_container.content = ft.Column(
            controls=[
                profitability_chart,
                ft.Container(height=30),
                bar_chart,
            ],
            spacing=10,
        )

    def _build_ratios_charts(self, analysis_service: AnalysisService) -> None:
        """Build financial ratios charts."""
        chart_data = analysis_service.get_chart_data(
            self.current_corp_code,
            "ratios",
        )

        # Prepare data series
        data_series = []
        for dataset in chart_data["datasets"]:
            data_points = []
            for label, value in zip(chart_data["labels"], dataset["data"], strict=False):
                if value is not None:
                    data_points.append({"x": label, "y": value})

            if data_points:
                data_series.append(
                    {
                        "name": dataset["name"],
                        "data": data_points,
                        "color": dataset.get("color"),
                    }
                )

        ratios_chart = LineChart(
            data_series=data_series,
            title="재무비율 추이 (%)",
            show_tooltip=True,
            animate=True,
            show_legend=True,
            height=350,
        )
        self.ratio_chart = ratios_chart

        # Health score
        latest_year = max(self.available_years)
        health_data = analysis_service.get_financial_health_score(
            self.current_corp_code,
            latest_year,
        )

        health_gauge = HealthScoreGauge(
            score=health_data["overall"],
            grade=health_data.get("grade", ""),
            label=f"재무 건전성 ({latest_year})",
        )

        # Component scores
        component_cards = []
        for _, comp in health_data.get("components", {}).items():
            component_cards.append(
                ft.Container(
                    content=MetricCard(
                        title=comp["label"],
                        value=f"{comp['value']:.1f}%",
                        subtitle=f"점수: {comp['score']:.0f}점",
                    ),
                    col={"xs": 6, "sm": 4, "md": 3},
                )
            )

        self.chart_container.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        health_gauge,
                        ft.Container(width=40),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "재무 건전성 종합 평가",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    self._get_health_description(health_data["overall"]),
                                    size=14,
                                    color=ft.Colors.GREY_600,
                                ),
                            ],
                            spacing=8,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(height=20),
                ft.Text("세부 지표", size=14, weight=ft.FontWeight.BOLD),
                ft.ResponsiveRow(
                    controls=component_cards,
                    spacing=10,
                    run_spacing=10,
                ),
                ft.Container(height=30),
                ratios_chart,
            ],
            spacing=10,
        )

    def _build_growth_charts(self, analysis_service: AnalysisService) -> None:
        """Build growth rate charts."""
        chart_data = analysis_service.get_chart_data(
            self.current_corp_code,
            "growth",
        )

        # Prepare data series
        data_series = []
        for dataset in chart_data["datasets"]:
            data_points = []
            for label, value in zip(chart_data["labels"], dataset["data"], strict=False):
                if value is not None:
                    data_points.append({"x": label, "y": value})

            if data_points:
                data_series.append(
                    {
                        "name": dataset["name"],
                        "data": data_points,
                        "color": dataset.get("color"),
                    }
                )

        growth_chart = BarChart(
            labels=chart_data["labels"],
            datasets=[
                {
                    "name": ds["name"],
                    "values": [v or 0 for v in ds["data"]],
                    "color": ds.get("color"),
                }
                for ds in chart_data["datasets"]
            ],
            title="연도별 성장률 비교 (%)",
            height=350,
        )
        self.growth_chart = growth_chart

        # Stability metrics
        stability_cards = []
        for account in ["매출액", "영업이익", "당기순이익"]:
            stability = analysis_service.get_growth_stability(
                self.current_corp_code,
                account,
            )
            if stability:
                stability_cards.append(
                    ft.Container(
                        content=MetricCard(
                            title=f"{account} 성장 안정성",
                            value=f"{stability['mean_growth']:.1f}%",
                            subtitle=f"변동성: {stability['std_growth']:.1f}%",
                            change=stability.get("stability_score"),
                            change_label="안정성 점수",
                        ),
                        col={"xs": 12, "sm": 6, "md": 4},
                    )
                )

        self.chart_container.content = ft.Column(
            controls=[
                ft.Text("성장률 분석", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.ResponsiveRow(
                    controls=stability_cards,
                    spacing=10,
                    run_spacing=10,
                ),
                ft.Container(height=30),
                growth_chart,
            ],
            spacing=10,
        )

    def _build_summary_row(
        self,
        fin_summary: dict | None,
        fin_service: FinancialService,
        latest_year: str,
    ) -> ft.Control:
        """Build summary cards row."""
        if not fin_summary:
            return ft.Container()

        cards = []

        metrics = [
            ("매출액", "revenue", ft.Icons.TRENDING_UP, ft.Colors.BLUE),
            ("영업이익", "operating_income", ft.Icons.MONETIZATION_ON, ft.Colors.GREEN),
            ("당기순이익", "net_income", ft.Icons.ACCOUNT_BALANCE, ft.Colors.PURPLE),
        ]

        for label, key, icon, color in metrics:
            value = fin_summary.get(key)
            yoy = fin_service.calculate_yoy_growth(
                self.current_corp_code,
                latest_year,
                label,
            )

            cards.append(
                ft.Container(
                    content=MetricCard(
                        title=label,
                        value=format_amount_short(value) if value else "-",
                        subtitle=f"{latest_year}년",
                        change=yoy,
                        icon=icon,
                        color=color,
                    ),
                    col={"xs": 12, "sm": 6, "md": 4},
                )
            )

        self.summary_cards.controls = cards
        return self.summary_cards

    def _build_cagr_row(self, cagrs: dict[str, float | None]) -> ft.Control:
        """Build CAGR display row."""
        period = f"{self.year_range[0]}-{self.year_range[1]}"

        cagr_items = [
            ft.Container(
                content=CAGRDisplay(
                    label=f"{label} CAGR",
                    cagr=cagrs.get(key),
                    period=period,
                ),
                col={"xs": 6, "sm": 4, "md": 3},
            )
            for label, key in [
                ("매출액", "revenue"),
                ("영업이익", "operating_income"),
                ("당기순이익", "net_income"),
            ]
        ]

        self.cagr_display.controls = cagr_items
        return self.cagr_display

    def _calculate_cagrs(self, analysis_service: AnalysisService) -> dict[str, float | None]:
        """Calculate CAGRs for key metrics."""
        if len(self.available_years) < 2:
            return {}

        start_year = min(self.available_years)
        end_year = max(self.available_years)

        return {
            "revenue": analysis_service.calculate_cagr(
                self.current_corp_code, "매출액", start_year, end_year
            ),
            "operating_income": analysis_service.calculate_cagr(
                self.current_corp_code, "영업이익", start_year, end_year
            ),
            "net_income": analysis_service.calculate_cagr(
                self.current_corp_code, "당기순이익", start_year, end_year
            ),
        }

    def get_cagr_data(self) -> dict[str, float | None]:
        """Get CAGR data for current corporation."""
        if not self.current_corp_code or not self.available_years:
            return {}
        analysis_service = AnalysisService(self.session)
        return self._calculate_cagrs(analysis_service)

    def get_ratio_chart_data(self) -> dict | None:
        """Get ratio chart data."""
        if not self.current_corp_code:
            return None
        analysis_service = AnalysisService(self.session)
        return analysis_service.get_chart_data(self.current_corp_code, "ratios")

    def _get_health_description(self, score: float) -> str:
        """Get description for health score."""
        if score >= 80:
            return "재무 상태가 매우 양호합니다. 안정적인 수익성과 건전한 자본 구조를 유지하고 있습니다."
        elif score >= 60:
            return "재무 상태가 양호합니다. 일부 지표에서 개선의 여지가 있습니다."
        elif score >= 40:
            return "재무 상태가 보통입니다. 수익성 또는 안정성 개선이 필요할 수 있습니다."
        else:
            return "재무 상태에 주의가 필요합니다. 주요 재무 지표 개선이 권장됩니다."

    def _build_no_data_state(self) -> ft.Control:
        """Build no data state."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.FOLDER_OFF_OUTLINED,
                        size=64,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Text(
                        "재무 데이터가 없습니다",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        "설정에서 DART API를 통해 데이터를 동기화하세요",
                        size=14,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
            padding=50,
        )

    def _build_error_state(self, error_msg: str) -> ft.Control:
        """Build error state."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        size=64,
                        color=ft.Colors.RED_400,
                    ),
                    ft.Text(
                        "오류가 발생했습니다",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_600,
                    ),
                    ft.Text(
                        error_msg,
                        size=14,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
            padding=50,
        )

    def _set_loading(self, is_loading: bool) -> None:
        """Set loading state."""
        self.is_loading = is_loading
        self.loading_indicator.visible = is_loading
        try:
            self.loading_indicator.update()
        except Exception:
            pass

    def show_loading(self, show: bool = True) -> None:
        """Show or hide loading indicator."""
        self._set_loading(show)

    def _on_corporation_change(self, e: ft.ControlEvent) -> None:
        """Handle corporation selection change."""
        corp_code = e.control.value
        if corp_code:
            self.load_corporation_data(corp_code)

    def _on_analysis_type_change(self, e: ft.ControlEvent) -> None:
        """Handle analysis type change."""
        selected = e.control.value
        if selected:
            self.analysis_type = selected
            self.change_analysis_type(self.analysis_type)

    def set_chart_type(self, chart_type: str) -> None:
        """Set chart type and update display."""
        self.analysis_type = chart_type
        self._update_charts()

    def change_analysis_type(self, analysis_type: str) -> None:
        """Change analysis type and update display."""
        self.analysis_type = analysis_type
        if self.current_corp_code:
            self._update_charts()

    def set_year_range(self, start_year: str, end_year: str) -> None:
        """Set year range for analysis."""
        self.year_range = (start_year, end_year)
        self._update_charts()

    def show_profitability_chart(self) -> None:
        """Show profitability chart."""
        self.set_chart_type("profitability")

    def update_chart(self) -> None:
        """Update current chart."""
        self._update_charts()
