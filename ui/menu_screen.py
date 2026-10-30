"""Main Menu: title, story, player name and the main navigation buttons."""

import tkinter as tk
from tkinter import ttk

from core.missions import MISSIONS, build_tile_costs
from core.state_planner import PlanContext, plan_state_route
from core.validation import validate_player_name
from ui import styles
from ui.base_screen import BaseScreen
from ui.map_view import draw_mini_map

STORY = ("The Meridian Consortium hides its secrets inside impossible facilities: "
         "a vault swept by patrol drones, a lab sealed behind keycards and lasers, a "
         "penthouse guarded by all of it at once. You are the planner. Time every move, "
         "crack the terminals, and bring your operative home unseen.")


class MenuScreen(BaseScreen):
    """The opening screen."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.columnconfigure(0, weight=3, uniform="menu")
        self.columnconfigure(1, weight=2, uniform="menu")
        self.rowconfigure(0, weight=1)

        # ---- left column: text, name, buttons
        left = ttk.Frame(self, padding=(48, 30, 24, 24))
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="MISSION STRATEGY SIMULATOR", style="Dim.TLabel",
                  font=styles.font(10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(left, text="Heist Planner", style="Title.TLabel",
                  font=styles.font(34, "bold")).grid(row=1, column=0, sticky="w")
        self.story = ttk.Label(left, text=STORY, style="Subtitle.TLabel", wraplength=520,
                               justify="left")
        self.story.grid(row=2, column=0, sticky="w", pady=(6, 18))
        left.bind("<Configure>", self.on_resize)

        ttk.Label(left, text="Operative name", style="Dim.TLabel").grid(
            row=3, column=0, sticky="w")
        self.name_var = tk.StringVar(value=app.player_name)
        self.name_entry = ttk.Entry(left, textvariable=self.name_var, width=32,
                                    font=styles.font(11))
        self.name_entry.grid(row=4, column=0, sticky="w", pady=(2, 2))
        self.name_entry.bind("<Return>", lambda e: self.start_mission())
        self.name_message = ttk.Label(left, text="Leave empty to play as \"Agent\".",
                                      style="Dim.TLabel")
        self.name_message.grid(row=5, column=0, sticky="w", pady=(0, 16))

        buttons = ttk.Frame(left)
        buttons.grid(row=6, column=0, sticky="w")
        ttk.Button(buttons, text="Start Mission", style="BigAccent.TButton",
                   command=self.start_mission).grid(row=0, column=0, columnspan=2,
                                                    sticky="ew", pady=(0, 8))
        ttk.Button(buttons, text="Mission History", style="Big.TButton",
                   command=self.open_history).grid(row=1, column=0, sticky="ew",
                                                   padx=(0, 8), pady=(0, 8))
        ttk.Button(buttons, text="How to Play", style="Big.TButton",
                   command=lambda: app.show("how_to_play")).grid(row=1, column=1,
                                                                 sticky="ew", pady=(0, 8))
        ttk.Button(buttons, text="About Project", style="Big.TButton",
                   command=lambda: app.show("about")).grid(row=2, column=0, sticky="ew",
                                                           padx=(0, 8))
        ttk.Button(buttons, text="Exit", style="Big.TButton",
                   command=app.on_close).grid(row=2, column=1, sticky="ew")
        buttons.columnconfigure(0, weight=1, uniform="b")
        buttons.columnconfigure(1, weight=1, uniform="b")

        self.db_label = ttk.Label(left, text="", style="Dim.TLabel")
        self.db_label.grid(row=7, column=0, sticky="w", pady=(20, 0))

        # ---- right column: a drawn preview of a fictional facility
        right = ttk.Frame(self, style="Panel.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 28), pady=28)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        ttk.Label(right, text="FACILITY SCAN  ●  LIVE", style="PanelAccent.TLabel").grid(
            row=0, column=0, sticky="w")
        self.preview = tk.Canvas(right, bg=styles.PANEL, highlightthickness=0, bd=0)
        self.preview.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.preview.bind("<Configure>", lambda e: self.draw_preview())
        ttk.Label(right, text="Three facilities. Ten patrol drones. Every turn counts.",
                  style="PanelDim.TLabel", wraplength=300).grid(row=2, column=0, sticky="w",
                                                                pady=(10, 0))

    def on_resize(self, event) -> None:
        self.story.configure(wraplength=max(300, min(620, event.width - 80)))

    def draw_preview(self) -> None:
        """Mini map of the Vault with its drones and a sample route drawn on top."""
        canvas = self.preview
        canvas.delete("all")
        vault = MISSIONS["vault"]
        grid = vault.grid
        width, height = canvas.winfo_width(), canvas.winfo_height()
        tile = max(6, min((width - 4) // len(grid[0]), (height - 4) // len(grid)))
        ox = (width - tile * len(grid[0])) // 2
        oy = (height - tile * len(grid)) // 2
        draw_mini_map(canvas, grid, tile, ox, oy, drones=vault.drones)
        # The real safe route of the planner (it dodges every drone).
        ctx = PlanContext(grid, build_tile_costs(), vault.drones)
        sample = plan_state_route(ctx, vault.start, vault.objective).path
        points = []
        for r, c in sample:
            points.extend([ox + c * tile + tile / 2, oy + r * tile + tile / 2])
        canvas.create_line(*points, fill=styles.ROUTE, width=2, dash=(5, 3))
        x, y = points[0], points[1]
        canvas.create_oval(x - tile * 0.3, y - tile * 0.3, x + tile * 0.3, y + tile * 0.3,
                           fill=styles.CHARACTER, outline=styles.CHARACTER_RING, width=2)

    # ------------------------------------------------------------ actions
    def read_name(self) -> bool:
        """Validate the typed name. Shows an inline message if it is not allowed."""
        name, error = validate_player_name(self.name_var.get())
        if error:
            self.name_message.configure(text=error, style="Error.TLabel")
            self.name_entry.focus_set()
            return False
        self.app.player_name = name
        self.name_var.set(name)
        self.name_message.configure(text=f"Welcome, {name}.", style="Dim.TLabel")
        return True

    def start_mission(self) -> None:
        if self.read_name():
            self.app.show("mission_select")

    def open_history(self) -> None:
        if self.read_name():
            self.app.show("history")

    def on_show(self, **kwargs) -> None:
        self.name_var.set(self.app.player_name)
        self.db_label.configure(text=f"Database: {self.app.db_status}")
        self.name_entry.focus_set()
