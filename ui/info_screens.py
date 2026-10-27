"""Read-only pages: How to Play and About Project."""

import tkinter as tk
from tkinter import ttk

from core import config
from ui import styles
from ui.base_screen import BaseScreen

HOW_TO_PLAY = [
    ("The goal",
     "Guide your operative to the objective, collect it, then reach the extraction "
     "point. A mission is only complete when you extract WITH the objective."),
    ("1. Choose a mission",
     "Pick one of three facilities. Read the briefing: it tells you what makes the "
     "map special."),
    ("2. Pack your kit",
     f"You have {config.KIT_CAPACITY} energy units. Tick gadgets to pack them. "
     "Press Suggested Kit to let your planner pick the most useful kit that fits; you can "
     "still change it. Mission Readiness shows how good your kit is for this mission."),
    ("3. Plan and move",
     "Plan Route draws the cheapest safe route to your current target. Move Next Step "
     "walks one tile; Auto Travel walks the whole route; Stop pauses it."),
    ("Effort",
     "Each floor tile costs 1 effort. Static fields cost 4 (only 2 with Mobility Boots). "
     "The planner always looks for the lowest total effort, not just the fewest steps."),
    ("4. Collect and extract",
     "Stand on the objective and press Collect Objective. Your target switches to the "
     "extraction point: plan again and get out."),
    ("Alerts",
     "In the Relay, taking the signal key raises an alert that seals the relay gate. "
     "Your route is recalculated at once. You can also trigger the alert early. "
     "A Pocket Scanner reveals the weak gate in advance; a Signal Decoy cancels the "
     "alert penalty."),
    ("Score",
     "Success 500 + objective 200 + extraction 100 + preparation bonus (up to 150), "
     "minus 5 per effort unit, minus 50 if an alert was raised without a decoy. "
     "Ranks: Phantom 800+, Specialist 650+, Operative 450+, Rookie below."),
    ("Keyboard",
     "P plan route   •   Space move next step   •   A auto travel   •   "
     "Esc stop   •   C collect objective"),
]


class TextPage(BaseScreen):
    """A scrollable page of headed paragraphs with a Back button."""

    page_title = ""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(40, 24, 40, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=self.page_title, style="Title.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Button(header, text="Back", command=lambda: app.show("menu")).grid(
            row=0, column=1, sticky="e")

        body = ttk.Frame(self, style="Panel.TFrame", padding=(24, 16))
        body.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 28))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        self.text = tk.Text(body, bg=styles.PANEL, fg=styles.TEXT, relief="flat",
                            wrap="word", padx=4, pady=4, highlightthickness=0, bd=0,
                            font=styles.font(10), cursor="arrow", spacing1=2, spacing3=2)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.tag_configure("heading", font=styles.font(12, "bold"),
                                foreground=styles.ACCENT, spacing1=10)
        self.text.tag_configure("body", foreground=styles.TEXT, lmargin1=2, lmargin2=2)
        self.text.tag_configure("dim", foreground=styles.TEXT_DIM)

    def sections(self) -> list:
        """(heading, paragraph) pairs. Child classes override this."""
        return []

    def on_show(self, **kwargs) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for heading, paragraph in self.sections():
            self.text.insert("end", heading + "\n", "heading")
            self.text.insert("end", paragraph + "\n", "body")
        self.text.configure(state="disabled")


class HowToPlayScreen(TextPage):
    page_title = "How to Play"

    def sections(self) -> list:
        return HOW_TO_PLAY


class AboutScreen(TextPage):
    """Credits page for the teacher: this is the one screen that names the algorithms."""

    page_title = "About Project"

    def sections(self) -> list:
        return [
            ("Heist Planner Game — Mission Strategy Simulator",
             "A fictional top-down stealth-puzzle and planning game, built as an MCA "
             "(AI & ML) project at Chandigarh University by Anshul Kaushik. All places, "
             "obstacles and gadgets are imaginary."),
            ("Active database mode", self.app.db_status),
            ("Route Guidance → Dijkstra's shortest-path algorithm",
             "Each walkable tile is a vertex and each up/right/down/left step is an edge "
             "whose cost is the cost of the tile entered. A heapq priority queue gives "
             "O((V + E) log V). The route is rebuilt from a 'previous' map and is "
             "recalculated whenever the target changes or a gate is sealed."),
            ("Suggested Kit → 0/1 Knapsack (dynamic programming)",
             "Energy cost is the weight, mission usefulness is the value, and 8 energy "
             "units is the capacity. A DP table best[i][c] is filled and traced back to "
             "find the chosen gadgets. Ties prefer the cheaper kit, then the "
             "alphabetically first one. Tests cross-check it with brute force and with a "
             "Branch and Bound version."),
            ("Technologies",
             "Python 3 standard library: tkinter / ttk / Canvas (all graphics are drawn "
             "shapes), heapq, dataclasses, sqlite3, json, logging, pathlib, unittest.\n"
             "Optional: Oracle Database (26ai Free / 19c) with PL/SQL procedures, a "
             "function and an audit trigger, reached through the python-oracledb driver "
             "in Thin mode."),
            ("Saving",
             "SQLite is the default local save (data/heist_planner.db). Oracle mode calls "
             "the stored procedures HP_SAVE_RUN and HP_GET_STATS and the function "
             "HP_RANK_TITLE. If Oracle is not reachable, the game falls back to SQLite."),
        ]
