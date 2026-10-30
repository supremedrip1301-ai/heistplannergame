"""The single main window: screen container, menu bar, navigation and shared state."""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from core import config
from ui import styles
from ui.debrief_screen import DebriefScreen
from ui.gameplay_screen import GameplayScreen
from ui.history_screen import HistoryScreen
from ui.info_screens import AboutScreen, HowToPlayScreen
from ui.menu_screen import MenuScreen
from ui.mission_select_screen import MissionSelectScreen
from ui.preparation_screen import PreparationScreen
from ui.terminal_screen import TerminalScreen

logger = logging.getLogger(__name__)

SCREEN_CLASSES = {
    "menu": MenuScreen,
    "how_to_play": HowToPlayScreen,
    "about": AboutScreen,
    "mission_select": MissionSelectScreen,
    "preparation": PreparationScreen,
    "gameplay": GameplayScreen,
    "terminal": TerminalScreen,
    "debrief": DebriefScreen,
    "history": HistoryScreen,
}


class MainWindow:
    """Owns the Tk root, every screen, the repository and the shared game state."""

    def __init__(self, root: tk.Tk, repository, db_status: str):
        self.root = root
        self.repository = repository        # SQLiteRepository / OracleRepository / None
        self.db_status = db_status          # friendly text for the About screen

        # Shared state that several screens need.
        self.player_name = config.DEFAULT_PLAYER_NAME
        self.mission_id = None
        self.kit_ids = ()
        self.best_usefulness = 0
        self.pro_mode = False
        self.run = None                     # the current MissionRun
        self.last_save_message = ""         # shown on the debrief screen
        self.terminal_message = ""          # result of the last terminal visit
        self.next_screen = None             # where show() is going (for can_leave)

        self.setup_window()
        styles.apply_style(root)
        self.build_menu_bar()

        # One container; every screen sits in the same grid cell and the
        # visible one is raised with tkraise().
        container = ttk.Frame(root)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.screens = {}
        for name, screen_class in SCREEN_CLASSES.items():
            screen = screen_class(container, self)
            screen.grid(row=0, column=0, sticky="nsew")
            self.screens[name] = screen
        self.current_name = None

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.report_callback_exception = self.on_callback_error
        root.bind("<KeyPress>", self.on_key)
        self.show("menu")
        if "unavailable" in db_status.lower():
            # Oracle (or every database) failed: tell the player once, kindly.
            root.after(400, lambda: messagebox.showinfo(
                "Database notice", f"{db_status}.\n\nThe game is fully playable.",
                parent=root))

    # ------------------------------------------------------------ window
    def setup_window(self) -> None:
        """Title, size (centred, clamped to small screens) and minimum size."""
        root = self.root
        root.title(config.APP_TITLE)
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        width = min(config.WINDOW_WIDTH, screen_w - 40)
        height = min(config.WINDOW_HEIGHT, screen_h - 90)   # leave room for the taskbar
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - 20)
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.minsize(min(config.MIN_WIDTH, width), min(config.MIN_HEIGHT, height))

    def build_menu_bar(self) -> None:
        menu_bar = tk.Menu(self.root)
        game_menu = tk.Menu(menu_bar, tearoff=0)
        game_menu.add_command(label="Main Menu", command=lambda: self.show("menu"))
        game_menu.add_command(label="Mission History", command=lambda: self.show("history"))
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="Game", menu=game_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="How to Play", command=lambda: self.show("how_to_play"))
        help_menu.add_command(label="About", command=lambda: self.show("about"))
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menu_bar)

    # ------------------------------------------------------------ navigation
    @property
    def current_screen(self):
        if self.current_name is None:
            return None
        return self.screens[self.current_name]

    def show(self, name: str, **kwargs) -> bool:
        """Switch to another screen. Returns False if the current one refused."""
        current = self.current_screen
        if current is not None and name != self.current_name:
            self.next_screen = name
            try:
                if not current.can_leave():
                    return False
            finally:
                self.next_screen = None
            current.on_hide()
        self.current_name = name
        screen = self.screens[name]
        screen.tkraise()
        screen.on_show(**kwargs)
        screen.focus_set()
        return True

    def on_key(self, event) -> None:
        """Forward keyboard shortcuts to the visible screen only."""
        # Typing inside a text field must never trigger game shortcuts.
        if isinstance(event.widget, (tk.Entry, ttk.Entry)):
            return
        screen = self.current_screen
        if screen is not None:
            screen.handle_key(event.keysym)

    # ------------------------------------------------------------ saving
    def save_run(self, run):
        """Save a finished or abandoned run exactly once.

        Returns (run_id or None, message). Errors are logged and turned into a
        friendly message; they never crash the game.
        """
        if self.repository is None:
            return None, "Saving is not available in this session."
        if run.result_saved:
            return None, "Result already saved."
        try:
            run_id = run.save_once(self.repository.save_run)
        except Exception as error:      # any database problem
            logger.exception("Saving the run failed")
            friendly = getattr(self.repository, "friendly_error", None)
            text = friendly(error) if friendly else "The result could not be saved."
            return None, text
        return run_id, f"Result saved ({self.repository.backend_label()})."

    def has_unfinished_run(self) -> bool:
        return self.run is not None and self.run.needs_abandon_save()

    # ------------------------------------------------------------ closing / errors
    def on_close(self) -> None:
        """Window close: confirm abandoning, stop timers, close the database."""
        current = self.current_screen
        if current is not None:
            if not current.can_leave():
                return
            current.on_hide()
        if self.repository is not None:
            try:
                self.repository.close()
            except Exception:
                logger.exception("Closing the repository failed")
        logger.info("Game closed")
        self.root.destroy()

    def on_callback_error(self, exc_type, exc_value, exc_traceback) -> None:
        """Tk callback crashed: log the details, show a friendly dialog."""
        logger.error("Unexpected error in a callback",
                     exc_info=(exc_type, exc_value, exc_traceback))
        messagebox.showerror(
            "Something went wrong",
            "An unexpected problem occurred. The details were written to "
            "logs/heist_planner.log.\nYou can keep playing or return to the main menu.",
            parent=self.root)
