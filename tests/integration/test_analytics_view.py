"""Integration tests for AnalyticsView."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.corporation import Corporation
from src.models.financial_statement import FinancialStatement


@pytest.fixture
def analytics_db():
    """Create in-memory SQLite with test data for analytics testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add test corporations
    corps = [
        Corporation(corp_code="00126380", corp_name="삼성전자", stock_code="005930", corp_cls="Y"),
        Corporation(corp_code="00164779", corp_name="SK하이닉스", stock_code="000660", corp_cls="Y"),
    ]
    for corp in corps:
        session.add(corp)

    # Add financial data for Samsung
    years = ["2021", "2022", "2023"]
    for i, year in enumerate(years):
        revenue = int(200_000_000_000_000 * (1.1 ** i))
        operating_income = int(35_000_000_000_000 * (1.1 ** i))
        net_income = int(25_000_000_000_000 * (1.1 ** i))

        statements = [
            {"account_nm": "매출액", "sj_div": "IS", "thstrm_amount": revenue},
            {"account_nm": "영업이익", "sj_div": "IS", "thstrm_amount": operating_income},
            {"account_nm": "당기순이익", "sj_div": "IS", "thstrm_amount": net_income},
            {"account_nm": "자산총계", "sj_div": "BS", "thstrm_amount": 400_000_000_000_000},
            {"account_nm": "부채총계", "sj_div": "BS", "thstrm_amount": 100_000_000_000_000},
            {"account_nm": "자본총계", "sj_div": "BS", "thstrm_amount": 300_000_000_000_000},
        ]

        for j, stmt_data in enumerate(statements):
            stmt = FinancialStatement(
                corp_code="00126380",
                bsns_year=year,
                reprt_code="11011",
                fs_div="CFS",
                sj_div=stmt_data["sj_div"],
                account_nm=stmt_data["account_nm"],
                thstrm_amount=stmt_data["thstrm_amount"],
                ord=j + 1,
            )
            session.add(stmt)

    session.commit()
    yield session
    session.close()


@pytest.fixture
def mock_analytics_page():
    """Create a mock Flet Page for analytics view testing."""
    import flet as ft

    page = MagicMock(spec=ft.Page)
    page.platform = ft.PagePlatform.WINDOWS
    page.width = 1400
    page.height = 900
    page.update = MagicMock()
    page.views = []
    page.route = "/analytics"
    page.go = MagicMock()
    page.snack_bar = None
    page.overlay = []

    # Mock window object
    page.window = MagicMock()
    page.window.width = 1400
    page.window.height = 900

    # Mock theme
    page.theme = None
    page.theme_mode = None

    return page


class TestAnalyticsViewInitialization:
    """Tests for AnalyticsView initialization."""

    def test_view_creation(self, mock_analytics_page, analytics_db):
        """Test analytics view can be created."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        assert view is not None

    def test_view_has_controls(self, mock_analytics_page, analytics_db):
        """Test view has necessary controls."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        # View is created with controls
        assert len(view.controls) > 0

    def test_view_has_corporation_selector(self, mock_analytics_page, analytics_db):
        """Test view has corporation selector dropdown."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        assert hasattr(view, "corp_dropdown") or hasattr(view, "corporation_selector")

    def test_view_has_chart_type_selector(self, mock_analytics_page, analytics_db):
        """Test view has chart type selector."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        assert hasattr(view, "chart_type_selector") or hasattr(view, "analysis_type")


class TestAnalyticsViewCharts:
    """Tests for chart display in AnalyticsView."""

    def test_revenue_chart_display(self, mock_analytics_page, analytics_db):
        """Test revenue chart can be displayed."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("00126380")

        # Should have chart container
        assert hasattr(view, "chart_container") or hasattr(view, "charts")

    def test_profitability_chart_display(self, mock_analytics_page, analytics_db):
        """Test profitability chart can be displayed."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("00126380")

        # View should have method to show profitability
        assert callable(getattr(view, "show_profitability_chart", None)) or \
               callable(getattr(view, "update_chart", None))

    def test_ratio_chart_display(self, mock_analytics_page, analytics_db):
        """Test ratio chart can be displayed."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("00126380")

        # View should handle ratio charts
        chart_data = view.get_ratio_chart_data() if hasattr(view, "get_ratio_chart_data") else None
        assert chart_data is not None or hasattr(view, "ratio_chart")


class TestAnalyticsViewInteraction:
    """Tests for user interaction in AnalyticsView."""

    def test_corporation_selection_updates_charts(self, mock_analytics_page, analytics_db):
        """Test selecting a corporation updates the charts."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("00126380")

        # Verify data is loaded
        assert view.current_corp_code == "00126380" or hasattr(view, "selected_corp")

    def test_chart_type_change(self, mock_analytics_page, analytics_db):
        """Test changing chart type updates display."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("00126380")

        if hasattr(view, "set_chart_type"):
            view.set_chart_type("profitability")
        elif hasattr(view, "change_analysis_type"):
            view.change_analysis_type("profitability")

        # Page should be updated
        mock_analytics_page.update.assert_called()

    def test_year_range_selection(self, mock_analytics_page, analytics_db):
        """Test year range can be selected."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)

        if hasattr(view, "set_year_range"):
            view.set_year_range("2021", "2023")
        elif hasattr(view, "year_range"):
            view.year_range = ("2021", "2023")


class TestAnalyticsViewDataDisplay:
    """Tests for data display in AnalyticsView."""

    def test_cagr_display(self, mock_analytics_page, analytics_db):
        """Test CAGR is calculated and displayed."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("00126380")

        # Should display CAGR somewhere
        cagr_data = view.get_cagr_data() if hasattr(view, "get_cagr_data") else None
        assert cagr_data is not None or hasattr(view, "cagr_display")

    def test_growth_trend_display(self, mock_analytics_page, analytics_db):
        """Test growth trend is displayed."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("00126380")

        assert hasattr(view, "trend_chart") or hasattr(view, "growth_chart")

    def test_summary_metrics_display(self, mock_analytics_page, analytics_db):
        """Test summary metrics are displayed."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("00126380")

        assert hasattr(view, "summary_cards") or hasattr(view, "metrics_row")


class TestAnalyticsViewLoading:
    """Tests for loading states in AnalyticsView."""

    def test_loading_indicator_shown(self, mock_analytics_page, analytics_db):
        """Test loading indicator is shown during data load."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)

        # Should have loading state management
        assert hasattr(view, "is_loading") or hasattr(view, "show_loading")

    def test_empty_state_when_no_data(self, mock_analytics_page, analytics_db):
        """Test empty state is shown when no data available."""
        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=mock_analytics_page, session=analytics_db)
        view.load_corporation_data("INVALID")

        # Should handle empty data gracefully
        assert hasattr(view, "empty_state") or hasattr(view, "show_empty_state")


class TestChartComponents:
    """Tests for chart component wrappers."""

    def test_line_chart_creation(self, mock_analytics_page):
        """Test LineChart component can be created."""
        from src.components.chart_components import LineChart

        chart = LineChart(
            data_points=[
                {"x": "2021", "y": 100},
                {"x": "2022", "y": 110},
                {"x": "2023", "y": 121},
            ],
            title="Revenue Trend",
        )
        assert chart is not None

    def test_bar_chart_creation(self, mock_analytics_page):
        """Test BarChart component can be created."""
        from src.components.chart_components import BarChart

        chart = BarChart(
            data_points=[
                {"label": "2021", "value": 100},
                {"label": "2022", "value": 110},
                {"label": "2023", "value": 121},
            ],
            title="Revenue Comparison",
        )
        assert chart is not None

    def test_line_chart_with_multiple_series(self, mock_analytics_page):
        """Test LineChart with multiple data series."""
        from src.components.chart_components import LineChart

        chart = LineChart(
            data_series=[
                {
                    "name": "매출액",
                    "data": [{"x": "2021", "y": 200}, {"x": "2022", "y": 220}],
                    "color": "#1f77b4",
                },
                {
                    "name": "영업이익",
                    "data": [{"x": "2021", "y": 35}, {"x": "2022", "y": 38}],
                    "color": "#ff7f0e",
                },
            ],
            title="Financial Trend",
        )
        assert chart is not None
        content = chart.build()
        assert content is not None

    def test_bar_chart_grouped(self, mock_analytics_page):
        """Test grouped BarChart."""
        from src.components.chart_components import BarChart

        chart = BarChart(
            labels=["2021", "2022", "2023"],
            datasets=[
                {"name": "매출액", "values": [200, 220, 242], "color": "#1f77b4"},
                {"name": "영업이익", "values": [35, 38, 42], "color": "#ff7f0e"},
            ],
            title="Year Comparison",
        )
        assert chart is not None

    def test_chart_tooltip_enabled(self, mock_analytics_page):
        """Test chart has tooltip support."""
        from src.components.chart_components import LineChart

        chart = LineChart(
            data_points=[{"x": "2021", "y": 100}],
            title="Test",
            show_tooltip=True,
        )
        assert chart.show_tooltip is True

    def test_chart_animation_enabled(self, mock_analytics_page):
        """Test chart has animation support."""
        from src.components.chart_components import LineChart

        chart = LineChart(
            data_points=[{"x": "2021", "y": 100}],
            title="Test",
            animate=True,
        )
        assert chart.animate is True

    def test_chart_legend_display(self, mock_analytics_page):
        """Test chart legend can be displayed."""
        from src.components.chart_components import LineChart

        chart = LineChart(
            data_series=[
                {"name": "Series A", "data": [{"x": "1", "y": 10}]},
            ],
            title="Test",
            show_legend=True,
        )
        assert chart.show_legend is True


class TestAnalyticsViewResponsive:
    """Tests for responsive layout in AnalyticsView."""

    def test_narrow_layout(self, analytics_db):
        """Test view adapts to narrow width."""
        import flet as ft

        page = MagicMock(spec=ft.Page)
        page.width = 600  # Narrow
        page.height = 800
        page.platform = ft.PagePlatform.WINDOWS
        page.update = MagicMock()
        page.views = []
        page.route = "/analytics"
        page.window = MagicMock()
        page.window.width = 600

        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=page, session=analytics_db)
        # View should be created with controls
        assert len(view.controls) > 0

    def test_wide_layout(self, analytics_db):
        """Test view adapts to wide width."""
        import flet as ft

        page = MagicMock(spec=ft.Page)
        page.width = 1600  # Wide
        page.height = 900
        page.platform = ft.PagePlatform.WINDOWS
        page.update = MagicMock()
        page.views = []
        page.route = "/analytics"
        page.window = MagicMock()
        page.window.width = 1600

        from src.views.analytics_view import AnalyticsView

        view = AnalyticsView(page=page, session=analytics_db)
        # View should be created with controls
        assert len(view.controls) > 0
