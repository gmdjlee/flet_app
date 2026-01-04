"""Corporation service for managing corporation data in SQLite."""

from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.models.corporation import Corporation
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CorporationService:
    """Service for managing corporation data in the database.

    Provides CRUD operations, search, filtering, and pagination for
    corporation records.

    Attributes:
        session: SQLAlchemy database session.
    """

    def __init__(self, session: Session):
        """Initialize corporation service with database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def create(self, data: dict[str, Any]) -> Corporation:
        """Create a new corporation record.

        Args:
            data: Dictionary containing corporation data.

        Returns:
            Created Corporation instance.
        """
        logger.debug(f"Creating corporation: {data.get('corp_code')}")
        corp = Corporation(**data)
        self.session.add(corp)
        self.session.commit()
        self.session.refresh(corp)
        logger.info(f"Corporation created: {corp.corp_code} ({corp.corp_name})")
        return corp

    def get_by_corp_code(self, corp_code: str) -> Corporation | None:
        """Get corporation by DART corp_code.

        Args:
            corp_code: DART corporation code (8 digits).

        Returns:
            Corporation instance or None if not found.
        """
        return self.session.query(Corporation).filter_by(corp_code=corp_code).first()

    def get_by_stock_code(self, stock_code: str) -> Corporation | None:
        """Get corporation by stock code.

        Args:
            stock_code: Stock code (6 digits).

        Returns:
            Corporation instance or None if not found.
        """
        return self.session.query(Corporation).filter_by(stock_code=stock_code).first()

    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Corporation]:
        """Search corporations by name.

        Args:
            query: Search query string.
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            List of matching Corporation instances.
        """
        offset = (page - 1) * page_size

        # Case-insensitive search using LIKE
        search_pattern = f"%{query}%"
        results = (
            self.session.query(Corporation)
            .filter(Corporation.corp_name.ilike(search_pattern))
            .order_by(Corporation.corp_name)
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return results

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Corporation]:
        """List all corporations with pagination.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            List of Corporation instances.
        """
        offset = (page - 1) * page_size

        return (
            self.session.query(Corporation)
            .order_by(Corporation.corp_name)
            .offset(offset)
            .limit(page_size)
            .all()
        )

    def list_by_market(
        self,
        market: str,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Corporation]:
        """List corporations by market type.

        Args:
            market: Market name (KOSPI, KOSDAQ, KONEX).
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            List of Corporation instances.
        """
        offset = (page - 1) * page_size

        return (
            self.session.query(Corporation)
            .filter(Corporation.market == market)
            .order_by(Corporation.corp_name)
            .offset(offset)
            .limit(page_size)
            .all()
        )

    def list_by_corp_cls(
        self,
        corp_cls: str,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Corporation]:
        """List corporations by corp_cls.

        Args:
            corp_cls: Corporation class (Y=KOSPI, K=KOSDAQ, N=KONEX, E=other).
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            List of Corporation instances.
        """
        offset = (page - 1) * page_size

        return (
            self.session.query(Corporation)
            .filter(Corporation.corp_cls == corp_cls)
            .order_by(Corporation.corp_name)
            .offset(offset)
            .limit(page_size)
            .all()
        )

    def list_listed_only(
        self,
        page: int = 1,
        page_size: int = 100,
    ) -> list[Corporation]:
        """List only listed corporations (with stock_code).

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            List of listed Corporation instances.
        """
        offset = (page - 1) * page_size

        return (
            self.session.query(Corporation)
            .filter(Corporation.stock_code.isnot(None))
            .order_by(Corporation.corp_name)
            .offset(offset)
            .limit(page_size)
            .all()
        )

    def update(
        self,
        corp_code: str,
        data: dict[str, Any],
    ) -> Corporation | None:
        """Update corporation data.

        Args:
            corp_code: DART corporation code.
            data: Dictionary containing fields to update.

        Returns:
            Updated Corporation instance or None if not found.
        """
        corp = self.get_by_corp_code(corp_code)
        if corp is None:
            return None

        for key, value in data.items():
            if hasattr(corp, key):
                setattr(corp, key, value)

        self.session.commit()
        self.session.refresh(corp)
        return corp

    def upsert(self, data: dict[str, Any]) -> Corporation:
        """Insert or update corporation (upsert).

        Args:
            data: Dictionary containing corporation data.
                  Must include 'corp_code'.

        Returns:
            Created or updated Corporation instance.
        """
        corp_code = data.get("corp_code")
        if not corp_code:
            logger.error("corp_code is required for upsert")
            raise ValueError("corp_code is required for upsert")

        try:
            existing = self.get_by_corp_code(corp_code)

            if existing:
                # Update existing record - skip None values to preserve existing data
                for key, value in data.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                self.session.commit()
                self.session.refresh(existing)
                logger.debug(f"Corporation updated: {corp_code}")
                return existing
            else:
                # Create new record - filter out None values for NOT NULL columns
                filtered_data = {k: v for k, v in data.items() if v is not None}
                # Ensure required fields have defaults
                if "corp_cls" not in filtered_data:
                    filtered_data["corp_cls"] = "E"
                return self.create(filtered_data)
        except Exception as e:
            logger.error(f"Failed to upsert corporation {corp_code}: {e}")
            self.session.rollback()
            raise

    def bulk_upsert(self, corps_data: list[dict[str, Any]]) -> int:
        """Bulk upsert multiple corporations.

        Args:
            corps_data: List of corporation data dictionaries.

        Returns:
            Number of records processed.
        """
        count = 0
        for data in corps_data:
            self.upsert(data)
            count += 1

        return count

    def delete(self, corp_code: str) -> bool:
        """Delete corporation by corp_code.

        Args:
            corp_code: DART corporation code.

        Returns:
            True if deleted, False if not found.
        """
        corp = self.get_by_corp_code(corp_code)
        if corp is None:
            logger.warning(f"Corporation not found for deletion: {corp_code}")
            return False

        self.session.delete(corp)
        self.session.commit()
        logger.info(f"Corporation deleted: {corp_code}")
        return True

    def delete_all(self) -> int:
        """Delete all corporation records.

        Returns:
            Number of records deleted.
        """
        count = self.session.query(Corporation).count()
        self.session.query(Corporation).delete()
        self.session.commit()
        logger.info(f"Deleted all {count} corporations")
        return count

    def count(self, listed_only: bool = False) -> int:
        """Count total corporations.

        Args:
            listed_only: If True, count only listed corporations.

        Returns:
            Total count.
        """
        query = self.session.query(func.count(Corporation.corp_code))

        if listed_only:
            query = query.filter(Corporation.stock_code.isnot(None))

        return query.scalar() or 0

    def get_recent(self, limit: int = 10) -> list[Corporation]:
        """Get recently updated corporations.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of recently updated Corporation instances.
        """
        return (
            self.session.query(Corporation)
            .order_by(Corporation.updated_at.desc())
            .limit(limit)
            .all()
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get corporation statistics by market.

        Returns:
            Dictionary containing statistics.
        """
        total = self.count()

        # Count by market
        market_counts = (
            self.session.query(
                Corporation.market,
                func.count(Corporation.corp_code),
            )
            .filter(Corporation.market.isnot(None))
            .group_by(Corporation.market)
            .all()
        )

        by_market = dict(market_counts)

        # Count by corp_cls
        cls_counts = (
            self.session.query(
                Corporation.corp_cls,
                func.count(Corporation.corp_code),
            )
            .group_by(Corporation.corp_cls)
            .all()
        )

        by_cls = dict(cls_counts)

        # Count listed vs unlisted
        listed = self.count(listed_only=True)

        return {
            "total": total,
            "listed": listed,
            "unlisted": total - listed,
            "by_market": by_market,
            "by_corp_cls": by_cls,
        }

    def search_by_multiple_fields(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Corporation]:
        """Search corporations by multiple fields.

        Searches corp_name, stock_code, and corp_code.

        Args:
            query: Search query string.
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            List of matching Corporation instances.
        """
        offset = (page - 1) * page_size
        search_pattern = f"%{query}%"

        results = (
            self.session.query(Corporation)
            .filter(
                or_(
                    Corporation.corp_name.ilike(search_pattern),
                    Corporation.stock_code.ilike(search_pattern),
                    Corporation.corp_code.ilike(search_pattern),
                )
            )
            .order_by(Corporation.corp_name)
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return results
