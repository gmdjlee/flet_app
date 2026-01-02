"""Shared test fixtures and configuration."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def mock_page():
    """Create a mock Flet Page for testing."""
    import flet as ft

    page = MagicMock(spec=ft.Page)
    page.platform = ft.PagePlatform.WINDOWS
    page.width = 1200
    page.height = 800
    page.update = MagicMock()
    page.views = []
    page.route = "/"
    page.go = MagicMock()

    # Mock window object
    page.window = MagicMock()
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 800
    page.window.min_height = 600

    # Mock theme
    page.theme = None
    page.theme_mode = None
    page.title = None
    page.padding = None
    page.spacing = None

    return page


@pytest.fixture
def test_db():
    """Create in-memory SQLite for testing."""
    from src.models.database import Base, get_engine

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_dart_api():
    """Mock DART API responses."""
    mock = AsyncMock()
    mock.get_corporation_list.return_value = [
        {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930"},
        {"corp_code": "00164779", "corp_name": "SK하이닉스", "stock_code": "000660"},
    ]
    return mock
