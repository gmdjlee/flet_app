"""Sync progress indicator component."""

from collections.abc import Callable
from datetime import datetime

import flet as ft

from src.services.sync_service import SyncProgress, SyncStatus


class SyncProgressIndicator:
    """Reusable sync progress indicator component.

    Shows progress bar, status message, elapsed time, and cancel button.
    """

    def __init__(
        self,
        on_cancel: Callable[[], None] | None = None,
        show_elapsed_time: bool = True,
        show_cancel_button: bool = True,
    ):
        """Initialize SyncProgressIndicator.

        Args:
            on_cancel: Callback when cancel button is clicked.
            show_elapsed_time: Whether to show elapsed time.
            show_cancel_button: Whether to show cancel button.
        """
        self._on_cancel = on_cancel
        self._show_elapsed_time = show_elapsed_time
        self._show_cancel_button = show_cancel_button
        self._start_time: datetime | None = None

        # UI Controls
        self.progress_bar = ft.ProgressBar(
            value=0,
            bar_height=4,
            color=ft.Colors.BLUE,
            bgcolor=ft.Colors.GREY_300,
        )

        self.status_text = ft.Text(
            "",
            size=14,
            weight=ft.FontWeight.W_500,
        )

        self.detail_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
        )

        self.elapsed_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
        )

        self.percentage_text = ft.Text(
            "",
            size=12,
            weight=ft.FontWeight.BOLD,
        )

        self.cancel_button = ft.Button(
            "취소",
            icon=ft.Icons.CANCEL,
            on_click=self._handle_cancel,
            visible=show_cancel_button,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, ft.Colors.GREY_400),
            ),
        )

        self.status_icon = ft.Icon(
            ft.Icons.SYNC,
            size=24,
            color=ft.Colors.BLUE,
        )

        self._container: ft.Container | None = None

    def build(self) -> ft.Control:
        """Build the progress indicator UI.

        Returns:
            Flet Control containing the progress indicator.
        """
        self._container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.status_icon,
                            ft.Column(
                                controls=[
                                    self.status_text,
                                    self.detail_text,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            self.percentage_text,
                        ],
                        spacing=15,
                    ),
                    self.progress_bar,
                    ft.Row(
                        controls=[
                            self.elapsed_text if self._show_elapsed_time else ft.Container(),
                            ft.Container(expand=True),
                            self.cancel_button if self._show_cancel_button else ft.Container(),
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=20,
            bgcolor=ft.Colors.GREY_100,
            border_radius=10,
            visible=False,
        )
        return self._container

    def update(self, progress: SyncProgress) -> None:
        """Update the indicator with new progress.

        Args:
            progress: SyncProgress instance.
        """
        if self._container:
            self._container.visible = True

        # Update progress bar
        if progress.total > 0:
            self.progress_bar.value = progress.current / progress.total
            percentage = int((progress.current / progress.total) * 100)
            self.percentage_text.value = f"{percentage}%"
        else:
            self.progress_bar.value = None  # Indeterminate
            self.percentage_text.value = ""

        # Update status
        self.status_text.value = self._get_status_title(progress.status)
        self.detail_text.value = progress.message

        # Update icon and colors based on status
        self._update_status_appearance(progress.status)

        # Update elapsed time
        if self._show_elapsed_time and progress.started_at:
            if self._start_time is None:
                self._start_time = progress.started_at
            elapsed = progress.elapsed_seconds or 0
            self.elapsed_text.value = self._format_elapsed_time(elapsed)

        # Update cancel button visibility
        is_syncing = progress.status == SyncStatus.SYNCING
        self.cancel_button.visible = self._show_cancel_button and is_syncing

    def _get_status_title(self, status: SyncStatus) -> str:
        """Get display title for status.

        Args:
            status: Sync status.

        Returns:
            Display title string.
        """
        titles = {
            SyncStatus.IDLE: "대기 중",
            SyncStatus.SYNCING: "동기화 중",
            SyncStatus.COMPLETED: "동기화 완료",
            SyncStatus.FAILED: "동기화 실패",
            SyncStatus.CANCELLED: "동기화 취소됨",
        }
        return titles.get(status, "")

    def _update_status_appearance(self, status: SyncStatus) -> None:
        """Update visual appearance based on status.

        Args:
            status: Current sync status.
        """
        if status == SyncStatus.SYNCING:
            self.status_icon.name = ft.Icons.SYNC
            self.status_icon.color = ft.Colors.BLUE
            self.progress_bar.color = ft.Colors.BLUE
        elif status == SyncStatus.COMPLETED:
            self.status_icon.name = ft.Icons.CHECK_CIRCLE
            self.status_icon.color = ft.Colors.GREEN
            self.progress_bar.color = ft.Colors.GREEN
            self.progress_bar.value = 1.0
        elif status == SyncStatus.FAILED:
            self.status_icon.name = ft.Icons.ERROR
            self.status_icon.color = ft.Colors.RED
            self.progress_bar.color = ft.Colors.RED
        elif status == SyncStatus.CANCELLED:
            self.status_icon.name = ft.Icons.CANCEL
            self.status_icon.color = ft.Colors.ORANGE
            self.progress_bar.color = ft.Colors.ORANGE

    def _format_elapsed_time(self, seconds: float) -> str:
        """Format elapsed time as string.

        Args:
            seconds: Elapsed seconds.

        Returns:
            Formatted time string.
        """
        if seconds < 60:
            return f"경과 시간: {int(seconds)}초"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"경과 시간: {mins}분 {secs}초"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"경과 시간: {hours}시간 {mins}분"

    def _handle_cancel(self, e: ft.ControlEvent) -> None:
        """Handle cancel button click."""
        if self._on_cancel:
            self._on_cancel()

    def show(self) -> None:
        """Show the progress indicator."""
        if self._container:
            self._container.visible = True
            self._start_time = None

    def hide(self) -> None:
        """Hide the progress indicator."""
        if self._container:
            self._container.visible = False
            self._start_time = None

    def reset(self) -> None:
        """Reset the progress indicator to initial state."""
        self.progress_bar.value = 0
        self.status_text.value = ""
        self.detail_text.value = ""
        self.elapsed_text.value = ""
        self.percentage_text.value = ""
        self.status_icon.name = ft.Icons.SYNC
        self.status_icon.color = ft.Colors.BLUE
        self.progress_bar.color = ft.Colors.BLUE
        self._start_time = None


class SyncProgressDialog:
    """Modal dialog for showing sync progress."""

    def __init__(
        self,
        page: ft.Page,
        title: str = "데이터 동기화",
        on_cancel: Callable[[], None] | None = None,
    ):
        """Initialize SyncProgressDialog.

        Args:
            page: Flet page instance.
            title: Dialog title.
            on_cancel: Cancel callback.
        """
        self._page = page
        self._title = title
        self._on_cancel = on_cancel

        self._indicator = SyncProgressIndicator(
            on_cancel=self._handle_cancel,
            show_elapsed_time=True,
            show_cancel_button=True,
        )

        self._dialog: ft.AlertDialog | None = None

    def build(self) -> ft.AlertDialog:
        """Build the dialog.

        Returns:
            AlertDialog instance.
        """
        indicator_content = self._indicator.build()
        indicator_content.visible = True  # Always visible in dialog
        indicator_content.bgcolor = None  # Remove background in dialog

        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self._title),
            content=ft.Container(
                content=indicator_content,
                width=400,
                height=150,
            ),
            actions=[],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        return self._dialog

    def update(self, progress: SyncProgress) -> None:
        """Update dialog with progress.

        Args:
            progress: SyncProgress instance.
        """
        self._indicator.update(progress)

        # Auto-close on completion (with delay)
        if progress.status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED]:
            # Add close button when done
            if self._dialog:
                self._dialog.actions = [
                    ft.TextButton("닫기", on_click=self._close_dialog),
                ]

        self._page.update()

    def show(self) -> None:
        """Show the dialog."""
        if self._dialog is None:
            self.build()
        self._indicator.reset()
        self._page.dialog = self._dialog
        if self._dialog:
            self._dialog.open = True
        self._page.update()

    def close(self) -> None:
        """Close the dialog."""
        if self._dialog:
            self._dialog.open = False
        self._page.update()

    def _close_dialog(self, e: ft.ControlEvent) -> None:
        """Handle close button click."""
        self.close()

    def _handle_cancel(self) -> None:
        """Handle cancel callback."""
        if self._on_cancel:
            self._on_cancel()


class MiniSyncIndicator:
    """Minimal sync indicator for use in navigation or status bars."""

    def __init__(self):
        """Initialize MiniSyncIndicator."""
        self.progress_ring = ft.ProgressRing(
            width=16,
            height=16,
            stroke_width=2,
            color=ft.Colors.BLUE,
            visible=False,
        )

        self.status_icon = ft.Icon(
            ft.Icons.CLOUD_DONE,
            size=16,
            color=ft.Colors.GREEN,
            visible=False,
        )

        self.tooltip_text = ""

    def build(self) -> ft.Control:
        """Build the mini indicator.

        Returns:
            Stack containing indicators.
        """
        return ft.Tooltip(
            message=self.tooltip_text or "동기화 상태",
            content=ft.Stack(
                controls=[
                    self.progress_ring,
                    self.status_icon,
                ],
                width=20,
                height=20,
            ),
        )

    def update(self, progress: SyncProgress) -> None:
        """Update indicator with progress.

        Args:
            progress: SyncProgress instance.
        """
        if progress.status == SyncStatus.SYNCING:
            self.progress_ring.visible = True
            self.status_icon.visible = False
            self.tooltip_text = progress.message
        elif progress.status == SyncStatus.COMPLETED:
            self.progress_ring.visible = False
            self.status_icon.visible = True
            self.status_icon.name = ft.Icons.CLOUD_DONE
            self.status_icon.color = ft.Colors.GREEN
            self.tooltip_text = "동기화 완료"
        elif progress.status == SyncStatus.FAILED:
            self.progress_ring.visible = False
            self.status_icon.visible = True
            self.status_icon.name = ft.Icons.CLOUD_OFF
            self.status_icon.color = ft.Colors.RED
            self.tooltip_text = f"동기화 실패: {progress.error}"
        else:
            self.progress_ring.visible = False
            self.status_icon.visible = False

    def hide(self) -> None:
        """Hide the indicator."""
        self.progress_ring.visible = False
        self.status_icon.visible = False
