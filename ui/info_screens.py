"""Read-only pages: How to Play and About Project."""

import tkinter as tk
from tkinter import ttk

from ui import styles
from ui.base_screen import BaseScreen

HOW_TO_PLAY = [
    ("The goal",
     "Guide your operative to the objective, collect it, then reach the extraction "
     "point - without being seen. A mission is only complete when you extract WITH the "
     "objective."),
    ("1. Choose a mission",
     "The Vault (Hard), the Lab (Expert) or the Penthouse (Master). Read the briefing: it "
     "tells you what guards the map. Tick Pro mode if you want no help at all."),
    ("2. Patrol drones",
     "Every move or Wait is one turn, and after each turn every drone moves one tile "
     "along its fixed patrol. A drone sees its own tile and two tiles ahead (red tiles); "
     "walls and locked doors block its view. Stand in a red tile, or walk through a "
     "drone, and you are caught: the mission fails. Amber outlines show where the drones "
     "will look after your next turn. Wait [W] lets a patrol pass."),
    ("3. Plan and move",
     "Plan Route draws the cheapest route that no drone can see, including the turns "
     "you must wait (amber number badges). Move Next Step walks one turn; Auto Travel walks "
     "the whole route; Stop pauses it. Arrow keys move one tile by hand."),
    ("Effort",
     "Each floor tile costs 1 effort, each Wait costs 1, and static fields cost 4. "
     "The planner always looks for the lowest total effort, not just the fewest steps."),
    ("4. Keycards, doors and terminals",
     "A locked door opens only once you have walked over the keycard. Laser barriers stay "
     "on until you hack the terminal [H]. The terminal is a Power Relay: draw the lightest "
     "path of numbered cells from IN to OUT (6 x 6 in the Lab, 7 x 7 in the Penthouse). "
     "Only the lightest possible path works; a wrong answer is a lockout (+5 effort). "
     "The Relay Monitor checks your path after every click: ON TRACK (green) means it can "
     "still reach the lightest load, OFF TRACK (red) means take back some cells."),
    ("5. Collect and extract",
     "Stand on the objective and press Collect Objective. Your target switches to the "
     "extraction point: plan again and get out."),
    ("Pro mode",
     "Plan Route, Auto Travel and the amber next-turn preview are switched off. You read "
     "the patrols yourself and move with the arrow keys and Wait. A Pro run earns +25% "
     "score."),
    ("Score",
     "Success 500 + objective 200 + extraction 100 + high-risk bonus (Vault 300, Lab 500, "
     "Penthouse 500), minus 5 per effort unit; then +25% in Pro mode. "
     "Ranks: Phantom 800+, Specialist 650+, Operative 450+, Rookie below."),
    ("Keyboard",
     "P plan route   •   Space next step   •   A auto travel   •   "
     "Esc stop   •   C collect   •   W wait   •   H hack terminal   "
     "•   arrow keys move by hand"),
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
             "drones and devices are imaginary."),
            ("Active database mode", self.app.db_status),
            ("Route Guidance → Dijkstra's shortest-path algorithm on a state graph",
             "With patrol drones and keycards a tile alone is not enough, so the planner's "
             "vertex is (tile, drone clock, keycard held). The drone clock is the turn number "
             "modulo the LCM of all patrol lengths, because the patrols then repeat. Edges are "
             "the four moves and Wait, with the cost of the tile entered; edges into a drone's "
             "view are left out. A heapq priority queue gives O((V + E) log V). Tests "
             "cross-check it with Bellman-Ford and with my matrix Dijkstra (DAA Exp 4)."),
            ("Terminal puzzle → Dijkstra is the judge",
             "The Power Relay is a shortest-path problem: each numbered cell is a vertex and "
             "the number is the cost of entering it. Dijkstra computes the minimum load, and "
             "only a path with exactly that load is accepted. Grids where a greedy walk "
             "(always the cheaper next cell) would already win are thrown away, so the player "
             "has to plan. The Relay Monitor runs Dijkstra again after every click, from the end "
             "of the player's path to OUT (cells already used are blocked): load so far + that "
             "shortest remaining cost = the best this path can still reach. If it equals the "
             "minimum the player is on track."),
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
