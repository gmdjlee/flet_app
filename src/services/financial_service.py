"""Financial Service for managing financial statement data."""

from typing import Any

from sqlalchemy.orm import Session

from src.models.financial_statement import FinancialStatement
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Key account names used for financial analysis
KEY_ACCOUNTS = [
    "자산총계",
    "부채총계",
    "자본총계",
    "유동자산",
    "유동부채",
    "비유동자산",
    "비유동부채",
    "매출액",
    "영업이익",
    "당기순이익",
    "영업수익",
    "매출총이익",
]

# Alternative account names for the same concepts
ACCOUNT_ALIASES = {
    "매출액": ["매출액", "영업수익", "수익(매출액)"],
    "영업이익": ["영업이익", "영업이익(손실)"],
    "당기순이익": ["당기순이익", "당기순이익(손실)", "분기순이익"],
}


class FinancialService:
    """Service for managing financial statement data in the database.

    Provides methods to query, analyze, and calculate ratios for
    financial statements.

    Attributes:
        session: SQLAlchemy database session.
    """

    def __init__(self, session: Session) -> None:
        """Initialize financial service with database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def get_statements(
        self,
        corp_code: str,
        bsns_year: str | None = None,
        reprt_code: str | None = None,
        fs_div: str | None = None,
        sj_div: str | None = None,
    ) -> list[FinancialStatement]:
        """Get financial statements with filters.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year (optional).
            reprt_code: Report code (optional).
            fs_div: Financial statement division - CFS/OFS (optional).
            sj_div: Statement division - BS/IS/CF/etc (optional).

        Returns:
            List of FinancialStatement instances.
        """
        query = self.session.query(FinancialStatement).filter(
            FinancialStatement.corp_code == corp_code
        )

        if bsns_year:
            query = query.filter(FinancialStatement.bsns_year == bsns_year)

        if reprt_code:
            query = query.filter(FinancialStatement.reprt_code == reprt_code)

        if fs_div:
            query = query.filter(FinancialStatement.fs_div == fs_div)

        if sj_div:
            query = query.filter(FinancialStatement.sj_div == sj_div)

        return query.order_by(FinancialStatement.ord).all()

    def get_balance_sheet(
        self,
        corp_code: str,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> list[FinancialStatement]:
        """Get balance sheet (재무상태표) items.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            fs_div: Financial statement division (default: CFS=consolidated).

        Returns:
            List of balance sheet items.
        """
        return self.get_statements(
            corp_code=corp_code,
            bsns_year=bsns_year,
            fs_div=fs_div,
            sj_div="BS",
        )

    def get_income_statement(
        self,
        corp_code: str,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> list[FinancialStatement]:
        """Get income statement (손익계산서) items.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            List of income statement items.
        """
        return self.get_statements(
            corp_code=corp_code,
            bsns_year=bsns_year,
            fs_div=fs_div,
            sj_div="IS",
        )

    def get_account_value(
        self,
        corp_code: str,
        bsns_year: str,
        account_nm: str,
        fs_div: str = "CFS",
        term: str = "thstrm",
    ) -> int | None:
        """Get specific account value.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            account_nm: Account name to find.
            fs_div: Financial statement division.
            term: Term to get (thstrm=current, frmtrm=prior, bfefrmtrm=before prior).

        Returns:
            Account value or None if not found.
        """
        # Try exact match first
        statement = (
            self.session.query(FinancialStatement)
            .filter(
                FinancialStatement.corp_code == corp_code,
                FinancialStatement.bsns_year == bsns_year,
                FinancialStatement.account_nm == account_nm,
                FinancialStatement.fs_div == fs_div,
            )
            .first()
        )

        # Try aliases if not found
        if statement is None and account_nm in ACCOUNT_ALIASES:
            for alias in ACCOUNT_ALIASES[account_nm]:
                statement = (
                    self.session.query(FinancialStatement)
                    .filter(
                        FinancialStatement.corp_code == corp_code,
                        FinancialStatement.bsns_year == bsns_year,
                        FinancialStatement.account_nm == alias,
                        FinancialStatement.fs_div == fs_div,
                    )
                    .first()
                )
                if statement:
                    break

        if statement is None:
            return None

        # Get the appropriate term value
        if term == "thstrm":
            return statement.thstrm_amount
        elif term == "frmtrm":
            return statement.frmtrm_amount
        elif term == "bfefrmtrm":
            return statement.bfefrmtrm_amount

        return None

    def get_key_accounts(
        self,
        corp_code: str,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> dict[str, int | None]:
        """Get key financial accounts.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            Dictionary mapping account names to values.
        """
        result = {}
        for account in KEY_ACCOUNTS:
            value = self.get_account_value(
                corp_code=corp_code,
                bsns_year=bsns_year,
                account_nm=account,
                fs_div=fs_div,
            )
            if value is not None:
                result[account] = value

        return result

    def calculate_ratio(
        self,
        corp_code: str,
        bsns_year: str,
        numerator_account: str,
        denominator_account: str,
        fs_div: str = "CFS",
    ) -> float | None:
        """Calculate financial ratio.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            numerator_account: Account name for numerator.
            denominator_account: Account name for denominator.
            fs_div: Financial statement division.

        Returns:
            Ratio value as percentage, or None if calculation fails.
        """
        numerator = self.get_account_value(
            corp_code=corp_code,
            bsns_year=bsns_year,
            account_nm=numerator_account,
            fs_div=fs_div,
        )

        denominator = self.get_account_value(
            corp_code=corp_code,
            bsns_year=bsns_year,
            account_nm=denominator_account,
            fs_div=fs_div,
        )

        if numerator is None or denominator is None:
            return None

        if denominator == 0:
            return None

        return (numerator / denominator) * 100

    def get_financial_ratios(
        self,
        corp_code: str,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> dict[str, float | None]:
        """Calculate all financial ratios.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            Dictionary of ratio names to values.
        """
        ratios = {}

        # 부채비율 (Debt Ratio) = 부채총계 / 자본총계 * 100
        ratios["debt_ratio"] = self.calculate_ratio(
            corp_code, bsns_year, "부채총계", "자본총계", fs_div
        )

        # 유동비율 (Current Ratio) = 유동자산 / 유동부채 * 100
        ratios["current_ratio"] = self.calculate_ratio(
            corp_code, bsns_year, "유동자산", "유동부채", fs_div
        )

        # 영업이익률 (Operating Margin) = 영업이익 / 매출액 * 100
        ratios["operating_margin"] = self.calculate_ratio(
            corp_code, bsns_year, "영업이익", "매출액", fs_div
        )

        # 순이익률 (Net Margin) = 당기순이익 / 매출액 * 100
        ratios["net_margin"] = self.calculate_ratio(
            corp_code, bsns_year, "당기순이익", "매출액", fs_div
        )

        # ROE = 당기순이익 / 자본총계 * 100
        ratios["roe"] = self.calculate_ratio(corp_code, bsns_year, "당기순이익", "자본총계", fs_div)

        # ROA = 당기순이익 / 자산총계 * 100
        ratios["roa"] = self.calculate_ratio(corp_code, bsns_year, "당기순이익", "자산총계", fs_div)

        return ratios

    def get_financial_summary(
        self,
        corp_code: str,
        bsns_year: str,
        fs_div: str = "CFS",
    ) -> dict[str, Any]:
        """Get comprehensive financial summary.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            fs_div: Financial statement division.

        Returns:
            Dictionary with key metrics and ratios.
        """
        logger.debug(f"Getting financial summary for {corp_code}, year={bsns_year}")
        summary = {
            "total_assets": self.get_account_value(corp_code, bsns_year, "자산총계", fs_div),
            "total_liabilities": self.get_account_value(corp_code, bsns_year, "부채총계", fs_div),
            "total_equity": self.get_account_value(corp_code, bsns_year, "자본총계", fs_div),
            "revenue": self.get_account_value(corp_code, bsns_year, "매출액", fs_div),
            "operating_income": self.get_account_value(corp_code, bsns_year, "영업이익", fs_div),
            "net_income": self.get_account_value(corp_code, bsns_year, "당기순이익", fs_div),
            "ratios": self.get_financial_ratios(corp_code, bsns_year, fs_div),
        }

        return summary

    def get_multi_year_account(
        self,
        corp_code: str,
        account_nm: str,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """Get account values across multiple years.

        Args:
            corp_code: DART corporation code.
            account_nm: Account name to query.
            fs_div: Financial statement division.

        Returns:
            List of year-value pairs.
        """
        # Get all statements for the account
        statements = (
            self.session.query(FinancialStatement)
            .filter(
                FinancialStatement.corp_code == corp_code,
                FinancialStatement.account_nm == account_nm,
                FinancialStatement.fs_div == fs_div,
            )
            .order_by(FinancialStatement.bsns_year.desc())
            .all()
        )

        results = []
        seen_years = set()

        for stmt in statements:
            # Add current year value
            if stmt.bsns_year not in seen_years and stmt.thstrm_amount is not None:
                results.append(
                    {
                        "year": stmt.bsns_year,
                        "value": stmt.thstrm_amount,
                    }
                )
                seen_years.add(stmt.bsns_year)

            # Also extract prior term values if available
            if stmt.frmtrm_amount is not None:
                prior_year = str(int(stmt.bsns_year) - 1)
                if prior_year not in seen_years:
                    results.append(
                        {
                            "year": prior_year,
                            "value": stmt.frmtrm_amount,
                        }
                    )
                    seen_years.add(prior_year)

            if stmt.bfefrmtrm_amount is not None:
                before_prior_year = str(int(stmt.bsns_year) - 2)
                if before_prior_year not in seen_years:
                    results.append(
                        {
                            "year": before_prior_year,
                            "value": stmt.bfefrmtrm_amount,
                        }
                    )
                    seen_years.add(before_prior_year)

        # Sort by year descending
        results.sort(key=lambda x: x["year"], reverse=True)

        return results

    def calculate_yoy_growth(
        self,
        corp_code: str,
        bsns_year: str,
        account_nm: str,
        fs_div: str = "CFS",
    ) -> float | None:
        """Calculate year-over-year growth rate.

        Args:
            corp_code: DART corporation code.
            bsns_year: Business year.
            account_nm: Account name.
            fs_div: Financial statement division.

        Returns:
            Growth rate as percentage, or None.
        """
        current = self.get_account_value(corp_code, bsns_year, account_nm, fs_div, term="thstrm")

        prior = self.get_account_value(corp_code, bsns_year, account_nm, fs_div, term="frmtrm")

        if current is None or prior is None or prior == 0:
            return None

        return ((current - prior) / abs(prior)) * 100

    def get_available_years(
        self,
        corp_code: str,
    ) -> list[str]:
        """Get list of available years for a corporation.

        Args:
            corp_code: DART corporation code.

        Returns:
            List of years sorted descending.
        """
        years = (
            self.session.query(FinancialStatement.bsns_year)
            .filter(FinancialStatement.corp_code == corp_code)
            .distinct()
            .order_by(FinancialStatement.bsns_year.desc())
            .all()
        )

        return [y[0] for y in years]

    def create(self, data: dict[str, Any]) -> FinancialStatement:
        """Create a new financial statement record.

        Args:
            data: Dictionary containing statement data.

        Returns:
            Created FinancialStatement instance.
        """
        logger.debug(f"Creating financial statement: {data.get('corp_code')}, {data.get('bsns_year')}")
        statement = FinancialStatement(**data)
        self.session.add(statement)
        self.session.commit()
        self.session.refresh(statement)
        return statement

    def bulk_create(self, data_list: list[dict[str, Any]]) -> int:
        """Bulk create financial statements.

        Args:
            data_list: List of statement data dictionaries.

        Returns:
            Number of records created.
        """
        count = 0
        for data in data_list:
            statement = FinancialStatement(**data)
            self.session.add(statement)
            count += 1

        self.session.commit()
        return count

    def delete_by_corp(
        self,
        corp_code: str,
        bsns_year: str | None = None,
    ) -> int:
        """Delete financial statements for a corporation.

        Args:
            corp_code: DART corporation code.
            bsns_year: Optional year filter.

        Returns:
            Number of records deleted.
        """
        query = self.session.query(FinancialStatement).filter(
            FinancialStatement.corp_code == corp_code
        )

        if bsns_year:
            query = query.filter(FinancialStatement.bsns_year == bsns_year)

        count = query.count()
        query.delete()
        self.session.commit()
        return count

    def delete_all(self) -> int:
        """Delete all financial statement records.

        Returns:
            Number of records deleted.
        """
        count = self.session.query(FinancialStatement).count()
        self.session.query(FinancialStatement).delete()
        self.session.commit()
        logger.info(f"Deleted all {count} financial statements")
        return count

    def count(self) -> int:
        """Count total financial statement records.

        Returns:
            Total count.
        """
        return self.session.query(FinancialStatement).count()
