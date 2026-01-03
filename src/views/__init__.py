"""Views package - Application pages/screens."""

from src.views.corporations_view import CorporationsView
from src.views.detail_view import DetailView
from src.views.home_view import HomeView
from src.views.settings_view import SettingsView

__all__ = [
    "HomeView",
    "CorporationsView",
    "DetailView",
    "SettingsView",
]
