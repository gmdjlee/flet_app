"""Compare Service for corporation comparison functionality."""

import json
import statistics
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from src.models.corporation import Corporation
from src.services.analysis_service import AnalysisService
from src.services.financial_service import FinancialService
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CompareService:
    """Service for comparing multiple corporations.

    Provides functionality to select, compare, and analyze multiple
    corporations (up to 5) with various financial metrics.

    Attributes:
        session: SQLAlchemy database session.
        MAX_CORPORATIONS: Maximum number of corporations that can be compared.
    """

    MAX_CORPORATIONS = 5

    def __init__(self, session: Session) -> None:
        """Initialize compare service with database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session
        self.financial_service = FinancialService(session)
        self.analysis_service = AnalysisService(session)
        self._selected_corporations: list[str] = []
        self._comparison_sets: dict[str, list[str]] = {}
        self._load_comparison_sets()

    def _get_data_dir(self) -> Path:
        """Get data directory for storing comparison sets."""
        data_dir = Path.home() / ".dart-db-flet" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def _load_comparison_sets(self) -> None:
        """Load saved comparison sets from disk."""
        sets_file = self._get_data_dir() / "comparison_sets.json"
        if sets_file.exists():
            try:
                with open(sets_file, encoding="utf-8") as f:
                    self._comparison_sets = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._comparison_sets = {}

    def _save_comparison_sets(self) -> None:
        """Save comparison sets to disk."""
        sets_file = self._get_data_dir() / "comparison_sets.json"
        try:
            with open(sets_file, "w", encoding="utf-8") as f:
                json.dump(self._comparison_sets, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def add_corporation(self, corp_code: str) -> bool:
        """Add a corporation to the comparison list.

        Args:
            corp_code: DART corporation code.

        Returns:
            True if successfully added, False otherwise.
        """
        # Check if already at max limit
        if len(self._selected_corporations) >= self.MAX_CORPORATIONS:
            logger.warning(f"Cannot add {corp_code}: max corporations limit reached")
            return False

        # Check if already selected
        if corp_code in self._selected_corporations:
            logger.debug(f"Corporation {corp_code} already in comparison list")
            return False

        # Verify corporation exists in database
        corp = self.session.query(Corporation).filter(Corporation.corp_code == corp_code).first()
        if corp is None:
            logger.warning(f"Corporation not found: {corp_code}")
            return False

        self._selected_corporations.append(corp_code)
        logger.info(f"Added corporation to comparison: {corp_code}")
        return True

    def remove_corporation(self, corp_code: str) -> bool:
        """Remove a corporation from the comparison list.

        Args:
            corp_code: DART corporation code.

        Returns:
            True if successfully removed, False otherwise.
        """
        if corp_code not in self._selected_corporations:
            return False

        self._selected_corporations.remove(corp_code)
        return True

    def clear_corporations(self) -> None:
        """Clear all selected corporations."""
        self._selected_corporations.clear()

    def get_selected_corporations(self) -> list[str]:
        """Get list of selected corporation codes.

        Returns:
            List of corporation codes.
        """
        return self._selected_corporations.copy()

    def get_corporation_details(self) -> list[dict[str, Any]]:
        """Get detailed information for selected corporations.

        Returns:
            List of corporation details.
        """
        details = []
        for corp_code in self._selected_corporations:
            corp = (
                self.session.query(Corporation).filter(Corporation.corp_code == corp_code).first()
            )
            if corp:
                details.append(
                    {
                        "corp_code": corp.corp_code,
                        "corp_name": corp.corp_name,
                        "stock_code": corp.stock_code,
                        "market": corp.market,
                        "corp_cls": corp.corp_cls,
                    }
                )
        return details

    def get_comparison_table_data(
        self,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """Get comparison data for table display.

        Args:
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            List of comparison data for each corporation.
        """
        results = []
        for corp_code in self._selected_corporations:
            corp = (
                self.session.query(Corporation).filter(Corporation.corp_code == corp_code).first()
            )

            if not corp:
                continue

            # Get financial summary
            summary = self.financial_service.get_financial_summary(corp_code, bsns_year, fs_div)

            data = {
                "corp_code": corp_code,
                "corp_name": corp.corp_name,
                "stock_code": corp.stock_code,
                "market": corp.market,
                "revenue": summary.get("revenue"),
                "operating_income": summary.get("operating_income"),
                "net_income": summary.get("net_income"),
                "total_assets": summary.get("total_assets"),
                "total_liabilities": summary.get("total_liabilities"),
                "total_equity": summary.get("total_equity"),
            }

            # Add ratios
            ratios = summary.get("ratios", {})
            data["debt_ratio"] = ratios.get("debt_ratio")
            data["current_ratio"] = ratios.get("current_ratio")
            data["operating_margin"] = ratios.get("operating_margin")
            data["net_margin"] = ratios.get("net_margin")
            data["roe"] = ratios.get("roe")
            data["roa"] = ratios.get("roa")

            results.append(data)

        return results

    def get_comparison_chart_data(
        self,
        metric: str,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> dict[str, Any]:
        """Get chart-ready comparison data for a single metric.

        Args:
            metric: Metric to compare (revenue, operating_income, etc.).
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            Dictionary with labels and values for charting.
        """
        table_data = self.get_comparison_table_data(bsns_year, fs_div)

        labels = []
        values = []

        for data in table_data:
            labels.append(data.get("corp_name", ""))
            values.append(data.get(metric))

        return {
            "labels": labels,
            "values": values,
            "metric": metric,
            "year": bsns_year,
        }

    def get_multi_metric_comparison(
        self,
        metrics: list[str],
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> dict[str, dict[str, Any]]:
        """Get comparison data for multiple metrics.

        Args:
            metrics: List of metrics to compare.
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            Dictionary mapping metrics to their comparison data.
        """
        result = {}
        for metric in metrics:
            result[metric] = self.get_comparison_chart_data(metric, bsns_year, fs_div)
        return result

    def get_ratio_comparison(
        self,
        ratios: list[str],
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> dict[str, dict[str, Any]]:
        """Get comparison data for financial ratios.

        Args:
            ratios: List of ratio types to compare.
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            Dictionary mapping ratios to their comparison data.
        """
        return self.get_multi_metric_comparison(ratios, bsns_year, fs_div)

    def rank_by_metric(
        self,
        metric: str,
        bsns_year: str,
        ascending: bool = False,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """Rank corporations by a specific metric.

        Args:
            metric: Metric to rank by.
            bsns_year: Business year.
            ascending: If True, lower values rank higher.
            fs_div: Financial statement division.

        Returns:
            List of corporations with rank and value.
        """
        table_data = self.get_comparison_table_data(bsns_year, fs_div)

        # Filter out None values and sort
        valid_data = [d for d in table_data if d.get(metric) is not None]
        sorted_data = sorted(
            valid_data,
            key=lambda x: x.get(metric, 0) or 0,
            reverse=not ascending,
        )

        # Add rank
        for i, data in enumerate(sorted_data):
            data["rank"] = i + 1

        return sorted_data

    def get_summary_statistics(
        self,
        metric: str,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> dict[str, float | None]:
        """Get summary statistics for a metric across selected corporations.

        Args:
            metric: Metric to analyze.
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            Dictionary with average, max, min, and median.
        """
        table_data = self.get_comparison_table_data(bsns_year, fs_div)
        values = [d.get(metric) for d in table_data if d.get(metric) is not None]

        if not values:
            return {
                "average": None,
                "max": None,
                "min": None,
                "median": None,
            }

        return {
            "average": statistics.mean(values),
            "max": max(values),
            "min": min(values),
            "median": statistics.median(values),
        }

    def get_health_score_comparison(
        self,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """Get financial health score comparison.

        Args:
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            List of health scores for each corporation.
        """
        results = []
        for corp_code in self._selected_corporations:
            corp = (
                self.session.query(Corporation).filter(Corporation.corp_code == corp_code).first()
            )

            if not corp:
                continue

            health = self.analysis_service.get_financial_health_score(corp_code, bsns_year, fs_div)

            results.append(
                {
                    "corp_code": corp_code,
                    "corp_name": corp.corp_name,
                    "overall_score": health.get("overall", 0),
                    "grade": health.get("grade", "N/A"),
                    "components": health.get("components", {}),
                }
            )

        return results

    def save_comparison_set(self, name: str) -> bool:
        """Save current comparison set.

        Args:
            name: Name for the comparison set.

        Returns:
            True if successfully saved.
        """
        if not self._selected_corporations:
            return False

        self._comparison_sets[name] = self._selected_corporations.copy()
        self._save_comparison_sets()
        return True

    def load_comparison_set(self, name: str) -> bool:
        """Load a saved comparison set.

        Args:
            name: Name of the comparison set.

        Returns:
            True if successfully loaded.
        """
        if name not in self._comparison_sets:
            return False

        self._selected_corporations = self._comparison_sets[name].copy()
        return True

    def get_saved_comparison_sets(self) -> list[str]:
        """Get list of saved comparison set names.

        Returns:
            List of saved set names.
        """
        return list(self._comparison_sets.keys())

    def delete_comparison_set(self, name: str) -> bool:
        """Delete a saved comparison set.

        Args:
            name: Name of the comparison set.

        Returns:
            True if successfully deleted.
        """
        if name not in self._comparison_sets:
            return False

        del self._comparison_sets[name]
        self._save_comparison_sets()
        return True
