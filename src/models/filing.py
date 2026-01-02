"""Filing model for storing DART disclosure reports."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class Filing(Base):
    """Filing model representing a DART disclosure report.

    Attributes:
        rcept_no: Receipt number (14 digits) - unique identifier
        corp_code: DART corporation code (8 digits)
        corp_name: Corporation name at the time of filing
        stock_code: Stock code at the time of filing
        corp_cls: Corporation class at the time of filing
        report_nm: Report name
        rcept_dt: Receipt date (YYYYMMDD)
        flr_nm: Filer name
        rm: Remarks (연결, 정정 등)
        created_at: Record creation timestamp
    """

    __tablename__ = "filings"

    # Primary key and identifiers
    rcept_no: Mapped[str] = mapped_column(String(14), primary_key=True)
    corp_code: Mapped[str] = mapped_column(
        String(8), ForeignKey("corporations.corp_code"), nullable=False, index=True
    )
    corp_name: Mapped[str] = mapped_column(String(200), nullable=False)
    stock_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    corp_cls: Mapped[str | None] = mapped_column(String(1), nullable=True)

    # Report info
    report_nm: Mapped[str] = mapped_column(String(500), nullable=False)
    rcept_dt: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    flr_nm: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rm: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (Index("ix_filings_corp_rcept", "corp_code", "rcept_dt"),)

    def __repr__(self) -> str:
        return f"<Filing(rcept_no='{self.rcept_no}', report_nm='{self.report_nm}')>"

    @property
    def is_annual_report(self) -> bool:
        """Check if this is an annual report (사업보고서)."""
        return "사업보고서" in self.report_nm

    @property
    def is_quarterly_report(self) -> bool:
        """Check if this is a quarterly report (분기보고서)."""
        return "분기보고서" in self.report_nm or "반기보고서" in self.report_nm

    @property
    def is_consolidated(self) -> bool:
        """Check if this is a consolidated report (연결)."""
        return self.rm is not None and "연결" in self.rm

    @property
    def receipt_date(self) -> datetime | None:
        """Parse receipt date as datetime object."""
        if self.rcept_dt and len(self.rcept_dt) == 8:
            try:
                return datetime.strptime(self.rcept_dt, "%Y%m%d")
            except ValueError:
                return None
        return None
