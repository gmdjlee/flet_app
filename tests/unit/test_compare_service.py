"""Tests for CompareService - TDD Phase 6."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.corporation import Corporation
from src.models.financial_statement import FinancialStatement


# Fixture for test database
@pytest.fixture
def compare_test_db():
    """Create in-memory SQLite for comparison testing."""
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
        Corporation(
            corp_code="00123456",
            corp_name="현대자동차",
            stock_code="005380",
            corp_cls="Y",
            market="KOSPI",
        ),
        Corporation(
            corp_code="00654321",
            corp_name="기아",
            stock_code="000270",
            corp_cls="Y",
            market="KOSPI",
        ),
        Corporation(
            corp_code="00999999",
            corp_name="테스트기업",
            stock_code="099999",
            corp_cls="K",
            market="KOSDAQ",
        ),
    ]
    for corp in corps:
        session.add(corp)

    # Create financial statements for testing
    financial_data = [
        # 삼성전자 2023
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자산총계", "thstrm_amount": 450000000000000, "ord": 1},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "부채총계", "thstrm_amount": 120000000000000, "ord": 2},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자본총계", "thstrm_amount": 330000000000000, "ord": 3},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "매출액", "thstrm_amount": 300000000000000, "ord": 1},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "영업이익", "thstrm_amount": 15000000000000, "ord": 2},
        {"corp_code": "00126380", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "당기순이익", "thstrm_amount": 10000000000000, "ord": 3},
        # SK하이닉스 2023
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자산총계", "thstrm_amount": 80000000000000, "ord": 1},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "부채총계", "thstrm_amount": 35000000000000, "ord": 2},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자본총계", "thstrm_amount": 45000000000000, "ord": 3},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "매출액", "thstrm_amount": 40000000000000, "ord": 1},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "영업이익", "thstrm_amount": -5000000000000, "ord": 2},
        {"corp_code": "00164779", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "당기순이익", "thstrm_amount": -8000000000000, "ord": 3},
        # LG전자 2023
        {"corp_code": "00401731", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자산총계", "thstrm_amount": 50000000000000, "ord": 1},
        {"corp_code": "00401731", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "부채총계", "thstrm_amount": 25000000000000, "ord": 2},
        {"corp_code": "00401731", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "BS",
         "account_nm": "자본총계", "thstrm_amount": 25000000000000, "ord": 3},
        {"corp_code": "00401731", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "매출액", "thstrm_amount": 85000000000000, "ord": 1},
        {"corp_code": "00401731", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "영업이익", "thstrm_amount": 3000000000000, "ord": 2},
        {"corp_code": "00401731", "bsns_year": "2023", "reprt_code": "11011", "fs_div": "CFS", "sj_div": "IS",
         "account_nm": "당기순이익", "thstrm_amount": 2000000000000, "ord": 3},
    ]

    for data in financial_data:
        stmt = FinancialStatement(**data)
        session.add(stmt)

    session.commit()
    yield session
    session.close()


class TestCompareServiceBasic:
    """Basic CompareService functionality tests."""

    def test_create_compare_service(self, compare_test_db):
        """Test CompareService instantiation."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        assert service is not None
        assert service.session == compare_test_db

    def test_max_corporations_limit(self, compare_test_db):
        """Test maximum of 5 corporations can be compared."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        assert service.MAX_CORPORATIONS == 5


class TestCompareServiceCorporationManagement:
    """Tests for managing corporations to compare."""

    def test_add_corporation_to_compare(self, compare_test_db):
        """Test adding a corporation to comparison list."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        result = service.add_corporation("00126380")

        assert result is True
        assert "00126380" in service.get_selected_corporations()

    def test_add_corporation_returns_corp_info(self, compare_test_db):
        """Test adding returns corporation info."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        result = service.add_corporation("00126380")

        assert result is True
        corps = service.get_selected_corporations()
        assert len(corps) == 1

    def test_add_multiple_corporations(self, compare_test_db):
        """Test adding multiple corporations."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")
        service.add_corporation("00401731")

        corps = service.get_selected_corporations()
        assert len(corps) == 3

    def test_cannot_exceed_max_corporations(self, compare_test_db):
        """Test that adding more than MAX_CORPORATIONS fails."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)

        # Add 5 corporations
        service.add_corporation("00126380")
        service.add_corporation("00164779")
        service.add_corporation("00401731")
        service.add_corporation("00123456")
        service.add_corporation("00654321")

        # Try to add 6th
        result = service.add_corporation("00999999")
        assert result is False
        assert len(service.get_selected_corporations()) == 5

    def test_remove_corporation(self, compare_test_db):
        """Test removing a corporation from comparison list."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        result = service.remove_corporation("00126380")
        assert result is True
        assert "00126380" not in service.get_selected_corporations()
        assert len(service.get_selected_corporations()) == 1

    def test_remove_nonexistent_corporation(self, compare_test_db):
        """Test removing a corporation not in list."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        result = service.remove_corporation("00126380")
        assert result is False

    def test_clear_corporations(self, compare_test_db):
        """Test clearing all corporations."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        service.clear_corporations()
        assert len(service.get_selected_corporations()) == 0

    def test_cannot_add_duplicate_corporation(self, compare_test_db):
        """Test that duplicate corporations are not added."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        result = service.add_corporation("00126380")

        assert result is False
        assert len(service.get_selected_corporations()) == 1

    def test_cannot_add_invalid_corporation(self, compare_test_db):
        """Test that invalid corporation codes are rejected."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        result = service.add_corporation("invalid_code")
        assert result is False


class TestCompareServiceComparisonData:
    """Tests for getting comparison data."""

    def test_get_comparison_table_data(self, compare_test_db):
        """Test getting comparison table data."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        data = service.get_comparison_table_data("2023")
        assert len(data) == 2
        assert data[0]["corp_name"] == "삼성전자"
        assert data[1]["corp_name"] == "SK하이닉스"

    def test_comparison_table_includes_metrics(self, compare_test_db):
        """Test that comparison table includes financial metrics."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")

        data = service.get_comparison_table_data("2023")
        assert "revenue" in data[0]
        assert "operating_income" in data[0]
        assert "net_income" in data[0]
        assert "total_assets" in data[0]

    def test_comparison_table_includes_ratios(self, compare_test_db):
        """Test that comparison table includes financial ratios."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")

        data = service.get_comparison_table_data("2023")
        assert "debt_ratio" in data[0]
        assert "roe" in data[0]
        assert "operating_margin" in data[0]

    def test_get_comparison_chart_data(self, compare_test_db):
        """Test getting chart-ready comparison data."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        chart_data = service.get_comparison_chart_data("revenue", "2023")
        assert "labels" in chart_data
        assert "values" in chart_data
        assert len(chart_data["labels"]) == 2
        assert len(chart_data["values"]) == 2

    def test_get_multi_metric_comparison(self, compare_test_db):
        """Test comparing multiple metrics at once."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        metrics = ["revenue", "operating_income", "net_income"]
        data = service.get_multi_metric_comparison(metrics, "2023")

        assert len(data) == len(metrics)
        for metric in metrics:
            assert metric in data
            assert len(data[metric]["labels"]) == 2

    def test_get_ratio_comparison(self, compare_test_db):
        """Test comparing financial ratios."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        ratios = ["debt_ratio", "roe", "operating_margin"]
        data = service.get_ratio_comparison(ratios, "2023")

        assert len(data) == len(ratios)
        for ratio in ratios:
            assert ratio in data


class TestCompareServiceRanking:
    """Tests for corporation ranking functionality."""

    def test_rank_by_metric(self, compare_test_db):
        """Test ranking corporations by a metric."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")  # 삼성전자 (높은 매출)
        service.add_corporation("00164779")  # SK하이닉스
        service.add_corporation("00401731")  # LG전자

        ranked = service.rank_by_metric("revenue", "2023")
        assert ranked[0]["corp_name"] == "삼성전자"  # 가장 높은 매출

    def test_rank_descending(self, compare_test_db):
        """Test ranking in descending order."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        ranked = service.rank_by_metric("revenue", "2023", ascending=False)
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2

    def test_rank_ascending(self, compare_test_db):
        """Test ranking in ascending order (for debt ratio, lower is better)."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        ranked = service.rank_by_metric("debt_ratio", "2023", ascending=True)
        # Lower debt ratio is ranked first
        assert len(ranked) == 2


class TestCompareServiceSaveLoad:
    """Tests for saving and loading comparison sets."""

    def test_save_comparison_set(self, compare_test_db):
        """Test saving a comparison set."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        result = service.save_comparison_set("반도체 기업 비교")
        assert result is True

    def test_load_comparison_set(self, compare_test_db):
        """Test loading a saved comparison set."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")
        service.save_comparison_set("반도체 기업 비교")

        # Clear and reload
        service.clear_corporations()
        result = service.load_comparison_set("반도체 기업 비교")

        assert result is True
        assert len(service.get_selected_corporations()) == 2

    def test_get_saved_comparison_sets(self, compare_test_db):
        """Test getting list of saved comparison sets."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.save_comparison_set("세트1")
        service.save_comparison_set("세트2")

        saved_sets = service.get_saved_comparison_sets()
        assert len(saved_sets) >= 2
        assert "세트1" in saved_sets
        assert "세트2" in saved_sets

    def test_delete_comparison_set(self, compare_test_db):
        """Test deleting a saved comparison set."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.save_comparison_set("삭제할 세트")

        result = service.delete_comparison_set("삭제할 세트")
        assert result is True
        assert "삭제할 세트" not in service.get_saved_comparison_sets()


class TestCompareServiceCorporationDetails:
    """Tests for getting corporation details in comparison."""

    def test_get_corporation_details(self, compare_test_db):
        """Test getting detailed corporation info."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")

        details = service.get_corporation_details()
        assert len(details) == 1
        assert details[0]["corp_code"] == "00126380"
        assert details[0]["corp_name"] == "삼성전자"
        assert details[0]["stock_code"] == "005930"
        assert details[0]["market"] == "KOSPI"

    def test_get_summary_statistics(self, compare_test_db):
        """Test getting summary statistics for selected corporations."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")
        service.add_corporation("00401731")

        stats = service.get_summary_statistics("revenue", "2023")
        assert "average" in stats
        assert "max" in stats
        assert "min" in stats
        assert "median" in stats

    def test_get_health_score_comparison(self, compare_test_db):
        """Test comparing financial health scores."""
        from src.services.compare_service import CompareService

        service = CompareService(compare_test_db)
        service.add_corporation("00126380")
        service.add_corporation("00164779")

        scores = service.get_health_score_comparison("2023")
        assert len(scores) == 2
        for score in scores:
            assert "corp_name" in score
            assert "overall_score" in score
            assert "grade" in score
