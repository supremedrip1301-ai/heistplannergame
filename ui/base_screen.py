"""BaseScreen: the parent class of every screen (inheritance + overriding)."""

from tkinter import ttk


class BaseScreen(ttk.Frame):
    """A full-window page. The main window raises one screen at a time.

    Child classes override on_show() to refresh their content every time they
    appear, on_hide() to stop timers, and can_leave() to ask for confirmation
    (the gameplay screen uses this for "Abandon mission?").
    """

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app      # the MainWindow: shared state and navigation

    def on_show(self, **kwargs) -> None:
        """Called every time the screen becomes visible."""

    def on_hide(self) -> None:
        """Called just before another screen is shown."""

    def can_leave(self) -> bool:
        """Return False to cancel navigation away from this screen."""
        return True

    def handle_key(self, key: str) -> None:
        """Keyboard shortcut forwarded by the main window (only to the visible screen)."""
