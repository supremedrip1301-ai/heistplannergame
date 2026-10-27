"""Mission History: saved runs in a Treeview, with statistics above it."""

import logging
import tkinter as tk
from tkinter import ttk

from core import config
from ui import styles
from ui.base_screen import BaseScreen

logger = logging.getLogger(__name__)

COLUMNS = (
    ("player", "Player", 110),
    ("mission", "Mission", 100),
    ("result", "Result", 90),
    ("score", "Score", 60),
    ("rank", "Rank", 90),
    ("moves", "Moves", 60),
    ("effort", "Effort", 60),
    ("kit", "Kit", 230),
    ("date", "Date/Time", 140),
)
EMPTY_TEXT = "No missions on record yet — your first debrief will appear here."


class StatTile(ttk.Frame):
    """A small panel with a big number and a caption."""

    def __init__(self, parent, caption: str):
        super().__init__(parent, style="Panel.TFrame", padding=(16, 10))
        self.value = ttk.Label(self, text="0", style="PanelHeading.TLabel",
                               font=styles.font(18, "bold"), foreground=styles.ACCENT)
        self.value.grid(row=0, column=0, sticky="w")
        ttk.Label(self, text=caption, style="PanelDim.TLabel").grid(row=1, column=0,
                                                                     sticky="w")


class HistoryScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        header = ttk.Frame(self, padding=(32, 18, 32, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Mission History", style="Title.TLabel").grid(
            row=0, column=0, sticky="w")
        self.scope_label = ttk.Label(header, text="", style="Subtitle.TLabel")
        self.scope_label.grid(row=1, column=0, sticky="w")
        self.all_players = tk.BooleanVar(value=False)
        ttk.Checkbutton(header, text="All players", variable=self.all_players,
                        command=self.refresh).grid(row=0, column=1, rowspan=2, padx=(0, 12))
        ttk.Button(header, text="Refresh", command=self.refresh).grid(
            row=0, column=2, rowspan=2, padx=(0, 8))
        ttk.Button(header, text="Back", command=lambda: app.show("menu")).grid(
            row=0, column=3, rowspan=2)

        stats = ttk.Frame(self, padding=(32, 6, 32, 6))
        stats.grid(row=1, column=0, sticky="ew")
        self.tiles = {}
        for i, (key, caption) in enumerate((("total_runs", "Total runs"),
                                            ("success_runs", "Successful missions"),
                                            ("best_score", "Best score"),
                                            ("avg_score", "Average score (successful)"))):
            tile = StatTile(stats, caption)
            tile.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))
            stats.columnconfigure(i, weight=1, uniform="stats")
            self.tiles[key] = tile

        self.notice = ttk.Label(self, text="", style="Dim.TLabel", padding=(32, 2))
        self.notice.grid(row=2, column=0, sticky="w")

        table = ttk.Frame(self, padding=(32, 4, 32, 20))
        table.grid(row=3, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=[c[0] for c in COLUMNS], show="headings",
                                 selectmode="browse")
        for key, heading, width in COLUMNS:
            anchor = "e" if key in ("score", "moves", "effort") else "w"
            self.tree.heading(key, text=heading, anchor=anchor)
            self.tree.column(key, width=width, minwidth=50, anchor=anchor,
                             stretch=(key == "kit"))
        self.tree.tag_configure("abandoned", foreground=styles.TEXT_DIM)
        self.tree.tag_configure("odd", background=styles.PANEL_ALT)
        scroll_y = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

    def on_show(self, **kwargs) -> None:
        self.refresh()

    def refresh(self) -> None:
        """Reload statistics and rows from the database."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        player = None if self.all_players.get() else self.app.player_name
        if player is None:
            self.scope_label.configure(text="Showing every operative.")
        else:
            self.scope_label.configure(text=f"Showing operative {player}.")

        repository = self.app.repository
        if repository is None:
            self.show_stats({"total_runs": 0, "success_runs": 0, "best_score": 0,
                             "avg_score": 0.0})
            self.notice.configure(text="Saving is not available in this session.")
            return
        try:
            stats = repository.get_stats(player)
            runs = repository.get_recent_runs(config.HISTORY_LIMIT, player)
        except Exception as error:
            logger.exception("Loading history failed")
            self.notice.configure(text=repository.friendly_error(error), style="Error.TLabel")
            return

        self.show_stats(stats)
        if not runs:
            self.notice.configure(text=EMPTY_TEXT, style="Dim.TLabel")
            return
        self.notice.configure(text=f"{len(runs)} most recent record"
                              f"{'' if len(runs) == 1 else 's'} · "
                              f"{repository.backend_label()}", style="Dim.TLabel")
        for i, run in enumerate(runs):
            tags = []
            if run["result"] == "ABANDONED":
                tags.append("abandoned")
            if i % 2 == 1:
                tags.append("odd")
            result = "Success" if run["result"] == "SUCCESS" else "Abandoned"
            if run["alert_triggered"] == "Y":
                result = result + " ▲"
            self.tree.insert("", "end", values=(
                run["player_name"], run["mission_name"], result, run["score"],
                run["rank_title"], run["moves"], run["route_cost"], run["kit_summary"],
                run["played_at"]), tags=tags)

    def show_stats(self, stats: dict) -> None:
        self.tiles["total_runs"].value.configure(text=str(stats["total_runs"]))
        self.tiles["success_runs"].value.configure(text=str(stats["success_runs"]))
        self.tiles["best_score"].value.configure(text=str(stats["best_score"]))
        self.tiles["avg_score"].value.configure(text=f"{stats['avg_score']:.0f}")
