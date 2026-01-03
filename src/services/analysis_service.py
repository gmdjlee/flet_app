"""Analysis Service for financial data analysis and chart data generation."""

import statistics
from typing import Any

from sqlalchemy.orm import Session

from src.services.financial_service import FinancialService

# Chart colors for consistent visualization
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


class AnalysisService:
    """Service for advanced financial analysis and chart data preparation.

    Provides CAGR calculation, trend analysis, volatility metrics,
    and chart-ready data formatting.

    Attributes:
        session: SQLAlchemy database session.
        financial_service: FinancialService instance for data access.
    """

    def __init__(self, session: Session) -> None:
        """Initialize analysis service with database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session
        self.financial_service = FinancialService(session)

    def calculate_cagr(
        self,
        corp_code: str,
        account_nm: str,
        start_year: str,
        end_year: str,
        fs_div: str = "CFS",
    ) -> float | None:
        """Calculate Compound Annual Growth Rate (CAGR).

        CAGR = (End Value / Start Value)^(1/years) - 1

        Args:
            corp_code: DART corporation code.
            account_nm: Account name to analyze.
            start_year: Start year (YYYY).
            end_year: End year (YYYY).
            fs_div: Financial statement division.

        Returns:
            CAGR as percentage, or None if calculation fails.
        """
        if start_year == end_year:
            return None

        start_value = self.financial_service.get_account_value(
            corp_code=corp_code,
            bsns_year=start_year,
            account_nm=account_nm,
            fs_div=fs_div,
        )

        end_value = self.financial_service.get_account_value(
            corp_code=corp_code,
            bsns_year=end_year,
            account_nm=account_nm,
            fs_div=fs_div,
        )

        if start_value is None or end_value is None:
            return None

        if start_value <= 0:
            return None

        years = int(end_year) - int(start_year)
        if years <= 0:
            return None

        try:
            cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
            return cagr
        except (ZeroDivisionError, ValueError):
            return None

    def get_growth_trend(
        self,
        corp_code: str,
        account_nm: str,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """Get growth trend data for an account.

        Args:
            corp_code: DART corporation code.
            account_nm: Account name to analyze.
            fs_div: Financial statement division.

        Returns:
            List of year-value pairs sorted by year ascending.
        """
        multi_year_data = self.financial_service.get_multi_year_account(
            corp_code=corp_code,
            account_nm=account_nm,
            fs_div=fs_div,
        )

        # Sort by year ascending for trend display
        trend = sorted(multi_year_data, key=lambda x: x["year"])
        return trend

    def get_growth_rates(
        self,
        corp_code: str,
        account_nm: str,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """Get year-over-year growth rates.

        Args:
            corp_code: DART corporation code.
            account_nm: Account name to analyze.
            fs_div: Financial statement division.

        Returns:
            List of year and growth rate pairs.
        """
        trend = self.get_growth_trend(corp_code, account_nm, fs_div)

        if len(trend) < 2:
            return []

        rates = []
        for i in range(1, len(trend)):
            prev_value = trend[i - 1]["value"]
            curr_value = trend[i]["value"]
            year = trend[i]["year"]

            if prev_value and prev_value != 0:
                growth_rate = ((curr_value - prev_value) / abs(prev_value)) * 100
                rates.append(
                    {
                        "year": year,
                        "growth_rate": growth_rate,
                        "prev_value": prev_value,
                        "curr_value": curr_value,
                    }
                )

        return rates

    def get_ratio_trend(
        self,
        corp_code: str,
        ratio_type: str,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """Get financial ratio trend over multiple years.

        Args:
            corp_code: DART corporation code.
            ratio_type: Type of ratio (operating_margin, net_margin, roe, roa, debt_ratio).
            fs_div: Financial statement division.

        Returns:
            List of year-value pairs for the ratio.
        """
        available_years = self.financial_service.get_available_years(corp_code)

        ratios = []
        for year in sorted(available_years):
            all_ratios = self.financial_service.get_financial_ratios(corp_code, year, fs_div)
            ratio_value = all_ratios.get(ratio_type)

            if ratio_value is not None:
                ratios.append(
                    {
                        "year": year,
                        "value": ratio_value,
                    }
                )

        return ratios

    def get_multi_account_trend(
        self,
        corp_code: str,
        accounts: list[str],
        fs_div: str = "CFS",
    ) -> dict[str, list[dict[str, Any]]]:
        """Get trends for multiple accounts.

        Args:
            corp_code: DART corporation code.
            accounts: List of account names to analyze.
            fs_div: Financial statement division.

        Returns:
            Dictionary mapping account names to their trend data.
        """
        result = {}
        for account in accounts:
            trend = self.get_growth_trend(corp_code, account, fs_div)
            result[account] = trend
        return result

    def get_chart_data(
        self,
        corp_code: str,
        chart_type: str,
        fs_div: str = "CFS",
    ) -> dict[str, Any]:
        """Get chart-ready data for visualization.

        Args:
            corp_code: DART corporation code.
            chart_type: Type of chart (revenue, profitability, ratios, growth).
            fs_div: Financial statement division.

        Returns:
            Dictionary with labels and datasets for charting.
        """
        if chart_type == "revenue":
            return self._get_revenue_chart_data(corp_code, fs_div)
        elif chart_type == "profitability":
            return self._get_profitability_chart_data(corp_code, fs_div)
        elif chart_type == "ratios":
            return self._get_ratios_chart_data(corp_code, fs_div)
        elif chart_type == "growth":
            return self._get_growth_chart_data(corp_code, fs_div)
        else:
            return {"labels": [], "datasets": []}

    def _get_revenue_chart_data(
        self,
        corp_code: str,
        fs_div: str,
    ) -> dict[str, Any]:
        """Get revenue and profit chart data."""
        accounts = ["매출액", "영업이익", "당기순이익"]
        trends = self.get_multi_account_trend(corp_code, accounts, fs_div)

        # Get all unique years
        all_years = set()
        for trend in trends.values():
            for item in trend:
                all_years.add(item["year"])

        labels = sorted(all_years)

        datasets = []
        for i, (account, trend) in enumerate(trends.items()):
            year_values = {item["year"]: item["value"] for item in trend}
            values = [year_values.get(year) for year in labels]
            datasets.append(
                {
                    "name": account,
                    "data": values,
                    "color": CHART_COLORS[i % len(CHART_COLORS)],
                    "backgroundColor": CHART_COLORS[i % len(CHART_COLORS)],
                }
            )

        return {"labels": labels, "datasets": datasets}

    def _get_profitability_chart_data(
        self,
        corp_code: str,
        fs_div: str,
    ) -> dict[str, Any]:
        """Get profitability margin chart data."""
        ratio_types = ["operating_margin", "net_margin"]
        ratio_names = {"operating_margin": "영업이익률", "net_margin": "순이익률"}

        all_years = set()
        ratio_data = {}

        for ratio_type in ratio_types:
            trend = self.get_ratio_trend(corp_code, ratio_type, fs_div)
            ratio_data[ratio_type] = {item["year"]: item["value"] for item in trend}
            for item in trend:
                all_years.add(item["year"])

        labels = sorted(all_years)

        datasets = []
        for i, ratio_type in enumerate(ratio_types):
            values = [ratio_data[ratio_type].get(year) for year in labels]
            datasets.append(
                {
                    "name": ratio_names[ratio_type],
                    "data": values,
                    "color": CHART_COLORS[i % len(CHART_COLORS)],
                    "backgroundColor": CHART_COLORS[i % len(CHART_COLORS)],
                }
            )

        return {"labels": labels, "datasets": datasets}

    def _get_ratios_chart_data(
        self,
        corp_code: str,
        fs_div: str,
    ) -> dict[str, Any]:
        """Get financial ratios chart data."""
        ratio_types = ["debt_ratio", "current_ratio", "roe", "roa"]
        ratio_names = {
            "debt_ratio": "부채비율",
            "current_ratio": "유동비율",
            "roe": "ROE",
            "roa": "ROA",
        }

        all_years = set()
        ratio_data = {}

        for ratio_type in ratio_types:
            trend = self.get_ratio_trend(corp_code, ratio_type, fs_div)
            ratio_data[ratio_type] = {item["year"]: item["value"] for item in trend}
            for item in trend:
                all_years.add(item["year"])

        labels = sorted(all_years)

        datasets = []
        for i, ratio_type in enumerate(ratio_types):
            values = [ratio_data[ratio_type].get(year) for year in labels]
            datasets.append(
                {
                    "name": ratio_names[ratio_type],
                    "data": values,
                    "color": CHART_COLORS[i % len(CHART_COLORS)],
                    "backgroundColor": CHART_COLORS[i % len(CHART_COLORS)],
                }
            )

        return {"labels": labels, "datasets": datasets}

    def _get_growth_chart_data(
        self,
        corp_code: str,
        fs_div: str,
    ) -> dict[str, Any]:
        """Get growth rates chart data."""
        accounts = ["매출액", "영업이익", "당기순이익"]
        account_growth = {}
        all_years = set()

        for account in accounts:
            rates = self.get_growth_rates(corp_code, account, fs_div)
            account_growth[account] = {item["year"]: item["growth_rate"] for item in rates}
            for item in rates:
                all_years.add(item["year"])

        labels = sorted(all_years)

        datasets = []
        for i, account in enumerate(accounts):
            values = [account_growth[account].get(year) for year in labels]
            datasets.append(
                {
                    "name": f"{account} 성장률",
                    "data": values,
                    "color": CHART_COLORS[i % len(CHART_COLORS)],
                    "backgroundColor": CHART_COLORS[i % len(CHART_COLORS)],
                }
            )

        return {"labels": labels, "datasets": datasets}

    def get_financial_health_score(
        self,
        corp_code: str,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> dict[str, Any]:
        """Calculate overall financial health score.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            Dictionary with overall score and component scores.
        """
        ratios = self.financial_service.get_financial_ratios(corp_code, bsns_year, fs_div)

        components = {}
        scores = []

        # Debt ratio score (lower is better, ideal < 100%)
        if ratios.get("debt_ratio") is not None:
            debt_score = max(0, min(100, 100 - (ratios["debt_ratio"] - 100) / 2))
            components["debt_ratio"] = {
                "value": ratios["debt_ratio"],
                "score": debt_score,
                "label": "부채비율",
            }
            scores.append(debt_score)

        # Current ratio score (higher is better, ideal > 200%)
        if ratios.get("current_ratio") is not None:
            current_score = min(100, ratios["current_ratio"] / 2)
            components["current_ratio"] = {
                "value": ratios["current_ratio"],
                "score": current_score,
                "label": "유동비율",
            }
            scores.append(current_score)

        # Operating margin score (higher is better)
        if ratios.get("operating_margin") is not None:
            op_margin = ratios["operating_margin"]
            op_score = min(100, max(0, op_margin * 5))  # 20% margin = 100 score
            components["operating_margin"] = {
                "value": op_margin,
                "score": op_score,
                "label": "영업이익률",
            }
            scores.append(op_score)

        # ROE score (higher is better)
        if ratios.get("roe") is not None:
            roe = ratios["roe"]
            roe_score = min(100, max(0, roe * 5))  # 20% ROE = 100 score
            components["roe"] = {
                "value": roe,
                "score": roe_score,
                "label": "ROE",
            }
            scores.append(roe_score)

        overall = sum(scores) / len(scores) if scores else 0

        return {
            "overall": overall,
            "components": components,
            "grade": self._get_grade(overall),
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"

    def get_peer_comparison_data(
        self,
        corp_codes: list[str],
        metrics: list[str],
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """Get comparison data for multiple corporations.

        Args:
            corp_codes: List of DART corporation codes.
            metrics: List of metrics to compare (revenue, operating_margin, etc.).
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            List of comparison data for each corporation.
        """
        from src.models.corporation import Corporation

        results = []
        for corp_code in corp_codes:
            corp = (
                self.session.query(Corporation).filter(Corporation.corp_code == corp_code).first()
            )

            if not corp:
                continue

            data = {
                "corp_code": corp_code,
                "corp_name": corp.corp_name,
            }

            for metric in metrics:
                if metric == "revenue":
                    data[metric] = self.financial_service.get_account_value(
                        corp_code, bsns_year, "매출액", fs_div
                    )
                elif metric == "operating_income":
                    data[metric] = self.financial_service.get_account_value(
                        corp_code, bsns_year, "영업이익", fs_div
                    )
                elif metric == "net_income":
                    data[metric] = self.financial_service.get_account_value(
                        corp_code, bsns_year, "당기순이익", fs_div
                    )
                elif metric in ["operating_margin", "net_margin", "roe", "roa", "debt_ratio"]:
                    ratios = self.financial_service.get_financial_ratios(
                        corp_code, bsns_year, fs_div
                    )
                    data[metric] = ratios.get(metric)

            results.append(data)

        return results

    def calculate_volatility(
        self,
        corp_code: str,
        account_nm: str,
        fs_div: str = "CFS",
    ) -> float | None:
        """Calculate value volatility (standard deviation).

        Args:
            corp_code: DART corporation code.
            account_nm: Account name to analyze.
            fs_div: Financial statement division.

        Returns:
            Standard deviation of values, or None.
        """
        trend = self.get_growth_trend(corp_code, account_nm, fs_div)

        if len(trend) < 2:
            return None

        values = [item["value"] for item in trend if item["value"] is not None]

        if len(values) < 2:
            return None

        try:
            return statistics.stdev(values)
        except statistics.StatisticsError:
            return None

    def get_growth_stability(
        self,
        corp_code: str,
        account_nm: str,
        fs_div: str = "CFS",
    ) -> dict[str, Any] | None:
        """Get growth stability metrics.

        Args:
            corp_code: DART corporation code.
            account_nm: Account name to analyze.
            fs_div: Financial statement division.

        Returns:
            Dictionary with mean growth, std deviation, and stability score.
        """
        rates = self.get_growth_rates(corp_code, account_nm, fs_div)

        if not rates:
            return None

        growth_values = [item["growth_rate"] for item in rates]

        if len(growth_values) < 1:
            return None

        mean_growth = statistics.mean(growth_values)

        if len(growth_values) >= 2:
            std_growth = statistics.stdev(growth_values)
        else:
            std_growth = 0

        # Stability score: higher mean growth with lower volatility is better
        # Score = mean_growth - std_growth (normalized)
        if std_growth > 0:
            stability_score = max(0, min(100, 50 + (mean_growth - std_growth) / 2))
        else:
            stability_score = max(0, min(100, 50 + mean_growth))

        return {
            "mean_growth": mean_growth,
            "std_growth": std_growth,
            "stability_score": stability_score,
            "num_periods": len(growth_values),
        }
