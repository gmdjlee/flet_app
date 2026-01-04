"""Navigation component for the application."""

from collections.abc import Callable
from typing import Any

import flet as ft


def create_navigation(
    page: ft.Page,
    on_destination_change: Callable[[int], Any] | None = None,
    selected_index: int = 0,
) -> ft.NavigationRail:
    """Create the main navigation rail component.

    Args:
        page: Flet page instance
        on_destination_change: Callback when navigation destination changes (sync or async)
        selected_index: Currently selected index

    Returns:
        NavigationRail component
    """

    async def handle_change(e: ft.ControlEvent) -> None:
        if on_destination_change:
            await on_destination_change(e.control.selected_index)

    nav_rail = ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        min_extended_width=180,
        extended=False,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="홈",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.BUSINESS_OUTLINED,
                selected_icon=ft.Icons.BUSINESS,
                label="기업",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ANALYTICS_OUTLINED,
                selected_icon=ft.Icons.ANALYTICS,
                label="분석",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.COMPARE_ARROWS_OUTLINED,
                selected_icon=ft.Icons.COMPARE_ARROWS,
                label="비교",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="설정",
            ),
        ],
        on_change=handle_change,
    )

    return nav_rail


def create_mobile_navigation(
    page: ft.Page,
    on_destination_change: Callable[[int], Any] | None = None,
    selected_index: int = 0,
) -> ft.NavigationBar:
    """Create the mobile navigation bar component.

    Args:
        page: Flet page instance
        on_destination_change: Callback when navigation destination changes (sync or async)
        selected_index: Currently selected index

    Returns:
        NavigationBar component for mobile devices
    """

    async def handle_change(e: ft.ControlEvent) -> None:
        if on_destination_change:
            await on_destination_change(e.control.selected_index)

    nav_bar = ft.NavigationBar(
        selected_index=selected_index,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="홈",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.BUSINESS_OUTLINED,
                selected_icon=ft.Icons.BUSINESS,
                label="기업",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ANALYTICS_OUTLINED,
                selected_icon=ft.Icons.ANALYTICS,
                label="분석",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="설정",
            ),
        ],
        on_change=handle_change,
    )

    return nav_bar
