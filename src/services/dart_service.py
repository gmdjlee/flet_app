"""DART API service for fetching corporate disclosure data."""

import asyncio
import os
from typing import Any

from src.utils.logging_config import get_logger

try:
    import dart_fss
except ImportError:
    dart_fss = None  # Will be mocked in tests

logger = get_logger(__name__)


class DartServiceError(Exception):
    """Exception raised for DART service errors."""

    pass


class DartService:
    """Service for interacting with DART Open API via dart-fss library.

    This service provides methods to fetch corporation lists, company info,
    and financial statements from the DART (Data Analysis, Retrieval and
    Transfer System) Open API.

    Attributes:
        api_key: DART API key for authentication.
    """

    # Valid report codes
    VALID_REPORT_CODES = {"11011", "11012", "11013", "11014"}

    # Market type mapping
    MARKET_TO_CORP_CLS = {
        "KOSPI": "Y",
        "KOSDAQ": "K",
        "KONEX": "N",
        "ETC": "E",
    }

    def __init__(self, api_key: str | None = None):
        """Initialize DART service with API key.

        Args:
            api_key: DART API key. If not provided, reads from DART_API_KEY
                     environment variable.

        Raises:
            ValueError: If API key is not provided and not in environment.
        """
        self.api_key = api_key or os.getenv("DART_API_KEY")

        if not self.api_key:
            logger.error("DART API key not provided and not found in environment")
            raise ValueError(
                "API key is required. Provide api_key parameter or set DART_API_KEY environment variable."
            )

        # Initialize dart-fss with API key
        if dart_fss is not None:
            dart_fss.set_api_key(self.api_key)
            logger.info("DART service initialized with API key")

    def _corp_to_dict(self, corp: Any) -> dict[str, Any]:
        """Convert Corp object to dictionary.

        Args:
            corp: Corp object from dart-fss or dict.

        Returns:
            Dictionary with corporation data.
        """
        # If already a dict, return as-is
        if isinstance(corp, dict):
            return corp

        # Convert Corp object attributes to dict
        # corp_cls defaults to "E" (etc) if not available
        corp_cls = getattr(corp, "corp_cls", None)
        if not corp_cls:
            corp_cls = "E"

        return {
            "corp_code": getattr(corp, "corp_code", None),
            "corp_name": getattr(corp, "corp_name", None),
            "stock_code": getattr(corp, "stock_code", None),
            "corp_cls": corp_cls,
            "modify_date": getattr(corp, "modify_date", None),
        }

    async def get_corporation_list(self, market: str | None = None) -> list[dict[str, Any]]:
        """Fetch list of all corporations from DART.

        Args:
            market: Optional market filter ("KOSPI", "KOSDAQ", "KONEX", "ETC").

        Returns:
            List of corporation dictionaries.

        Raises:
            DartServiceError: If API call fails.
        """
        logger.info(f"Fetching corporation list from DART API (market={market})")
        try:
            # Run synchronous dart-fss call in thread pool
            loop = asyncio.get_event_loop()
            corps = await loop.run_in_executor(None, dart_fss.get_corp_list)

            # Convert Corp objects to dicts
            corps = [self._corp_to_dict(c) for c in corps]
            logger.debug(f"Retrieved {len(corps)} corporations from DART")

            # Filter by market if specified
            if market and market in self.MARKET_TO_CORP_CLS:
                target_cls = self.MARKET_TO_CORP_CLS[market]
                corps = [c for c in corps if c.get("corp_cls") == target_cls]
                logger.debug(f"Filtered to {len(corps)} corporations for market {market}")

            logger.info(f"Corporation list fetched successfully: {len(corps)} corporations")
            return corps

        except Exception as e:
            logger.error(f"Failed to fetch corporation list: {e}")
            raise DartServiceError(f"Failed to fetch corporation list: {e}") from e

    async def get_corporation_info(self, corp_code: str) -> dict[str, Any]:
        """Fetch detailed information for a specific corporation.

        Args:
            corp_code: DART corporation code (8 digits).

        Returns:
            Dictionary containing corporation details.

        Raises:
            DartServiceError: If API call fails.
            ValueError: If corp_code is invalid.
        """
        if not self.validate_corp_code(corp_code):
            logger.warning(f"Invalid corp_code format: {corp_code}")
            raise ValueError(f"Invalid corp_code format: {corp_code}")

        logger.debug(f"Fetching corporation info for {corp_code}")
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: dart_fss.get_corp_info(corp_code))
            logger.debug(f"Corporation info fetched for {corp_code}")
            return info

        except Exception as e:
            logger.error(f"Failed to fetch corporation info for {corp_code}: {e}")
            raise DartServiceError(f"Failed to fetch corporation info for {corp_code}: {e}") from e

    # Report code to pblntf_detail_ty mapping for XBRL extraction
    REPORT_CODE_TO_PBLNTF = {
        "11011": "a001",  # 사업보고서
        "11012": "a002",  # 반기보고서
        "11013": "a003",  # 1분기보고서
        "11014": "a003",  # 3분기보고서
    }

    async def get_financial_statements(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str = "11011",
        fs_div: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch financial statements for a corporation using XBRL extraction.

        Uses dart-fss XBRL extraction via report.xbrl to get financial statements.

        Args:
            corp_code: DART corporation code (8 digits).
            bsns_year: Business year (YYYY format).
            reprt_code: Report code (11011=annual, 11012=semi-annual,
                        11013=Q1, 11014=Q3).
            fs_div: Financial statement division filter (CFS=consolidated,
                    OFS=separate). If None, returns consolidated first, then separate.

        Returns:
            List of financial statement items.

        Raises:
            DartServiceError: If API call fails.
            ValueError: If parameters are invalid.
        """
        if not self.validate_corp_code(corp_code):
            logger.warning(f"Invalid corp_code format: {corp_code}")
            raise ValueError(f"Invalid corp_code format: {corp_code}")

        if not self.validate_report_code(reprt_code):
            logger.warning(f"Invalid report code: {reprt_code}")
            raise ValueError(f"Invalid report code: {reprt_code}")

        logger.debug(f"Fetching financial statements for {corp_code}, year={bsns_year}, report={reprt_code}")
        try:
            loop = asyncio.get_event_loop()

            # Extract financial statements using XBRL from report
            def extract_xbrl_data() -> list[dict[str, Any]]:
                # Get corporation list and find target corporation
                corp_list = dart_fss.get_corp_list()
                corp = corp_list.find_by_corp_code(corp_code=corp_code)

                if corp is None:
                    return []

                # Map report code to pblntf_detail_ty
                pblntf_detail_ty = self.REPORT_CODE_TO_PBLNTF.get(reprt_code, "a001")

                # Calculate date range for the business year
                bgn_de = f"{bsns_year}0101"
                end_de = f"{bsns_year}1231"

                # Search for filings (reports)
                reports = corp.search_filings(
                    bgn_de=bgn_de,
                    end_de=end_de,
                    pblntf_detail_ty=pblntf_detail_ty,
                )

                if not reports or len(reports) == 0:
                    return []

                # Get the first (most recent) report
                report = reports[0]

                # Get XBRL data from report
                xbrl = report.xbrl

                if xbrl is None:
                    return []

                # Check if consolidated financial statements exist
                has_consolidated = xbrl.exist_consolidated()

                # Extract all financial statement types
                return self._extract_xbrl_statements(
                    xbrl, bsns_year, reprt_code, fs_div, has_consolidated
                )

            statements = await loop.run_in_executor(None, extract_xbrl_data)
            logger.debug(f"Fetched {len(statements)} financial statement items for {corp_code}")
            return statements

        except Exception as e:
            logger.error(f"Failed to fetch financial statements for {corp_code}: {e}")
            raise DartServiceError(
                f"Failed to fetch financial statements for {corp_code}: {e}"
            ) from e

    def _extract_xbrl_statements(
        self,
        xbrl: Any,
        bsns_year: str,
        reprt_code: str,
        fs_div: str | None,
        has_consolidated: bool,
    ) -> list[dict[str, Any]]:
        """Extract financial statements from XBRL data.

        Args:
            xbrl: XBRL data object from report.xbrl
            bsns_year: Target business year
            reprt_code: Report code (11011=annual, etc.)
            fs_div: Financial statement division filter (CFS/OFS)
            has_consolidated: Whether consolidated statements exist

        Returns:
            List of financial statement items as dictionaries.
        """
        statements = []

        # Define extraction methods and their names
        extraction_methods = [
            ("get_financial_statement", "BS", "재무상태표"),
            ("get_income_statement", "IS", "손익계산서"),
            ("get_income_statement_cis", "CIS", "포괄손익계산서"),
            ("get_cash_flows", "CF", "현금흐름표"),
        ]

        for method_name, sj_div, sj_nm in extraction_methods:
            try:
                # Get the extraction method
                method = getattr(xbrl, method_name, None)
                if method is None:
                    continue

                # Call the method to get list of statements
                fs_list = method()

                if not fs_list:
                    continue

                # Process each statement (consolidated and/or separate)
                for idx, fs_item in enumerate(fs_list):
                    # Determine if this is consolidated (first item) or separate
                    # First item is typically consolidated if exists
                    if has_consolidated:
                        current_fs_div = "CFS" if idx == 0 else "OFS"
                    else:
                        current_fs_div = "OFS"

                    # Filter by fs_div if specified
                    if fs_div and current_fs_div != fs_div:
                        continue

                    # Convert to DataFrame
                    try:
                        df = fs_item.to_DataFrame(show_class=False)
                    except Exception:
                        df = fs_item.to_DataFrame() if hasattr(fs_item, "to_DataFrame") else None

                    if df is None or df.empty:
                        continue

                    # Convert DataFrame rows to statement dictionaries
                    statements.extend(
                        self._dataframe_to_statements(
                            df, sj_div, sj_nm, bsns_year, reprt_code, current_fs_div
                        )
                    )

            except Exception:
                # Skip this statement type if extraction fails
                continue

        return statements

    def _dataframe_to_statements(
        self,
        df: Any,
        sj_div: str,
        sj_nm: str,
        bsns_year: str,
        reprt_code: str,
        fs_div: str,
    ) -> list[dict[str, Any]]:
        """Convert a DataFrame to list of statement dictionaries.

        Args:
            df: Pandas DataFrame with financial data
            sj_div: Statement division code (BS, IS, CIS, CF)
            sj_nm: Statement name in Korean
            bsns_year: Target business year
            reprt_code: Report code (11011=annual, etc.)
            fs_div: Financial statement division (CFS/OFS)

        Returns:
            List of statement dictionaries.
        """
        statements = []

        for idx, row in df.iterrows():
            # Find amount for the target year
            amount = None
            for col in df.columns:
                col_str = str(col)
                if bsns_year in col_str:
                    val = row.get(col)
                    if val is not None and not (isinstance(val, float) and str(val) == "nan"):
                        amount = val
                        break

            # Get account name from index or label column
            if isinstance(idx, tuple):
                account_nm = str(idx[-1]) if idx else ""
            else:
                account_nm = str(idx) if idx else ""

            # Try to get label from row if available
            for label_col in ["label_ko", "concept_id", "account"]:
                if label_col in df.columns:
                    label_val = row.get(label_col)
                    if label_val and str(label_val) != "nan":
                        account_nm = str(label_val)
                        break

            statement = {
                "sj_div": sj_div,
                "sj_nm": sj_nm,
                "account_id": str(idx) if idx else "",
                "account_nm": account_nm,
                "account_detail": "",
                "thstrm_nm": f"{bsns_year}년",
                "thstrm_amount": str(amount) if amount is not None else "",
                "fs_div": fs_div,
                "fs_nm": "연결재무제표" if fs_div == "CFS" else "재무제표",
                "bsns_year": bsns_year,
                "reprt_code": reprt_code,
            }
            statements.append(statement)

        return statements

    async def search_corporations(self, query: str) -> list[dict[str, Any]]:
        """Search corporations by name.

        Args:
            query: Search query string (corporation name).

        Returns:
            List of matching corporations.

        Raises:
            DartServiceError: If API call fails.
        """
        logger.debug(f"Searching corporations with query: {query}")
        try:
            # Fetch all corporations and filter by name
            all_corps = await self.get_corporation_list()

            # Filter by name (case-insensitive)
            query_lower = query.lower()
            results = [c for c in all_corps if query_lower in c.get("corp_name", "").lower()]
            logger.debug(f"Search found {len(results)} matching corporations")

            return results

        except DartServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to search corporations: {e}")
            raise DartServiceError(f"Failed to search corporations: {e}") from e

    async def get_filings(
        self,
        corp_code: str,
        bgn_de: str | None = None,
        end_de: str | None = None,
        pblntf_ty: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch filings (disclosures) for a corporation.

        Args:
            corp_code: DART corporation code (8 digits).
            bgn_de: Start date (YYYYMMDD format).
            end_de: End date (YYYYMMDD format).
            pblntf_ty: Disclosure type filter.

        Returns:
            List of filing dictionaries.

        Raises:
            DartServiceError: If API call fails.
        """
        if not self.validate_corp_code(corp_code):
            logger.warning(f"Invalid corp_code format: {corp_code}")
            raise ValueError(f"Invalid corp_code format: {corp_code}")

        logger.debug(f"Fetching filings for {corp_code}, period={bgn_de}-{end_de}")
        try:
            loop = asyncio.get_event_loop()
            filings = await loop.run_in_executor(
                None,
                lambda: dart_fss.get_disclosure_list(
                    corp_code=corp_code,
                    bgn_de=bgn_de,
                    end_de=end_de,
                    pblntf_ty=pblntf_ty,
                ),
            )
            logger.debug(f"Fetched {len(filings)} filings for {corp_code}")
            return filings

        except Exception as e:
            logger.error(f"Failed to fetch filings for {corp_code}: {e}")
            raise DartServiceError(f"Failed to fetch filings for {corp_code}: {e}") from e

    def validate_corp_code(self, corp_code: str) -> bool:
        """Validate corporation code format.

        Args:
            corp_code: Corporation code to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not corp_code or not isinstance(corp_code, str):
            return False

        # Corp code should be exactly 8 digits
        if len(corp_code) != 8:
            return False

        return corp_code.isdigit()

    def validate_report_code(self, reprt_code: str) -> bool:
        """Validate report code.

        Args:
            reprt_code: Report code to validate.

        Returns:
            True if valid, False otherwise.
        """
        return reprt_code in self.VALID_REPORT_CODES

    @staticmethod
    def get_report_name(reprt_code: str) -> str:
        """Get human-readable report name.

        Args:
            reprt_code: Report code.

        Returns:
            Report name in Korean.
        """
        names = {
            "11011": "사업보고서",
            "11012": "반기보고서",
            "11013": "1분기보고서",
            "11014": "3분기보고서",
        }
        return names.get(reprt_code, "알 수 없음")

    @staticmethod
    def get_market_name(corp_cls: str) -> str:
        """Get market name from corporation class.

        Args:
            corp_cls: Corporation class (Y/K/N/E).

        Returns:
            Market name.
        """
        names = {
            "Y": "KOSPI",
            "K": "KOSDAQ",
            "N": "KONEX",
            "E": "기타",
        }
        return names.get(corp_cls, "기타")
