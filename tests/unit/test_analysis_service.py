"""Tests for Analysis Service."""

import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.financial_statement import FinancialStatement
from src.services.analysis_service import AnalysisService


@pytest.fixture
def analysis_db():
    """Create in-memory SQLite for testing analysis service."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add test corporation
    from src.models.corporation import Corporation
    corp = Corporation(
        corp_code="00126380",
        corp_name="삼성전자",
        stock_code="005930",
        corp_cls="Y",
    )
    session.add(corp)

    # Add multi-year financial data for testing
    years = ["2021", "2022", "2023"]
    base_revenue = 200_000_000_000_000  # 200조
    base_operating_income = 35_000_000_000_000  # 35조
    base_net_income = 25_000_000_000_000  # 25조
    base_assets = 400_000_000_000_000  # 400조
    base_liabilities = 100_000_000_000_000  # 100조
    base_equity = 300_000_000_000_000  # 300조

    for i, year in enumerate(years):
        # Revenue grows 10% each year
        revenue = int(base_revenue * (1.1 ** i))
        operating_income = int(base_operating_income * (1.1 ** i))
        net_income = int(base_net_income * (1.1 ** i))
        assets = int(base_assets * (1.05 ** i))
        liabilities = int(base_liabilities * (1.02 ** i))
        equity = int(base_equity * (1.05 ** i))

        statements = [
            {"account_nm": "매출액", "sj_div": "IS", "thstrm_amount": revenue},
            {"account_nm": "영업이익", "sj_div": "IS", "thstrm_amount": operating_income},
            {"account_nm": "당기순이익", "sj_div": "IS", "thstrm_amount": net_income},
            {"account_nm": "자산총계", "sj_div": "BS", "thstrm_amount": assets},
            {"account_nm": "부채총계", "sj_div": "BS", "thstrm_amount": liabilities},
            {"account_nm": "자본총계", "sj_div": "BS", "thstrm_amount": equity},
            {"account_nm": "유동자산", "sj_div": "BS", "thstrm_amount": assets // 2},
            {"account_nm": "유동부채", "sj_div": "BS", "thstrm_amount": liabilities // 2},
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


class TestAnalysisService:
    """Tests for AnalysisService class."""

    def test_initialization(self, analysis_db):
        """Test service initialization."""
        service = AnalysisService(analysis_db)
        assert service is not None
        assert service.session == analysis_db

    def test_calculate_cagr_positive(self, analysis_db):
        """Test CAGR calculation with positive growth."""
        service = AnalysisService(analysis_db)
        # 2021: 200조, 2023: 242조 (10% annual growth)
        cagr = service.calculate_cagr(
            corp_code="00126380",
            account_nm="매출액",
            start_year="2021",
            end_year="2023",
        )
        assert cagr is not None
        assert 9.5 < cagr < 10.5  # Approximately 10%

    def test_calculate_cagr_single_year(self, analysis_db):
        """Test CAGR with single year returns None."""
        service = AnalysisService(analysis_db)
        cagr = service.calculate_cagr(
            corp_code="00126380",
            account_nm="매출액",
            start_year="2023",
            end_year="2023",
        )
        assert cagr is None

    def test_calculate_cagr_missing_data(self, analysis_db):
        """Test CAGR with missing data returns None."""
        service = AnalysisService(analysis_db)
        cagr = service.calculate_cagr(
            corp_code="00126380",
            account_nm="매출액",
            start_year="2019",
            end_year="2023",
        )
        assert cagr is None

    def test_get_growth_trend(self, analysis_db):
        """Test getting growth trend data."""
        service = AnalysisService(analysis_db)
        trend = service.get_growth_trend(
            corp_code="00126380",
            account_nm="매출액",
        )
        assert len(trend) >= 2
        assert all("year" in item and "value" in item for item in trend)
        # Should be sorted by year ascending
        years = [item["year"] for item in trend]
        assert years == sorted(years)

    def test_get_growth_rates(self, analysis_db):
        """Test getting year-over-year growth rates."""
        service = AnalysisService(analysis_db)
        rates = service.get_growth_rates(
            corp_code="00126380",
            account_nm="매출액",
        )
        assert len(rates) >= 1
        assert all("year" in item and "growth_rate" in item for item in rates)
        # Growth rates should be approximately 10%
        for rate in rates:
            assert 9 < rate["growth_rate"] < 11

    def test_get_ratio_trend(self, analysis_db):
        """Test getting financial ratio trend."""
        service = AnalysisService(analysis_db)
        ratios = service.get_ratio_trend(
            corp_code="00126380",
            ratio_type="operating_margin",
        )
        assert len(ratios) >= 1
        assert all("year" in item and "value" in item for item in ratios)
        # Operating margin should be around 17.5% (35조/200조)
        for ratio in ratios:
            assert 15 < ratio["value"] < 20

    def test_get_multi_account_trend(self, analysis_db):
        """Test getting multiple account trends for charts."""
        service = AnalysisService(analysis_db)
        trends = service.get_multi_account_trend(
            corp_code="00126380",
            accounts=["매출액", "영업이익", "당기순이익"],
        )
        assert "매출액" in trends
        assert "영업이익" in trends
        assert "당기순이익" in trends
        assert len(trends["매출액"]) >= 2

    def test_get_chart_data_revenue(self, analysis_db):
        """Test getting chart-ready revenue data."""
        service = AnalysisService(analysis_db)
        chart_data = service.get_chart_data(
            corp_code="00126380",
            chart_type="revenue",
        )
        assert "labels" in chart_data
        assert "datasets" in chart_data
        assert len(chart_data["labels"]) >= 2
        assert len(chart_data["datasets"]) >= 1

    def test_get_chart_data_profitability(self, analysis_db):
        """Test getting chart-ready profitability data."""
        service = AnalysisService(analysis_db)
        chart_data = service.get_chart_data(
            corp_code="00126380",
            chart_type="profitability",
        )
        assert "labels" in chart_data
        assert "datasets" in chart_data

    def test_get_chart_data_ratios(self, analysis_db):
        """Test getting chart-ready ratio data."""
        service = AnalysisService(analysis_db)
        chart_data = service.get_chart_data(
            corp_code="00126380",
            chart_type="ratios",
        )
        assert "labels" in chart_data
        assert "datasets" in chart_data

    def test_get_financial_health_score(self, analysis_db):
        """Test getting overall financial health score."""
        service = AnalysisService(analysis_db)
        result = service.get_financial_health_score(
            corp_code="00126380",
            bsns_year="2023",
        )
        assert result is not None
        assert "overall" in result
        assert "components" in result
        assert 0 <= result["overall"] <= 100

    def test_get_peer_comparison_data(self, analysis_db):
        """Test getting peer comparison data."""
        service = AnalysisService(analysis_db)
        # With single company, it should still work
        comparison = service.get_peer_comparison_data(
            corp_codes=["00126380"],
            metrics=["revenue", "operating_margin"],
            bsns_year="2023",
        )
        assert len(comparison) >= 1
        assert "corp_code" in comparison[0]

    def test_calculate_volatility(self, analysis_db):
        """Test calculating value volatility (standard deviation)."""
        service = AnalysisService(analysis_db)
        volatility = service.calculate_volatility(
            corp_code="00126380",
            account_nm="매출액",
        )
        assert volatility is not None
        assert volatility >= 0

    def test_get_growth_stability(self, analysis_db):
        """Test getting growth stability metrics."""
        service = AnalysisService(analysis_db)
        stability = service.get_growth_stability(
            corp_code="00126380",
            account_nm="매출액",
        )
        assert stability is not None
        assert "mean_growth" in stability
        assert "std_growth" in stability
        assert "stability_score" in stability


class TestCAGRCalculation:
    """Detailed tests for CAGR calculation edge cases."""

    def test_cagr_with_negative_start(self, analysis_db):
        """Test CAGR calculation when start value is negative."""
        service = AnalysisService(analysis_db)
        # Add statement with negative value
        stmt = FinancialStatement(
            corp_code="00126380",
            bsns_year="2020",
            reprt_code="11011",
            fs_div="CFS",
            sj_div="IS",
            account_nm="특별손실",
            thstrm_amount=-1_000_000_000,
            ord=100,
        )
        analysis_db.add(stmt)
        analysis_db.commit()

        cagr = service.calculate_cagr(
            corp_code="00126380",
            account_nm="특별손실",
            start_year="2020",
            end_year="2023",
        )
        # CAGR with negative start should return None
        assert cagr is None

    def test_cagr_with_zero_start(self, analysis_db):
        """Test CAGR calculation when start value is zero."""
        service = AnalysisService(analysis_db)
        stmt = FinancialStatement(
            corp_code="00126380",
            bsns_year="2020",
            reprt_code="11011",
            fs_div="CFS",
            sj_div="IS",
            account_nm="신규계정",
            thstrm_amount=0,
            ord=101,
        )
        analysis_db.add(stmt)
        analysis_db.commit()

        cagr = service.calculate_cagr(
            corp_code="00126380",
            account_nm="신규계정",
            start_year="2020",
            end_year="2023",
        )
        # CAGR with zero start should return None
        assert cagr is None


class TestTrendAnalysis:
    """Tests for trend analysis functionality."""

    def test_trend_with_missing_years(self, analysis_db):
        """Test trend analysis handles missing years gracefully."""
        service = AnalysisService(analysis_db)
        # Remove 2022 data
        analysis_db.query(FinancialStatement).filter(
            FinancialStatement.bsns_year == "2022",
            FinancialStatement.account_nm == "매출액",
        ).delete()
        analysis_db.commit()

        trend = service.get_growth_trend(
            corp_code="00126380",
            account_nm="매출액",
        )
        # Should still return available data
        assert len(trend) >= 1

    def test_trend_empty_result(self, analysis_db):
        """Test trend analysis with non-existent account."""
        service = AnalysisService(analysis_db)
        trend = service.get_growth_trend(
            corp_code="00126380",
            account_nm="존재하지않는계정",
        )
        assert len(trend) == 0


class TestChartDataGeneration:
    """Tests for chart data generation."""

    def test_chart_colors_assigned(self, analysis_db):
        """Test that chart datasets have colors assigned."""
        service = AnalysisService(analysis_db)
        chart_data = service.get_chart_data(
            corp_code="00126380",
            chart_type="revenue",
        )
        for dataset in chart_data["datasets"]:
            assert "color" in dataset or "backgroundColor" in dataset

    def test_chart_data_sorted_by_year(self, analysis_db):
        """Test that chart data is sorted chronologically."""
        service = AnalysisService(analysis_db)
        chart_data = service.get_chart_data(
            corp_code="00126380",
            chart_type="revenue",
        )
        labels = chart_data["labels"]
        assert labels == sorted(labels)
