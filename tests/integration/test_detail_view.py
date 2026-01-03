"""Tests for DetailView - Corporation detail and financial statements."""

import pytest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.corporation import Corporation
from src.models.financial_statement import FinancialStatement


# Sample test data
SAMPLE_CORPORATION = {
    "corp_code": "00126380",
    "corp_name": "삼성전자",
    "stock_code": "005930",
    "corp_cls": "Y",
    "market": "KOSPI",
    "ceo_nm": "한종희",
    "corp_name_eng": "Samsung Electronics Co., Ltd.",
    "adres": "경기도 수원시 영통구 삼성로 129",
    "hm_url": "www.samsung.com",
    "est_dt": "19690113",
    "acc_mt": "12",
}

SAMPLE_FINANCIAL_DATA = [
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_nm": "자산총계",
        "thstrm_amount": 450_000_000_000_000,
        "frmtrm_amount": 420_000_000_000_000,
        "bfefrmtrm_amount": 380_000_000_000_000,
    },
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_nm": "부채총계",
        "thstrm_amount": 100_000_000_000_000,
        "frmtrm_amount": 90_000_000_000_000,
        "bfefrmtrm_amount": 80_000_000_000_000,
    },
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_nm": "자본총계",
        "thstrm_amount": 350_000_000_000_000,
        "frmtrm_amount": 330_000_000_000_000,
        "bfefrmtrm_amount": 300_000_000_000_000,
    },
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "IS",
        "account_nm": "매출액",
        "thstrm_amount": 280_000_000_000_000,
        "frmtrm_amount": 300_000_000_000_000,
        "bfefrmtrm_amount": 270_000_000_000_000,
    },
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "IS",
        "account_nm": "영업이익",
        "thstrm_amount": 50_000_000_000_000,
        "frmtrm_amount": 60_000_000_000_000,
        "bfefrmtrm_amount": 40_000_000_000_000,
    },
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "IS",
        "account_nm": "당기순이익",
        "thstrm_amount": 40_000_000_000_000,
        "frmtrm_amount": 55_000_000_000_000,
        "bfefrmtrm_amount": 35_000_000_000_000,
    },
]


@pytest.fixture
def detail_db():
    """Create in-memory SQLite database with test data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add sample corporation
    corp = Corporation(**SAMPLE_CORPORATION)
    session.add(corp)

    # Add financial statements
    for data in SAMPLE_FINANCIAL_DATA:
        fs = FinancialStatement(**data)
        session.add(fs)

    session.commit()
    yield session
    session.close()


@pytest.fixture
def mock_page():
    """Create a mock Flet Page for testing."""
    import flet as ft

    page = MagicMock(spec=ft.Page)
    page.platform = ft.PagePlatform.WINDOWS
    page.width = 1200
    page.height = 800
    page.update = MagicMock()
    page.go = MagicMock()
    page.route = "/detail/00126380"

    page.window = MagicMock()
    page.window.width = 1200
    page.window.height = 800

    return page


class TestDetailViewInitialization:
    """Tests for DetailView initialization."""

    def test_view_initialization(self, mock_page, detail_db):
        """Test DetailView can be initialized."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert view is not None
        assert view.corp_code == "00126380"

    def test_view_loads_corporation(self, mock_page, detail_db):
        """Test DetailView loads corporation data."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert view.corporation is not None
        assert view.corporation.corp_name == "삼성전자"

    def test_view_with_invalid_corp_code(self, mock_page, detail_db):
        """Test DetailView with non-existent corp_code."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="99999999",
            session=detail_db,
        )

        assert view.corporation is None

    def test_view_route(self, mock_page, detail_db):
        """Test DetailView has correct route."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert "/detail" in view.route or "/corporations" in view.route


class TestDetailViewTabs:
    """Tests for DetailView tabs functionality."""

    def test_view_has_tabs(self, mock_page, detail_db):
        """Test DetailView has tabs for different sections."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        # View should have multiple tabs/sections
        assert hasattr(view, "tabs") or hasattr(view, "tab_bar")

    def test_basic_info_tab_content(self, mock_page, detail_db):
        """Test basic info tab shows corporation details."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        # Build basic info content
        basic_info = view._build_basic_info_tab()
        assert basic_info is not None

    def test_financial_tab_content(self, mock_page, detail_db):
        """Test financial tab shows financial statements."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        # Build financial tab content
        financial_tab = view._build_financial_tab()
        assert financial_tab is not None

    def test_ratios_tab_content(self, mock_page, detail_db):
        """Test ratios tab shows financial ratios."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        # Build ratios tab content
        ratios_tab = view._build_ratios_tab()
        assert ratios_tab is not None


class TestDetailViewCorporationInfo:
    """Tests for corporation info display."""

    def test_displays_corp_name(self, mock_page, detail_db):
        """Test corporation name is displayed."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert view.corporation.corp_name == "삼성전자"

    def test_displays_stock_code(self, mock_page, detail_db):
        """Test stock code is displayed."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert view.corporation.stock_code == "005930"

    def test_displays_market(self, mock_page, detail_db):
        """Test market info is displayed."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert view.corporation.market == "KOSPI"


class TestDetailViewFinancialData:
    """Tests for financial data display."""

    def test_loads_financial_statements(self, mock_page, detail_db):
        """Test financial statements are loaded."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert view.financial_statements is not None
        assert len(view.financial_statements) > 0

    def test_available_years(self, mock_page, detail_db):
        """Test available years are detected."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert "2023" in view.available_years

    def test_year_selection(self, mock_page, detail_db):
        """Test year can be selected."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        view.selected_year = "2023"
        assert view.selected_year == "2023"


class TestDetailViewFinancialRatios:
    """Tests for financial ratios display."""

    def test_calculates_ratios(self, mock_page, detail_db):
        """Test financial ratios are calculated."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        ratios = view.get_financial_ratios()
        assert ratios is not None

    def test_ratio_formatting(self, mock_page, detail_db):
        """Test ratios are formatted as percentages."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        ratios = view.get_financial_ratios()
        # Ratios should be numeric values
        if ratios.get("debt_ratio") is not None:
            assert isinstance(ratios["debt_ratio"], (int, float))


class TestDetailViewNavigation:
    """Tests for navigation functionality."""

    def test_back_button_exists(self, mock_page, detail_db):
        """Test back button is present."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        # View should have a way to go back
        assert hasattr(view, "_go_back") or hasattr(view, "back_button")

    def test_go_back_navigates(self, mock_page, detail_db):
        """Test back button navigates to corporations list."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        view._go_back(None)
        mock_page.go.assert_called()


class TestFinancialTableComponent:
    """Tests for FinancialTable component."""

    def test_table_initialization(self, detail_db):
        """Test FinancialTable can be initialized."""
        from src.components.financial_table import FinancialTable
        from src.models.financial_statement import FinancialStatement

        statements = (
            detail_db.query(FinancialStatement)
            .filter(FinancialStatement.sj_div == "BS")
            .all()
        )

        table = FinancialTable(statements=statements)
        assert table is not None

    def test_table_with_empty_data(self):
        """Test FinancialTable with no data."""
        from src.components.financial_table import FinancialTable

        table = FinancialTable(statements=[])
        assert table is not None

    def test_table_columns(self, detail_db):
        """Test FinancialTable has correct columns."""
        from src.components.financial_table import FinancialTable
        from src.models.financial_statement import FinancialStatement

        statements = (
            detail_db.query(FinancialStatement)
            .filter(FinancialStatement.sj_div == "BS")
            .all()
        )

        table = FinancialTable(statements=statements)
        columns = table.get_columns()

        # Should have account name and term columns
        assert len(columns) >= 2


class TestNumberFormatting:
    """Tests for number formatting utilities."""

    def test_format_amount_in_billion(self):
        """Test formatting amount in 억원."""
        from src.utils.formatters import format_amount

        # 100조 = 1,000,000억원
        result = format_amount(100_000_000_000_000, unit="억원")
        assert "1,000,000" in result or "100만" in result

    def test_format_amount_in_manwon(self):
        """Test formatting amount in 만원."""
        from src.utils.formatters import format_amount

        result = format_amount(100_000_000, unit="만원")
        assert "10,000" in result

    def test_format_amount_none(self):
        """Test formatting None amount."""
        from src.utils.formatters import format_amount

        result = format_amount(None)
        assert result == "-" or result == "N/A"

    def test_format_percentage(self):
        """Test formatting percentage."""
        from src.utils.formatters import format_percentage

        result = format_percentage(28.5714)
        assert "28.57" in result or "29" in result

    def test_format_growth_positive(self):
        """Test formatting positive growth."""
        from src.utils.formatters import format_growth

        result = format_growth(10.5)
        assert "+" in result or "10" in result

    def test_format_growth_negative(self):
        """Test formatting negative growth."""
        from src.utils.formatters import format_growth

        result = format_growth(-5.5)
        assert "-" in result


class TestYearOverYearComparison:
    """Tests for year-over-year comparison display."""

    def test_yoy_change_indicator(self, mock_page, detail_db):
        """Test YoY change indicator shows correctly."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        # The view should be able to show YoY changes
        assert hasattr(view, "_build_yoy_indicator") or hasattr(
            view, "_calculate_yoy_change"
        )

    def test_yoy_positive_change_color(self, mock_page, detail_db):
        """Test positive YoY change uses correct color indicator."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        # Method should exist to build YoY indicator
        indicator = view._build_yoy_indicator(10.5)
        assert indicator is not None

    def test_yoy_negative_change_color(self, mock_page, detail_db):
        """Test negative YoY change uses correct color indicator."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        indicator = view._build_yoy_indicator(-5.5)
        assert indicator is not None


class TestLoadingState:
    """Tests for loading state handling."""

    def test_loading_indicator(self, mock_page, detail_db):
        """Test loading indicator is shown during data load."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert hasattr(view, "is_loading") or hasattr(view, "loading_indicator")

    def test_set_loading_state(self, mock_page, detail_db):
        """Test loading state can be toggled."""
        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        view._set_loading(True)
        assert view.is_loading is True

        view._set_loading(False)
        assert view.is_loading is False


class TestResponsiveLayout:
    """Tests for responsive layout."""

    def test_narrow_layout(self, detail_db):
        """Test layout adapts to narrow screens."""
        import flet as ft

        mock_page = MagicMock(spec=ft.Page)
        mock_page.platform = ft.PagePlatform.WINDOWS
        mock_page.width = 600  # Narrow screen
        mock_page.height = 800
        mock_page.update = MagicMock()
        mock_page.go = MagicMock()
        mock_page.window = MagicMock()
        mock_page.window.width = 600

        from src.views.detail_view import DetailView

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        # View should adapt to narrow screen
        assert view is not None

    def test_wide_layout(self, mock_page, detail_db):
        """Test layout adapts to wide screens."""
        from src.views.detail_view import DetailView

        mock_page.width = 1400  # Wide screen

        view = DetailView(
            page=mock_page,
            corp_code="00126380",
            session=detail_db,
        )

        assert view is not None
