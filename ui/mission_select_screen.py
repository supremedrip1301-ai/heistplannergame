"""Mission Selection and Briefing: three cards with thumbnails, then the briefing."""

import tkinter as tk
from tkinter import ttk

from core.missions import MISSIONS, MISSION_ORDER
from ui import styles
from ui.base_screen import BaseScreen
from ui.map_view import draw_mini_map

DIFFICULTY_STYLE = {"Easy": styles.GREEN, "Medium": styles.AMBER, "Hard": styles.RED}
THUMB_TILE = 9
MAX_ROWS = max(m.rows for m in MISSIONS.values())


class MissionCard(ttk.Frame):
    """One clickable mission card."""

    def __init__(self, parent, mission, on_select):
        super().__init__(parent, style="Card.TFrame", padding=12)
        self.mission = mission
        self.on_select = on_select
        self.columnconfigure(0, weight=1)

        # Same canvas size for every card (the tallest map has 11 rows), so the
        # card texts line up even though the Relay map is taller.
        width = mission.cols * THUMB_TILE
        height = MAX_ROWS * THUMB_TILE
        self.thumb = tk.Canvas(self, width=width, height=height, bg=styles.PANEL_ALT,
                               highlightthickness=0, bd=0)
        self.thumb.grid(row=0, column=0, sticky="w")
        draw_mini_map(self.thumb, mission.grid, THUMB_TILE)

        self.name_label = ttk.Label(self, text=mission.name, style="CardHeading.TLabel")
        self.name_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.level_label = tk.Label(self, text=mission.difficulty.upper(),
                                    fg=DIFFICULTY_STYLE[mission.difficulty],
                                    bg=styles.PANEL_ALT, font=styles.font(8, "bold"))
        self.level_label.grid(row=2, column=0, sticky="w")
        self.hook_label = ttk.Label(self, text=mission.hook, style="CardDim.TLabel",
                                    wraplength=230, justify="left")
        self.hook_label.grid(row=3, column=0, sticky="w", pady=(4, 0))

        for widget in (self, self.thumb, self.name_label, self.level_label, self.hook_label):
            widget.bind("<Button-1>", lambda e: self.on_select(self.mission.mission_id))
            widget.configure(cursor="hand2")
        self.bind("<Configure>", lambda e: self.hook_label.configure(
            wraplength=max(150, e.width - 30)))

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.configure(style="Selected.TFrame")
            self.name_label.configure(style="SelectedHeading.TLabel")
            self.hook_label.configure(style="SelectedDim.TLabel")
            bg = styles.ACCENT_SOFT
        else:
            self.configure(style="Card.TFrame")
            self.name_label.configure(style="CardHeading.TLabel")
            self.hook_label.configure(style="CardDim.TLabel")
            bg = styles.PANEL_ALT
        self.level_label.configure(bg=bg)
        self.thumb.configure(bg=bg)


class MissionSelectScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.selected_id = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Frame(self, padding=(36, 20, 36, 8))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Choose a Mission", style="Title.TLabel").grid(
            row=0, column=0, sticky="w")
        self.welcome = ttk.Label(header, text="", style="Subtitle.TLabel")
        self.welcome.grid(row=1, column=0, sticky="w")

        cards = ttk.Frame(self, padding=(36, 4, 36, 8))
        cards.grid(row=1, column=0, sticky="ew")
        self.cards = {}
        for i, mission_id in enumerate(MISSION_ORDER):
            card = MissionCard(cards, MISSIONS[mission_id], self.select)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            cards.columnconfigure(i, weight=1, uniform="cards")
            self.cards[mission_id] = card

        # Briefing panel
        brief = ttk.Frame(self, style="Panel.TFrame", padding=(20, 14))
        brief.grid(row=2, column=0, sticky="nsew", padx=36, pady=(4, 8))
        brief.columnconfigure(1, weight=1)
        self.brief_title = ttk.Label(brief, text="Mission Briefing",
                                     style="PanelHeading.TLabel")
        self.brief_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.brief_rows = {}
        for row, key in enumerate(("Goal", "Condition", "Extraction", "Terrain"), start=1):
            ttk.Label(brief, text=key, style="PanelDim.TLabel").grid(
                row=row, column=0, sticky="nw", padx=(0, 16), pady=3)
            value = ttk.Label(brief, text="", style="Panel.TLabel", wraplength=700,
                              justify="left")
            value.grid(row=row, column=1, sticky="nw", pady=3)
            self.brief_rows[key] = value
        brief.bind("<Configure>", self.on_brief_resize)

        buttons = ttk.Frame(self, padding=(36, 4, 36, 18))
        buttons.grid(row=3, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        ttk.Button(buttons, text="Back", command=lambda: app.show("menu")).grid(
            row=0, column=1, padx=(0, 10))
        self.start_button = ttk.Button(buttons, text="Start Preparation",
                                       style="Accent.TButton", command=self.start_preparation)
        self.start_button.grid(row=0, column=2)

    def on_brief_resize(self, event) -> None:
        for label in self.brief_rows.values():
            label.configure(wraplength=max(300, event.width - 160))

    def select(self, mission_id: str) -> None:
        self.selected_id = mission_id
        for card_id, card in self.cards.items():
            card.set_selected(card_id == mission_id)
        mission = MISSIONS[mission_id]
        self.brief_title.configure(
            text=f"Mission Briefing — {mission.name}  ({mission.difficulty})")
        self.brief_rows["Goal"].configure(text=mission.goal)
        self.brief_rows["Condition"].configure(text=mission.condition)
        self.brief_rows["Extraction"].configure(text=mission.extraction)
        terrain = ["Floor", "Walls"] + mission.tile_types() + ["Objective", "Extraction"]
        self.brief_rows["Terrain"].configure(text=", ".join(terrain))
        self.start_button.state(["!disabled"])

    def start_preparation(self) -> None:
        if self.selected_id is None:
            return
        self.app.mission_id = self.selected_id
        self.app.show("preparation")

    def on_show(self, **kwargs) -> None:
        self.welcome.configure(text=f"Operative {self.app.player_name}, select your target.")
        if self.app.mission_id in MISSIONS:
            self.select(self.app.mission_id)
        else:
            self.selected_id = None
            for card in self.cards.values():
                card.set_selected(False)
            self.brief_title.configure(text="Mission Briefing")
            for key, label in self.brief_rows.items():
                label.configure(text="Select a mission card above." if key == "Goal" else "")
            self.start_button.state(["disabled"])
