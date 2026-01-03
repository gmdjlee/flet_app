"""DART API service for fetching corporate disclosure data."""

import asyncio
import os
from typing import Any

try:
    import dart_fss
except ImportError:
    dart_fss = None  # Will be mocked in tests


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
            raise ValueError(
                "API key is required. Provide api_key parameter or set DART_API_KEY environment variable."
            )

        # Initialize dart-fss with API key
        if dart_fss is not None:
            dart_fss.set_api_key(self.api_key)

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
        return {
            "corp_code": getattr(corp, "corp_code", None),
            "corp_name": getattr(corp, "corp_name", None),
            "stock_code": getattr(corp, "stock_code", None),
            "corp_cls": getattr(corp, "corp_cls", None),
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
        try:
            # Run synchronous dart-fss call in thread pool
            loop = asyncio.get_event_loop()
            corps = await loop.run_in_executor(None, dart_fss.get_corp_list)

            # Convert Corp objects to dicts
            corps = [self._corp_to_dict(c) for c in corps]

            # Filter by market if specified
            if market and market in self.MARKET_TO_CORP_CLS:
                target_cls = self.MARKET_TO_CORP_CLS[market]
                corps = [c for c in corps if c.get("corp_cls") == target_cls]

            return corps

        except Exception as e:
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
            raise ValueError(f"Invalid corp_code format: {corp_code}")

        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: dart_fss.get_corp_info(corp_code))
            return info

        except Exception as e:
            raise DartServiceError(f"Failed to fetch corporation info for {corp_code}: {e}") from e

    async def get_financial_statements(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str = "11011",
        fs_div: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch financial statements for a corporation.

        Args:
            corp_code: DART corporation code (8 digits).
            bsns_year: Business year (YYYY format).
            reprt_code: Report code (11011=annual, 11012=semi-annual,
                        11013=Q1, 11014=Q3).
            fs_div: Financial statement division filter (CFS=consolidated,
                    OFS=separate). If None, returns both.

        Returns:
            List of financial statement items.

        Raises:
            DartServiceError: If API call fails.
            ValueError: If parameters are invalid.
        """
        if not self.validate_corp_code(corp_code):
            raise ValueError(f"Invalid corp_code format: {corp_code}")

        if not self.validate_report_code(reprt_code):
            raise ValueError(f"Invalid report code: {reprt_code}")

        try:
            loop = asyncio.get_event_loop()
            statements = await loop.run_in_executor(
                None,
                lambda: dart_fss.get_financial_statement(
                    corp_code=corp_code,
                    bsns_year=bsns_year,
                    reprt_code=reprt_code,
                ),
            )

            # Filter by fs_div if specified
            if fs_div:
                statements = [s for s in statements if s.get("fs_div") == fs_div]

            return statements

        except Exception as e:
            raise DartServiceError(
                f"Failed to fetch financial statements for {corp_code}: {e}"
            ) from e

    async def search_corporations(self, query: str) -> list[dict[str, Any]]:
        """Search corporations by name.

        Args:
            query: Search query string (corporation name).

        Returns:
            List of matching corporations.

        Raises:
            DartServiceError: If API call fails.
        """
        try:
            # Fetch all corporations and filter by name
            all_corps = await self.get_corporation_list()

            # Filter by name (case-insensitive)
            query_lower = query.lower()
            results = [c for c in all_corps if query_lower in c.get("corp_name", "").lower()]

            return results

        except DartServiceError:
            raise
        except Exception as e:
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
            raise ValueError(f"Invalid corp_code format: {corp_code}")

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
            return filings

        except Exception as e:
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
