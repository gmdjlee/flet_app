"""Tests for SQLite database models and operations."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker


class TestDatabase:
    """Database connection and table creation tests."""

    def test_create_tables(self, test_db):
        """Tables should be created correctly."""
        from src.models.database import Base

        engine = test_db.get_bind()
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        assert "corporations" in table_names
        assert "filings" in table_names
        assert "financial_statements" in table_names

    def test_corporation_crud(self, test_db):
        """Basic CRUD operations for Corporation model."""
        from src.models.corporation import Corporation

        # Create
        corp = Corporation(
            corp_code="00126380",
            corp_name="삼성전자",
            stock_code="005930",
            corp_cls="Y",  # KOSPI
            market="KOSPI"
        )
        test_db.add(corp)
        test_db.commit()

        # Read
        found = test_db.query(Corporation).filter_by(corp_code="00126380").first()
        assert found is not None
        assert found.corp_name == "삼성전자"
        assert found.stock_code == "005930"

        # Update
        found.corp_name = "삼성전자(주)"
        test_db.commit()
        updated = test_db.query(Corporation).filter_by(corp_code="00126380").first()
        assert updated.corp_name == "삼성전자(주)"

        # Delete
        test_db.delete(updated)
        test_db.commit()
        deleted = test_db.query(Corporation).filter_by(corp_code="00126380").first()
        assert deleted is None

    def test_filing_crud(self, test_db):
        """Basic CRUD operations for Filing model."""
        from src.models.corporation import Corporation
        from src.models.filing import Filing

        # First create a corporation
        corp = Corporation(
            corp_code="00126380",
            corp_name="삼성전자",
            stock_code="005930",
            corp_cls="Y",
            market="KOSPI"
        )
        test_db.add(corp)
        test_db.commit()

        # Create filing
        filing = Filing(
            rcept_no="20240315000123",
            corp_code="00126380",
            corp_name="삼성전자",
            report_nm="사업보고서",
            rcept_dt="20240315",
            flr_nm="삼성전자",
            rm=""
        )
        test_db.add(filing)
        test_db.commit()

        # Read
        found = test_db.query(Filing).filter_by(rcept_no="20240315000123").first()
        assert found is not None
        assert found.report_nm == "사업보고서"

    def test_financial_statement_crud(self, test_db):
        """Basic CRUD operations for FinancialStatement model."""
        from src.models.corporation import Corporation
        from src.models.financial_statement import FinancialStatement

        # First create a corporation
        corp = Corporation(
            corp_code="00126380",
            corp_name="삼성전자",
            stock_code="005930",
            corp_cls="Y",
            market="KOSPI"
        )
        test_db.add(corp)
        test_db.commit()

        # Create financial statement
        fs = FinancialStatement(
            corp_code="00126380",
            bsns_year="2023",
            reprt_code="11011",  # 사업보고서
            fs_div="CFS",  # 연결재무제표
            sj_div="BS",  # 재무상태표
            account_id="ifrs-full_Assets",
            account_nm="자산총계",
            thstrm_amount=100000000000,
            frmtrm_amount=90000000000,
            bfefrmtrm_amount=85000000000
        )
        test_db.add(fs)
        test_db.commit()

        # Read
        found = test_db.query(FinancialStatement).filter_by(
            corp_code="00126380",
            bsns_year="2023"
        ).first()
        assert found is not None
        assert found.account_nm == "자산총계"
        assert found.thstrm_amount == 100000000000


class TestDatabaseConnection:
    """Database connection utility tests."""

    def test_get_engine_creates_engine(self):
        """get_engine should return a valid SQLAlchemy engine."""
        from src.models.database import get_engine

        engine = get_engine(":memory:")
        assert engine is not None
        assert "sqlite" in str(engine.url)

    def test_get_session_factory(self):
        """get_session should return a valid session."""
        from src.models.database import get_engine, get_session

        engine = get_engine(":memory:")
        session = get_session(engine)
        assert session is not None
        session.close()

    def test_init_db_creates_all_tables(self):
        """init_db should create all tables."""
        from src.models.database import init_db, Base
        from sqlalchemy import inspect

        engine = init_db(":memory:")
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        assert "corporations" in table_names
        assert "filings" in table_names
        assert "financial_statements" in table_names
