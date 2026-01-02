"""Integration tests for CorporationsView."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import flet as ft

from src.views.corporations_view import CorporationsView
from src.components.search_bar import SearchBar
from src.components.corporation_card import CorporationCard
from src.models.corporation import Corporation
from src.services.corporation_service import CorporationService


class TestCorporationsView:
    """Test cases for CorporationsView."""

    def test_view_initialization(self, mock_page):
        """Test that CorporationsView initializes correctly."""
        view = CorporationsView(mock_page)

        assert view._page_ref == mock_page
        assert view.current_page == 1
        assert view.items_per_page == 20
        assert view.selected_market == "ALL"
        assert view.search_query == ""

    def test_search_field_exists(self, mock_page):
        """Test that search field is present."""
        view = CorporationsView(mock_page)

        assert hasattr(view, "search_bar")
        assert view.search_bar is not None

    def test_search_filters_list(self, mock_page, test_db):
        """Test that search filters the corporation list."""
        # Setup: Create test corporations
        service = CorporationService(test_db)
        service.create({
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "market": "KOSPI",
        })
        service.create({
            "corp_code": "00164779",
            "corp_name": "SK하이닉스",
            "stock_code": "000660",
            "corp_cls": "Y",
            "market": "KOSPI",
        })
        service.create({
            "corp_code": "00401731",
            "corp_name": "LG전자",
            "stock_code": "066570",
            "corp_cls": "Y",
            "market": "KOSPI",
        })

        view = CorporationsView(mock_page, session=test_db)

        # Act: Perform search
        view.search_query = "삼성"
        view._perform_search()

        # Assert: Only matching corporations are shown
        assert len(view.corporations) == 1
        assert view.corporations[0].corp_name == "삼성전자"

    def test_pagination_works(self, mock_page, test_db):
        """Test that pagination works correctly."""
        # Setup: Create 25 corporations (more than one page)
        service = CorporationService(test_db)
        for i in range(25):
            service.create({
                "corp_code": f"0012638{i:02d}",
                "corp_name": f"테스트기업{i:02d}",
                "stock_code": f"00593{i:01d}",
                "corp_cls": "Y",
                "market": "KOSPI",
            })

        view = CorporationsView(mock_page, session=test_db)
        view.items_per_page = 20

        # Initial page
        assert view.current_page == 1
        view._load_corporations()
        assert len(view.corporations) == 20

        # Go to next page
        view._next_page(None)
        assert view.current_page == 2
        assert len(view.corporations) == 5  # Remaining 5 items

    def test_prev_page_disabled_on_first_page(self, mock_page):
        """Test that previous page button is disabled on first page."""
        view = CorporationsView(mock_page)

        assert view.current_page == 1
        view._prev_page(None)
        assert view.current_page == 1  # Should not go below 1

    def test_market_filter_works(self, mock_page, test_db):
        """Test that market filter works correctly."""
        # Setup: Create corporations in different markets
        service = CorporationService(test_db)
        service.create({
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "market": "KOSPI",
        })
        service.create({
            "corp_code": "00293886",
            "corp_name": "카카오",
            "stock_code": "035720",
            "corp_cls": "K",
            "market": "KOSDAQ",
        })

        view = CorporationsView(mock_page, session=test_db)

        # Filter by KOSPI
        view._on_filter_change("KOSPI")
        assert len(view.corporations) == 1
        assert view.corporations[0].corp_name == "삼성전자"

        # Filter by KOSDAQ
        view._on_filter_change("KOSDAQ")
        assert len(view.corporations) == 1
        assert view.corporations[0].corp_name == "카카오"

        # Filter all
        view._on_filter_change("ALL")
        assert len(view.corporations) == 2

    def test_loading_state_displayed(self, mock_page):
        """Test that loading state is shown during data fetch."""
        view = CorporationsView(mock_page)

        assert hasattr(view, "is_loading")
        assert hasattr(view, "loading_indicator")

    def test_empty_state_displayed(self, mock_page, test_db):
        """Test that empty state is shown when no corporations."""
        view = CorporationsView(mock_page, session=test_db)
        view._load_corporations()

        assert len(view.corporations) == 0
        # Empty state should be displayed

    def test_total_count_displayed(self, mock_page, test_db):
        """Test that total corporation count is displayed."""
        service = CorporationService(test_db)
        for i in range(5):
            service.create({
                "corp_code": f"0012638{i:02d}",
                "corp_name": f"테스트기업{i:02d}",
                "stock_code": f"00593{i:01d}",
                "corp_cls": "Y",
                "market": "KOSPI",
            })

        view = CorporationsView(mock_page, session=test_db)
        view._load_corporations()

        assert view.total_count == 5


class TestSearchBar:
    """Test cases for SearchBar component."""

    def test_search_bar_initialization(self, mock_page):
        """Test SearchBar initializes correctly."""
        on_search = MagicMock()
        search_bar = SearchBar(on_search=on_search)

        assert search_bar is not None
        assert hasattr(search_bar, "search_field")

    def test_search_bar_on_submit(self, mock_page):
        """Test SearchBar triggers callback on submit."""
        on_search = MagicMock()
        search_bar = SearchBar(on_search=on_search)

        search_bar.search_field.value = "삼성"
        search_bar._on_submit(None)

        on_search.assert_called_once_with("삼성")

    def test_search_bar_clear(self, mock_page):
        """Test SearchBar clears input."""
        on_search = MagicMock()
        search_bar = SearchBar(on_search=on_search)

        search_bar.search_field.value = "삼성"
        search_bar._on_clear(None)

        assert search_bar.search_field.value == ""

    def test_recent_searches_stored(self, mock_page):
        """Test that recent searches are stored."""
        on_search = MagicMock()
        search_bar = SearchBar(on_search=on_search, max_recent=5)

        search_bar.add_recent_search("삼성")
        search_bar.add_recent_search("SK")

        assert "삼성" in search_bar.recent_searches
        assert "SK" in search_bar.recent_searches

    def test_recent_searches_limit(self, mock_page):
        """Test that recent searches are limited."""
        on_search = MagicMock()
        search_bar = SearchBar(on_search=on_search, max_recent=3)

        search_bar.add_recent_search("검색1")
        search_bar.add_recent_search("검색2")
        search_bar.add_recent_search("검색3")
        search_bar.add_recent_search("검색4")

        assert len(search_bar.recent_searches) == 3
        assert "검색1" not in search_bar.recent_searches
        assert "검색4" in search_bar.recent_searches


class TestCorporationCard:
    """Test cases for CorporationCard component."""

    def test_card_initialization(self, test_db):
        """Test CorporationCard initializes correctly."""
        service = CorporationService(test_db)
        corp = service.create({
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "market": "KOSPI",
        })

        on_click = MagicMock()
        card = CorporationCard(corporation=corp, on_click=on_click)

        assert card is not None
        assert card.corporation == corp

    def test_card_displays_info(self, test_db):
        """Test CorporationCard displays corporation info."""
        service = CorporationService(test_db)
        corp = service.create({
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "market": "KOSPI",
        })

        on_click = MagicMock()
        card = CorporationCard(corporation=corp, on_click=on_click)

        # Card should contain corp_name and stock_code display
        assert hasattr(card, "content")

    def test_card_click_callback(self, test_db):
        """Test CorporationCard triggers callback on click."""
        service = CorporationService(test_db)
        corp = service.create({
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "market": "KOSPI",
        })

        on_click = MagicMock()
        card = CorporationCard(corporation=corp, on_click=on_click)
        card._on_click(None)

        on_click.assert_called_once_with(corp)

    def test_card_market_badge(self, test_db):
        """Test CorporationCard shows market badge."""
        service = CorporationService(test_db)
        corp = service.create({
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "market": "KOSPI",
        })

        on_click = MagicMock()
        card = CorporationCard(corporation=corp, on_click=on_click)

        # Card should show market badge
        assert hasattr(card, "market_badge")


class TestResponsiveLayout:
    """Test cases for responsive layout."""

    def test_wide_layout(self, mock_page):
        """Test layout on wide screens."""
        mock_page.width = 1200
        view = CorporationsView(mock_page)

        # Should use grid layout
        assert view.grid_columns >= 3

    def test_narrow_layout(self, mock_page):
        """Test layout on narrow screens."""
        mock_page.width = 600
        view = CorporationsView(mock_page)

        # Should use list layout
        assert view.grid_columns <= 2
