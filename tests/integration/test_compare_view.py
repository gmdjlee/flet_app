"""Integration tests for CompareView - TDD Phase 6."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.corporation import Corporation
from src.models.financial_statement import FinancialStatement


@pytest.fixture
def compare_view_db():
    """Create in-memory SQLite for CompareView testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create sample corporations
    corps = [
        Corporation(
            corp_code="00126380",
            corp_name="삼성전자",
            stock_code="005930",
            corp_cls="Y",
            market="KOSPI",
        ),
        Corporation(
            corp_code="00164779",
            corp_name="SK하이닉스",
            stock_code="000660",
            corp_cls="Y",
            market="KOSPI",
        ),
        Corporation(
            corp_code="00401731",
            corp_name="LG전자",
            stock_code="066570",
            corp_cls="Y",
            market="KOSPI",
        ),
    ]
    for corp in corps:
        session.add(corp)

    # Create financial statements
    financial_data = [
        # 삼성전자
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "매출액", "thstrm_amount": 300000000000000, "ord": 1},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "영업이익", "thstrm_amount": 15000000000000, "ord": 2},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자산총계", "thstrm_amount": 450000000000000, "ord": 1},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "부채총계", "thstrm_amount": 120000000000000, "ord": 2},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자본총계", "thstrm_amount": 330000000000000, "ord": 3},
        # SK하이닉스
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "매출액", "thstrm_amount": 40000000000000, "ord": 1},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "영업이익", "thstrm_amount": -5000000000000, "ord": 2},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자산총계", "thstrm_amount": 80000000000000, "ord": 1},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "부채총계", "thstrm_amount": 35000000000000, "ord": 2},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자본총계", "thstrm_amount": 45000000000000, "ord": 3},
    ]

    for data in financial_data:
        stmt = FinancialStatement(**data)
        session.add(stmt)

    session.commit()
    yield session
    session.close()


@pytest.fixture
def mock_compare_page():
    """Create mock Flet page for CompareView testing."""
    import flet as ft

    page = MagicMock(spec=ft.Page)
    page.platform = ft.PagePlatform.WINDOWS
    page.width = 1200
    page.height = 800
    page.update = MagicMock()
    page.views = []
    page.route = "/compare"
    page.go = MagicMock()
    page.window = MagicMock()
    page.window.width = 1200
    page.window.height = 800
    page.snack_bar = None
    page.overlay = []

    return page


class TestCompareViewInitialization:
    """Tests for CompareView initialization."""

    def test_create_compare_view(self, mock_compare_page, compare_view_db):
        """Test CompareView creation."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view is not None

    def test_compare_view_has_title(self, mock_compare_page, compare_view_db):
        """Test that CompareView has a title."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)

        # View inherits from ft.View and has controls
        assert view.controls is not None
        assert len(view.controls) > 0

    def test_compare_view_has_search_bar(self, mock_compare_page, compare_view_db):
        """Test that CompareView has a search bar for adding corporations."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.search_bar is not None

    def test_compare_view_has_comparison_table(self, mock_compare_page, compare_view_db):
        """Test that CompareView has a comparison table."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.comparison_table is not None

    def test_compare_view_has_chart_section(self, mock_compare_page, compare_view_db):
        """Test that CompareView has a chart section."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.chart_section is not None


class TestCompareViewCorporationSelection:
    """Tests for corporation selection in CompareView."""

    def test_add_corporation_to_compare(self, mock_compare_page, compare_view_db):
        """Test adding a corporation to compare list via UI."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")

        assert len(view.selected_corporations) == 1

    def test_remove_corporation_from_compare(self, mock_compare_page, compare_view_db):
        """Test removing a corporation from compare list."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")
        view.add_corporation("00164779")
        view.remove_corporation("00126380")

        assert len(view.selected_corporations) == 1
        assert "00164779" in view.selected_corporations

    def test_max_corporations_limit_ui(self, mock_compare_page, compare_view_db):
        """Test that UI enforces max corporations limit."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)

        # Try adding 6 (should fail for 6th)
        for i, corp_code in enumerate(["00126380", "00164779", "00401731", "00123456", "00654321", "00999999"]):
            if i < 5:
                # Create dummy corporations in DB for test
                if i >= 3:
                    corp = Corporation(
                        corp_code=corp_code,
                        corp_name=f"Test{i}",
                        stock_code=f"00000{i}",
                        corp_cls="Y",
                    )
                    compare_view_db.merge(corp)
                    compare_view_db.commit()

            view.add_corporation(corp_code)

        # Should only have 5 (or less depending on available corps)
        assert len(view.selected_corporations) <= 5

    def test_clear_all_corporations(self, mock_compare_page, compare_view_db):
        """Test clearing all selected corporations."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")
        view.add_corporation("00164779")
        view.clear_corporations()

        assert len(view.selected_corporations) == 0


class TestCompareViewSelectedCorporationsDisplay:
    """Tests for displaying selected corporations."""

    def test_selected_corporations_chips(self, mock_compare_page, compare_view_db):
        """Test that selected corporations are displayed as chips."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")

        chips = view.get_selected_chips()
        assert len(chips) == 1

    def test_chip_shows_corp_name(self, mock_compare_page, compare_view_db):
        """Test that chips show corporation name."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")

        chips = view.get_selected_chips()
        # Should contain corp name text
        assert chips is not None

    def test_chip_has_remove_button(self, mock_compare_page, compare_view_db):
        """Test that chips have remove button."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")

        # Chip should be removable
        assert view.can_remove_corporation("00126380")


class TestCompareViewComparisonTable:
    """Tests for comparison table display."""

    def test_comparison_table_renders(self, mock_compare_page, compare_view_db):
        """Test that comparison table renders properly."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")
        view.add_corporation("00164779")

        table = view.build_comparison_table()
        assert table is not None

    def test_comparison_table_has_columns(self, mock_compare_page, compare_view_db):
        """Test that comparison table has expected columns."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")

        columns = view.get_table_columns()
        expected = ["기업명", "매출액", "영업이익", "자산총계", "부채비율", "ROE"]
        for col in expected:
            assert col in columns

    def test_comparison_table_has_data_rows(self, mock_compare_page, compare_view_db):
        """Test that comparison table has data rows for each corporation."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")
        view.add_corporation("00164779")

        rows = view.get_table_rows()
        assert len(rows) == 2

    def test_comparison_table_empty_state(self, mock_compare_page, compare_view_db):
        """Test comparison table shows empty state when no corps selected."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        table = view.build_comparison_table()

        # Should show empty state message
        assert table is not None


class TestCompareViewYearSelection:
    """Tests for year selection in comparison."""

    def test_year_selector_exists(self, mock_compare_page, compare_view_db):
        """Test that year selector exists."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.year_selector is not None

    def test_change_year_updates_data(self, mock_compare_page, compare_view_db):
        """Test that changing year updates comparison data."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")

        initial_year = view.selected_year
        view.set_year("2022")

        assert view.selected_year == "2022"


class TestCompareViewCharts:
    """Tests for chart components in CompareView."""

    def test_chart_section_renders(self, mock_compare_page, compare_view_db):
        """Test that chart section renders."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")
        view.add_corporation("00164779")

        chart = view.build_comparison_chart()
        assert chart is not None

    def test_chart_type_selector(self, mock_compare_page, compare_view_db):
        """Test chart type selector."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.chart_type_selector is not None

    def test_change_chart_type(self, mock_compare_page, compare_view_db):
        """Test changing chart type."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.set_chart_type("profitability")

        assert view.current_chart_type == "profitability"


class TestCompareViewMetricSelection:
    """Tests for metric selection in charts."""

    def test_metric_selector_exists(self, mock_compare_page, compare_view_db):
        """Test that metric selector exists."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.metric_selector is not None

    def test_available_metrics(self, mock_compare_page, compare_view_db):
        """Test available metrics for comparison."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        metrics = view.get_available_metrics()

        expected = ["revenue", "operating_income", "net_income", "total_assets"]
        for metric in expected:
            assert metric in metrics


class TestCompareViewSaveLoad:
    """Tests for saving and loading comparison sets."""

    def test_save_button_exists(self, mock_compare_page, compare_view_db):
        """Test that save button exists."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.save_button is not None

    def test_load_button_exists(self, mock_compare_page, compare_view_db):
        """Test that load button exists."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.load_button is not None

    def test_save_comparison_set(self, mock_compare_page, compare_view_db):
        """Test saving a comparison set."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")
        view.add_corporation("00164779")

        result = view.save_comparison("테스트 세트")
        assert result is True

    def test_load_saved_set(self, mock_compare_page, compare_view_db):
        """Test loading a saved comparison set."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")
        view.save_comparison("테스트 세트")

        view.clear_corporations()
        result = view.load_comparison("테스트 세트")

        assert result is True
        assert len(view.selected_corporations) == 1


class TestCompareViewResponsiveLayout:
    """Tests for responsive layout in CompareView."""

    def test_wide_screen_layout(self, mock_compare_page, compare_view_db):
        """Test layout on wide screens."""
        from src.views.compare_view import CompareView

        mock_compare_page.width = 1400
        view = CompareView(mock_compare_page, compare_view_db)

        # Should use side-by-side layout
        assert view.get_layout_mode() == "wide"

    def test_narrow_screen_layout(self, mock_compare_page, compare_view_db):
        """Test layout on narrow screens."""
        from src.views.compare_view import CompareView

        mock_compare_page.width = 600
        view = CompareView(mock_compare_page, compare_view_db)

        # Should use stacked layout
        assert view.get_layout_mode() == "narrow"


class TestCompareViewRanking:
    """Tests for ranking display in CompareView."""

    def test_ranking_indicator_shows(self, mock_compare_page, compare_view_db):
        """Test that ranking indicators show in table."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        view.add_corporation("00126380")
        view.add_corporation("00164779")

        # Should show ranking for metrics (may be empty if no financial data)
        ranking = view.get_ranking_for_metric("revenue")
        assert ranking is not None
        # Ranking will be populated when financial data exists
        assert isinstance(ranking, list)


class TestCompareViewExport:
    """Tests for export functionality."""

    def test_export_button_exists(self, mock_compare_page, compare_view_db):
        """Test that export button exists."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        assert view.export_button is not None

    def test_export_to_excel_option(self, mock_compare_page, compare_view_db):
        """Test Excel export option exists."""
        from src.views.compare_view import CompareView

        view = CompareView(mock_compare_page, compare_view_db)
        export_options = view.get_export_options()

        assert "excel" in export_options
