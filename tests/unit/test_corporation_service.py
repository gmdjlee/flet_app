"""Tests for Corporation service."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base
from src.models.corporation import Corporation
from src.services.corporation_service import CorporationService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_corporations():
    """Sample corporation data for testing."""
    return [
        Corporation(
            corp_code="00126380",
            corp_name="삼성전자",
            stock_code="005930",
            corp_cls="Y",
            market="KOSPI",
            ceo_nm="한종희",
        ),
        Corporation(
            corp_code="00164779",
            corp_name="SK하이닉스",
            stock_code="000660",
            corp_cls="Y",
            market="KOSPI",
            ceo_nm="곽노정",
        ),
        Corporation(
            corp_code="00126389",
            corp_name="삼성SDI",
            stock_code="006400",
            corp_cls="Y",
            market="KOSPI",
            ceo_nm="최윤호",
        ),
        Corporation(
            corp_code="00413046",
            corp_name="카카오",
            stock_code="035720",
            corp_cls="K",
            market="KOSDAQ",
            ceo_nm="홍은택",
        ),
    ]


class TestCorporationService:
    """Test cases for CorporationService."""

    def test_create_corporation(self, db_session):
        """Should create a new corporation."""
        service = CorporationService(db_session)

        corp_data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
        }

        result = service.create(corp_data)

        assert result.corp_code == "00126380"
        assert result.corp_name == "삼성전자"

    def test_get_by_corp_code(self, db_session, sample_corporations):
        """Should get corporation by corp_code."""
        service = CorporationService(db_session)

        # Add sample data
        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        result = service.get_by_corp_code("00126380")

        assert result is not None
        assert result.corp_name == "삼성전자"

    def test_get_by_stock_code(self, db_session, sample_corporations):
        """Should get corporation by stock_code."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        result = service.get_by_stock_code("005930")

        assert result is not None
        assert result.corp_name == "삼성전자"
        assert result.stock_code == "005930"

    def test_get_nonexistent_corporation(self, db_session):
        """Should return None for non-existent corporation."""
        service = CorporationService(db_session)

        result = service.get_by_corp_code("99999999")

        assert result is None

    def test_search_by_name(self, db_session, sample_corporations):
        """Should search corporations by name."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        results = service.search("삼성")

        assert len(results) == 2
        for result in results:
            assert "삼성" in result.corp_name

    def test_search_by_partial_name(self, db_session, sample_corporations):
        """Should search with partial name match."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        results = service.search("전자")

        assert len(results) == 1
        assert results[0].corp_name == "삼성전자"

    def test_search_case_insensitive(self, db_session, sample_corporations):
        """Search should be case-insensitive for English names."""
        service = CorporationService(db_session)

        # Add corporation with English name
        corp = Corporation(
            corp_code="00999999",
            corp_name="ABC Company",
            stock_code="123456",
            corp_cls="Y",
        )
        db_session.add(corp)
        db_session.commit()

        results = service.search("abc")

        assert len(results) == 1
        assert results[0].corp_name == "ABC Company"

    def test_list_all(self, db_session, sample_corporations):
        """Should list all corporations."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        results = service.list_all()

        assert len(results) == 4

    def test_list_with_pagination(self, db_session, sample_corporations):
        """Should support pagination."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        # Page 1 with 2 items
        page1 = service.list_all(page=1, page_size=2)
        assert len(page1) == 2

        # Page 2 with 2 items
        page2 = service.list_all(page=2, page_size=2)
        assert len(page2) == 2

        # Different items on each page
        assert page1[0].corp_code != page2[0].corp_code

    def test_filter_by_market(self, db_session, sample_corporations):
        """Should filter corporations by market type."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        kospi_results = service.list_by_market("KOSPI")
        kosdaq_results = service.list_by_market("KOSDAQ")

        assert len(kospi_results) == 3
        assert len(kosdaq_results) == 1
        assert all(c.market == "KOSPI" for c in kospi_results)
        assert all(c.market == "KOSDAQ" for c in kosdaq_results)

    def test_filter_by_corp_cls(self, db_session, sample_corporations):
        """Should filter corporations by corp_cls (Y/K/N/E)."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        kospi_results = service.list_by_corp_cls("Y")  # KOSPI
        kosdaq_results = service.list_by_corp_cls("K")  # KOSDAQ

        assert len(kospi_results) == 3
        assert len(kosdaq_results) == 1

    def test_list_listed_corporations(self, db_session, sample_corporations):
        """Should list only listed corporations (with stock_code)."""
        service = CorporationService(db_session)

        # Add unlisted corporation
        unlisted = Corporation(
            corp_code="00888888",
            corp_name="비상장회사",
            stock_code=None,
            corp_cls="E",
        )
        sample_corporations.append(unlisted)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        listed = service.list_listed_only()

        assert len(listed) == 4  # Excludes the unlisted one
        assert all(c.stock_code is not None for c in listed)

    def test_update_corporation(self, db_session, sample_corporations):
        """Should update corporation data."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        updated = service.update(
            "00126380",
            {"ceo_nm": "새로운 CEO", "hm_url": "https://www.samsung.com"}
        )

        assert updated is not None
        assert updated.ceo_nm == "새로운 CEO"
        assert updated.hm_url == "https://www.samsung.com"

    def test_upsert_corporation(self, db_session):
        """Should insert or update corporation (upsert)."""
        service = CorporationService(db_session)

        # First upsert - should insert
        corp_data = {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
        }
        result1 = service.upsert(corp_data)
        assert result1.corp_name == "삼성전자"

        # Second upsert - should update
        corp_data["ceo_nm"] = "새로운 CEO"
        result2 = service.upsert(corp_data)
        assert result2.ceo_nm == "새로운 CEO"

        # Should be same record
        count = db_session.query(Corporation).filter_by(corp_code="00126380").count()
        assert count == 1

    def test_bulk_upsert(self, db_session):
        """Should bulk upsert multiple corporations."""
        service = CorporationService(db_session)

        corps_data = [
            {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930", "corp_cls": "Y"},
            {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660", "corp_cls": "Y"},
            {"corp_code": "00126389", "corp_name": "삼성SDI", "stock_code": "006400", "corp_cls": "Y"},
        ]

        count = service.bulk_upsert(corps_data)

        assert count == 3
        assert db_session.query(Corporation).count() == 3

    def test_delete_corporation(self, db_session, sample_corporations):
        """Should delete corporation."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        deleted = service.delete("00126380")

        assert deleted is True
        assert service.get_by_corp_code("00126380") is None

    def test_count_corporations(self, db_session, sample_corporations):
        """Should count total corporations."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        total = service.count()
        listed = service.count(listed_only=True)

        assert total == 4
        assert listed == 4  # All sample corps are listed

    def test_get_recent_corporations(self, db_session, sample_corporations):
        """Should get recently updated corporations."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        recent = service.get_recent(limit=2)

        assert len(recent) == 2

    def test_search_with_pagination(self, db_session, sample_corporations):
        """Should search with pagination support."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        page1 = service.search("성", page=1, page_size=1)
        page2 = service.search("성", page=2, page_size=1)

        assert len(page1) == 1
        assert len(page2) == 1
        assert page1[0].corp_code != page2[0].corp_code

    def test_get_statistics(self, db_session, sample_corporations):
        """Should return market statistics."""
        service = CorporationService(db_session)

        for corp in sample_corporations:
            db_session.add(corp)
        db_session.commit()

        stats = service.get_statistics()

        assert "total" in stats
        assert "by_market" in stats
        assert stats["total"] == 4
        assert stats["by_market"]["KOSPI"] == 3
        assert stats["by_market"]["KOSDAQ"] == 1
