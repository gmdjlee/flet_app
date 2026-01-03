"""DART-DB Flet Application - Main entry point."""

from collections.abc import Callable

import flet as ft

from src.components.navigation import create_navigation
from src.views.analytics_view import AnalyticsView
from src.views.corporations_view import CorporationsView
from src.views.detail_view import DetailView
from src.views.home_view import HomeView
from src.views.settings_view import SettingsView

# Route definitions
ROUTES: dict[str, Callable[[ft.Page], ft.View]] = {
    "/": HomeView,
    "/corporations": CorporationsView,
    "/analytics": AnalyticsView,
    "/settings": SettingsView,
}

# Navigation index to route mapping
NAV_ROUTES = {
    0: "/",
    1: "/corporations",
    2: "/analytics",  # Placeholder
    3: "/compare",  # Placeholder
    4: "/settings",
}


def configure_page(page: ft.Page) -> None:
    """Configure the page settings and theme.

    Args:
        page: Flet page instance
    """
    page.title = "DART-DB - 전자공시 데이터 분석"
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 800
    page.window.min_height = 600

    # Configure theme
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True,
    )
    page.theme_mode = ft.ThemeMode.LIGHT

    # Configure fonts and padding
    page.padding = 0
    page.spacing = 0


def handle_route_change(page: ft.Page) -> Callable[[ft.ControlEvent], None]:
    """Create route change handler.

    Args:
        page: Flet page instance

    Returns:
        Route change handler function
    """

    def handler(e: ft.ControlEvent) -> None:
        page.views.clear()

        route = page.route
        if route in ROUTES:
            view = ROUTES[route](page)
        else:
            # Default to home
            view = ROUTES["/"](page)

        page.views.append(view)
        page.update()

    return handler


def create_app(page: ft.Page) -> None:
    """Create and configure the main application.

    Args:
        page: Flet page instance
    """
    # Configure page
    configure_page(page)

    # Initialize database
    from src.models.database import init_db

    init_db()

    # Selected navigation index
    selected_index = 0

    def get_nav_index_from_route(route: str) -> int:
        """Get navigation index from route."""
        for idx, r in NAV_ROUTES.items():
            if r == route:
                return idx
        return 0

    def on_nav_change(index: int) -> None:
        """Handle navigation change."""
        nonlocal selected_index
        selected_index = index
        route = NAV_ROUTES.get(index, "/")
        page.go(route)

    def build_layout() -> ft.Control:
        """Build the main layout with navigation."""
        nonlocal selected_index

        # Get current view
        current_route = page.route or "/"
        selected_index = get_nav_index_from_route(current_route)

        # Handle detail routes (/detail/{corp_code})
        if current_route.startswith("/detail/"):
            corp_code = current_route.split("/")[-1]
            current_view = DetailView(page, corp_code)
        else:
            view_class = ROUTES.get(current_route, ROUTES["/"])
            current_view = view_class(page)

        # Create navigation
        nav_rail = create_navigation(
            page,
            on_destination_change=on_nav_change,
            selected_index=selected_index,
        )

        # Main layout
        return ft.Row(
            controls=[
                nav_rail,
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=current_view.controls[0] if current_view.controls else ft.Container(),
                    expand=True,
                ),
            ],
            expand=True,
        )

    def on_route_change(e: ft.ControlEvent) -> None:
        """Handle route changes."""
        page.controls.clear()
        page.add(build_layout())
        page.update()

    # Set up routing
    page.on_route_change = on_route_change

    # Initial render
    page.add(build_layout())


def main() -> None:
    """Application entry point."""
    ft.app(target=create_app)


if __name__ == "__main__":
    main()
