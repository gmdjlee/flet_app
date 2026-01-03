"""Corporation model for storing company information."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Corporation(Base):
    """Corporation model representing a listed company.

    Attributes:
        corp_code: DART corporation code (8 digits)
        corp_name: Corporation name
        stock_code: Stock code (6 digits, nullable for unlisted)
        corp_cls: Corporation class (Y=KOSPI, K=KOSDAQ, N=KONEX, E=etc)
        market: Market name (KOSPI, KOSDAQ, KONEX)
        modify_date: Last modification date from DART
        ceo_nm: CEO name
        corp_name_eng: Corporation name in English
        jurir_no: Legal registration number
        bizr_no: Business registration number
        adres: Address
        hm_url: Homepage URL
        ir_url: IR page URL
        phn_no: Phone number
        fax_no: Fax number
        induty_code: Industry code
        est_dt: Establishment date
        acc_mt: Fiscal month
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "corporations"

    # Primary key and identifiers
    corp_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    corp_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    stock_code: Mapped[str | None] = mapped_column(String(6), nullable=True, index=True)
    corp_cls: Mapped[str] = mapped_column(String(1), nullable=False, default="E")
    market: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Additional info
    modify_date: Mapped[str | None] = mapped_column(String(8), nullable=True)
    ceo_nm: Mapped[str | None] = mapped_column(String(200), nullable=True)
    corp_name_eng: Mapped[str | None] = mapped_column(String(500), nullable=True)
    jurir_no: Mapped[str | None] = mapped_column(String(13), nullable=True)
    bizr_no: Mapped[str | None] = mapped_column(String(10), nullable=True)
    adres: Mapped[str | None] = mapped_column(Text, nullable=True)
    hm_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ir_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phn_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fax_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    induty_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    est_dt: Mapped[str | None] = mapped_column(String(8), nullable=True)
    acc_mt: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utc_now, onupdate=_utc_now, nullable=False
    )

    # Indexes
    __table_args__ = (
        Index("ix_corporations_corp_cls", "corp_cls"),
        Index("ix_corporations_market", "market"),
    )

    def __repr__(self) -> str:
        return f"<Corporation(corp_code='{self.corp_code}', corp_name='{self.corp_name}')>"

    @property
    def is_listed(self) -> bool:
        """Check if the corporation is listed (has stock code)."""
        return self.stock_code is not None

    @property
    def market_display(self) -> str:
        """Get display name for market type."""
        market_names = {
            "Y": "KOSPI",
            "K": "KOSDAQ",
            "N": "KONEX",
            "E": "기타",
        }
        return market_names.get(self.corp_cls, "기타")
