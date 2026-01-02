"""Financial Statement model for storing financial data."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class FinancialStatement(Base):
    """Financial Statement model for storing financial data.

    Attributes:
        id: Auto-incremented primary key
        corp_code: DART corporation code (8 digits)
        bsns_year: Business year (YYYY)
        reprt_code: Report code (11011=사업보고서, 11012=반기, 11013=1분기, 11014=3분기)
        fs_div: Financial statement division (CFS=연결, OFS=별도)
        sj_div: Statement division (BS=재무상태표, IS=손익계산서, etc)
        account_id: Account ID (IFRS taxonomy)
        account_nm: Account name in Korean
        account_detail: Account detail/sub-account
        thstrm_nm: Current term name
        thstrm_amount: Current term amount
        frmtrm_nm: Prior term name
        frmtrm_amount: Prior term amount
        bfefrmtrm_nm: Before prior term name
        bfefrmtrm_amount: Before prior term amount
        ord: Order in statement
        currency: Currency code (KRW, USD, etc)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "financial_statements"

    # Primary key - Use Integer for SQLite autoincrement compatibility
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Corporation and report identifiers
    corp_code: Mapped[str] = mapped_column(
        String(8), ForeignKey("corporations.corp_code"), nullable=False, index=True
    )
    bsns_year: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    reprt_code: Mapped[str] = mapped_column(String(5), nullable=False)
    fs_div: Mapped[str] = mapped_column(String(3), nullable=False)
    sj_div: Mapped[str] = mapped_column(String(10), nullable=False)

    # Account info
    account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    account_nm: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    account_detail: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Term names and amounts
    thstrm_nm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    thstrm_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    frmtrm_nm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    frmtrm_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bfefrmtrm_nm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bfefrmtrm_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Additional info
    ord: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="KRW")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Indexes
    __table_args__ = (
        Index("ix_fs_corp_year", "corp_code", "bsns_year"),
        Index("ix_fs_account", "corp_code", "bsns_year", "sj_div", "account_nm"),
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialStatement(corp_code='{self.corp_code}', "
            f"year='{self.bsns_year}', account='{self.account_nm}')>"
        )

    @property
    def report_type_name(self) -> str:
        """Get display name for report type."""
        report_names = {
            "11011": "사업보고서",
            "11012": "반기보고서",
            "11013": "1분기보고서",
            "11014": "3분기보고서",
        }
        return report_names.get(self.reprt_code, "기타")

    @property
    def statement_type_name(self) -> str:
        """Get display name for statement type."""
        statement_names = {
            "BS": "재무상태표",
            "IS": "손익계산서",
            "CIS": "포괄손익계산서",
            "CF": "현금흐름표",
            "SCE": "자본변동표",
        }
        return statement_names.get(self.sj_div, self.sj_div)

    @property
    def is_consolidated(self) -> bool:
        """Check if this is consolidated financial statement."""
        return self.fs_div == "CFS"

    def format_amount(self, amount: int | None, unit: str = "억원") -> str:
        """Format amount with unit.

        Args:
            amount: Amount in KRW
            unit: Display unit ("억원" or "만원")

        Returns:
            Formatted amount string
        """
        if amount is None:
            return "-"

        if unit == "억원":
            value = amount / 100_000_000
            return f"{value:,.1f}"
        elif unit == "만원":
            value = amount / 10_000
            return f"{value:,.0f}"
        else:
            return f"{amount:,}"
