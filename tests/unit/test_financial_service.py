"""Tests for Financial Service."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.corporation import Corporation
from src.models.financial_statement import FinancialStatement


# Test data for financial statements
SAMPLE_FINANCIAL_DATA = [
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_nm": "자산총계",
        "thstrm_amount": 450_000_000_000_000,  # 450조
        "frmtrm_amount": 420_000_000_000_000,  # 420조
        "bfefrmtrm_amount": 380_000_000_000_000,  # 380조
    },
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_nm": "부채총계",
        "thstrm_amount": 100_000_000_000_000,  # 100조
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
        "thstrm_amount": 350_000_000_000_000,  # 350조
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
        "thstrm_amount": 280_000_000_000_000,  # 280조
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
        "thstrm_amount": 50_000_000_000_000,  # 50조
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
        "thstrm_amount": 40_000_000_000_000,  # 40조
        "frmtrm_amount": 55_000_000_000_000,
        "bfefrmtrm_amount": 35_000_000_000_000,
    },
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_nm": "유동자산",
        "thstrm_amount": 200_000_000_000_000,
        "frmtrm_amount": 180_000_000_000_000,
        "bfefrmtrm_amount": 160_000_000_000_000,
    },
    {
        "corp_code": "00126380",
        "bsns_year": "2023",
        "reprt_code": "11011",
        "fs_div": "CFS",
        "sj_div": "BS",
        "account_nm": "유동부채",
        "thstrm_amount": 70_000_000_000_000,
        "frmtrm_amount": 60_000_000_000_000,
        "bfefrmtrm_amount": 50_000_000_000_000,
    },
]


@pytest.fixture
def financial_db():
    """Create in-memory SQLite database with test data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add sample corporation
    corp = Corporation(
        corp_code="00126380",
        corp_name="삼성전자",
        stock_code="005930",
        corp_cls="Y",
        market="KOSPI",
    )
    session.add(corp)

    # Add financial statements
    for data in SAMPLE_FINANCIAL_DATA:
        fs = FinancialStatement(**data)
        session.add(fs)

    session.commit()
    yield session
    session.close()


class TestFinancialServiceBasic:
    """Basic Financial Service tests."""

    def test_service_initialization(self, financial_db):
        """Test FinancialService can be initialized."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        assert service is not None
        assert service.session == financial_db

    def test_get_financial_statements_by_corp_code(self, financial_db):
        """Test fetching financial statements by corp_code."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        statements = service.get_statements(corp_code="00126380")

        assert statements is not None
        assert len(statements) > 0
        assert all(s.corp_code == "00126380" for s in statements)

    def test_get_financial_statements_by_year(self, financial_db):
        """Test fetching financial statements by year."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        statements = service.get_statements(corp_code="00126380", bsns_year="2023")

        assert statements is not None
        assert all(s.bsns_year == "2023" for s in statements)

    def test_get_financial_statements_by_statement_type(self, financial_db):
        """Test fetching financial statements by type (BS, IS)."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)

        # Get balance sheet items
        bs_statements = service.get_statements(
            corp_code="00126380", sj_div="BS"
        )
        assert all(s.sj_div == "BS" for s in bs_statements)

        # Get income statement items
        is_statements = service.get_statements(
            corp_code="00126380", sj_div="IS"
        )
        assert all(s.sj_div == "IS" for s in is_statements)

    def test_get_statements_empty_result(self, financial_db):
        """Test fetching statements for non-existent corp."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        statements = service.get_statements(corp_code="99999999")

        assert statements == []


class TestFinancialServiceAccounts:
    """Tests for specific account retrieval."""

    def test_get_account_value(self, financial_db):
        """Test getting specific account value."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        value = service.get_account_value(
            corp_code="00126380",
            bsns_year="2023",
            account_nm="자산총계",
        )

        assert value == 450_000_000_000_000

    def test_get_account_value_not_found(self, financial_db):
        """Test getting non-existent account value."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        value = service.get_account_value(
            corp_code="00126380",
            bsns_year="2023",
            account_nm="존재하지않는계정",
        )

        assert value is None

    def test_get_key_accounts(self, financial_db):
        """Test getting key financial accounts."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        key_accounts = service.get_key_accounts(
            corp_code="00126380",
            bsns_year="2023",
        )

        assert "자산총계" in key_accounts
        assert "부채총계" in key_accounts
        assert "자본총계" in key_accounts
        assert "매출액" in key_accounts
        assert "영업이익" in key_accounts
        assert "당기순이익" in key_accounts


class TestFinancialRatioCalculation:
    """Tests for financial ratio calculations."""

    def test_calculate_debt_ratio(self, financial_db):
        """Test debt ratio calculation (부채비율 = 부채/자본 * 100)."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        ratio = service.calculate_ratio(
            corp_code="00126380",
            bsns_year="2023",
            numerator_account="부채총계",
            denominator_account="자본총계",
        )

        # 100조 / 350조 * 100 = 28.57%
        expected = 100_000_000_000_000 / 350_000_000_000_000 * 100
        assert ratio is not None
        assert abs(ratio - expected) < 0.01

    def test_calculate_current_ratio(self, financial_db):
        """Test current ratio calculation (유동비율 = 유동자산/유동부채 * 100)."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        ratio = service.calculate_ratio(
            corp_code="00126380",
            bsns_year="2023",
            numerator_account="유동자산",
            denominator_account="유동부채",
        )

        # 200조 / 70조 * 100 = 285.71%
        expected = 200_000_000_000_000 / 70_000_000_000_000 * 100
        assert ratio is not None
        assert abs(ratio - expected) < 0.01

    def test_calculate_operating_margin(self, financial_db):
        """Test operating margin calculation (영업이익률 = 영업이익/매출액 * 100)."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        ratio = service.calculate_ratio(
            corp_code="00126380",
            bsns_year="2023",
            numerator_account="영업이익",
            denominator_account="매출액",
        )

        # 50조 / 280조 * 100 = 17.86%
        expected = 50_000_000_000_000 / 280_000_000_000_000 * 100
        assert ratio is not None
        assert abs(ratio - expected) < 0.01

    def test_calculate_roe(self, financial_db):
        """Test ROE calculation (자기자본이익률 = 당기순이익/자본총계 * 100)."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        ratio = service.calculate_ratio(
            corp_code="00126380",
            bsns_year="2023",
            numerator_account="당기순이익",
            denominator_account="자본총계",
        )

        # 40조 / 350조 * 100 = 11.43%
        expected = 40_000_000_000_000 / 350_000_000_000_000 * 100
        assert ratio is not None
        assert abs(ratio - expected) < 0.01

    def test_calculate_ratio_division_by_zero(self, financial_db):
        """Test ratio calculation when denominator is zero."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)

        # Add a statement with zero value
        fs = FinancialStatement(
            corp_code="00126380",
            bsns_year="2023",
            reprt_code="11011",
            fs_div="CFS",
            sj_div="BS",
            account_nm="제로계정",
            thstrm_amount=0,
        )
        financial_db.add(fs)
        financial_db.commit()

        ratio = service.calculate_ratio(
            corp_code="00126380",
            bsns_year="2023",
            numerator_account="자산총계",
            denominator_account="제로계정",
        )

        assert ratio is None

    def test_calculate_ratio_missing_account(self, financial_db):
        """Test ratio calculation with missing account."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        ratio = service.calculate_ratio(
            corp_code="00126380",
            bsns_year="2023",
            numerator_account="존재하지않음",
            denominator_account="자본총계",
        )

        assert ratio is None


class TestFinancialRatiosSummary:
    """Tests for financial ratios summary."""

    def test_get_financial_ratios(self, financial_db):
        """Test getting all financial ratios for a corporation."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        ratios = service.get_financial_ratios(
            corp_code="00126380",
            bsns_year="2023",
        )

        assert ratios is not None
        assert "debt_ratio" in ratios  # 부채비율
        assert "current_ratio" in ratios  # 유동비율
        assert "operating_margin" in ratios  # 영업이익률
        assert "net_margin" in ratios  # 순이익률
        assert "roe" in ratios  # ROE

    def test_get_financial_summary(self, financial_db):
        """Test getting financial summary with key metrics."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        summary = service.get_financial_summary(
            corp_code="00126380",
            bsns_year="2023",
        )

        assert summary is not None
        assert "total_assets" in summary
        assert "total_liabilities" in summary
        assert "total_equity" in summary
        assert "revenue" in summary
        assert "operating_income" in summary
        assert "net_income" in summary
        assert "ratios" in summary


class TestMultiYearComparison:
    """Tests for multi-year data comparison."""

    def test_get_multi_year_account(self, financial_db):
        """Test getting account values across multiple years."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        result = service.get_multi_year_account(
            corp_code="00126380",
            account_nm="자산총계",
        )

        # Should get current year and include prior terms from the data
        assert result is not None
        assert len(result) > 0

    def test_calculate_yoy_growth(self, financial_db):
        """Test year-over-year growth calculation."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        growth = service.calculate_yoy_growth(
            corp_code="00126380",
            bsns_year="2023",
            account_nm="자산총계",
        )

        # (450조 - 420조) / 420조 * 100 = 7.14%
        expected = (450_000_000_000_000 - 420_000_000_000_000) / 420_000_000_000_000 * 100
        assert growth is not None
        assert abs(growth - expected) < 0.01


class TestFinancialStatementCRUD:
    """Tests for CRUD operations on financial statements."""

    def test_create_financial_statement(self, financial_db):
        """Test creating a new financial statement."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        data = {
            "corp_code": "00126380",
            "bsns_year": "2022",
            "reprt_code": "11011",
            "fs_div": "CFS",
            "sj_div": "BS",
            "account_nm": "테스트계정",
            "thstrm_amount": 1000000,
        }
        statement = service.create(data)

        assert statement is not None
        assert statement.id is not None
        assert statement.corp_code == "00126380"
        assert statement.account_nm == "테스트계정"

    def test_bulk_upsert(self, financial_db):
        """Test bulk upserting financial statements."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        data_list = [
            {
                "corp_code": "00126380",
                "bsns_year": "2022",
                "reprt_code": "11011",
                "fs_div": "CFS",
                "sj_div": "BS",
                "account_nm": "벌크계정1",
                "thstrm_amount": 1000000,
            },
            {
                "corp_code": "00126380",
                "bsns_year": "2022",
                "reprt_code": "11011",
                "fs_div": "CFS",
                "sj_div": "BS",
                "account_nm": "벌크계정2",
                "thstrm_amount": 2000000,
            },
        ]

        count = service.bulk_create(data_list)
        assert count == 2

    def test_get_available_years(self, financial_db):
        """Test getting available years for a corporation."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        years = service.get_available_years(corp_code="00126380")

        assert "2023" in years


class TestBalanceSheetStatements:
    """Tests for balance sheet statement retrieval."""

    def test_get_balance_sheet(self, financial_db):
        """Test getting balance sheet items."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        bs = service.get_balance_sheet(
            corp_code="00126380",
            bsns_year="2023",
        )

        assert bs is not None
        assert len(bs) > 0
        assert all(s.sj_div == "BS" for s in bs)


class TestIncomeStatement:
    """Tests for income statement retrieval."""

    def test_get_income_statement(self, financial_db):
        """Test getting income statement items."""
        from src.services.financial_service import FinancialService

        service = FinancialService(financial_db)
        income = service.get_income_statement(
            corp_code="00126380",
            bsns_year="2023",
        )

        assert income is not None
        assert len(income) > 0
        assert all(s.sj_div == "IS" for s in income)
