"""Equipment Preparation: pick gadgets within the energy capacity.

The Suggested Kit button runs the 0/1 Knapsack optimiser (core/loadout_optimizer.py),
but the player only ever sees game words: energy, usefulness bars, readiness.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from core import config
from core.game_engine import MissionRun
from core.gadgets import GADGETS, GADGET_ORDER, kit_energy
from core.loadout_optimizer import recommend_for_mission
from core.missions import MISSIONS
from core.scoring import readiness_percent
from ui import styles
from ui.base_screen import BaseScreen
from ui.widgets import CapacityBar, ScrollableFrame, draw_level_bars, usefulness_level


class GadgetRow:
    """One gadget line: name, description, energy, usefulness bars, Pack checkbox."""

    def __init__(self, parent, row, gadget, on_toggle):
        self.gadget = gadget
        self.var = tk.BooleanVar(value=False)
        self.frame = ttk.Frame(parent, style="Card.TFrame", padding=(14, 8))
        self.frame.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        self.frame.columnconfigure(0, weight=1)

        title = ttk.Frame(self.frame, style="Card.TFrame")
        title.grid(row=0, column=0, sticky="w")
        ttk.Label(title, text=gadget.name, style="CardHeading.TLabel").grid(
            row=0, column=0, sticky="w")
        self.tag = ttk.Label(title, text="Recommended", style="Tag.TLabel")
        self.tag.grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.tag.grid_remove()
        self.texts = [
            ttk.Label(self.frame, text=gadget.description, style="CardDim.TLabel",
                      wraplength=360, justify="left"),
            ttk.Label(self.frame, text=gadget.effect, style="CardDim.TLabel",
                      foreground=styles.ACCENT, wraplength=360, justify="left"),
        ]
        self.texts[0].grid(row=1, column=0, sticky="w")
        self.texts[1].grid(row=2, column=0, sticky="w")
        self.frame.bind("<Configure>", self.on_resize)

        ttk.Label(self.frame, text=f"{gadget.energy_cost} energy", style="Card.TLabel",
                  font=styles.font(10, "bold")).grid(row=0, column=1, rowspan=3, padx=16)
        self.bars = tk.Canvas(self.frame, width=26, height=24, bg=styles.PANEL_ALT,
                              highlightthickness=0, bd=0)
        self.bars.grid(row=0, column=2, rowspan=3)
        self.level_text = ttk.Label(self.frame, text="", style="CardDim.TLabel", width=8)
        self.level_text.grid(row=0, column=3, rowspan=3, padx=(4, 12))
        self.check = ttk.Checkbutton(self.frame, text="Pack", variable=self.var,
                                     style="Card.TCheckbutton",
                                     command=lambda: on_toggle(self))
        self.check.grid(row=0, column=4, rowspan=3)

    def on_resize(self, event) -> None:
        # Leave room for the energy, bars and Pack columns on the right.
        for label in self.texts:
            label.configure(wraplength=max(180, event.width - 270))

    def show_usefulness(self, value: int) -> None:
        bars, word = usefulness_level(value)
        self.bars.delete("all")
        draw_level_bars(self.bars, bars, x=2, y=4)
        self.level_text.configure(text=word)

    def set_recommended(self, recommended: bool) -> None:
        if recommended:
            self.tag.grid()
        else:
            self.tag.grid_remove()


class PreparationScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.mission = None
        self.best = None                   # LoadoutResult of the Suggested Kit
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=0, minsize=300)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(32, 18, 32, 8))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.title_label = ttk.Label(header, text="Equipment Preparation", style="Title.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=f"Pack gadgets for the mission. Your kit can hold "
                  f"{config.KIT_CAPACITY} energy units.", style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w")

        # Gadget list (scrollable on small screens)
        self.list_area = ScrollableFrame(self)
        self.list_area.grid(row=1, column=0, sticky="nsew", padx=(32, 12), pady=(4, 16))
        self.list_area.inner.columnconfigure(0, weight=1)
        self.rows = {}
        for i, gadget_id in enumerate(GADGET_ORDER):
            self.rows[gadget_id] = GadgetRow(self.list_area.inner, i, GADGETS[gadget_id],
                                             self.on_toggle)

        # Side panel: capacity, readiness, actions
        side = ttk.Frame(self, style="Panel.TFrame", padding=18)
        side.grid(row=1, column=1, sticky="nsew", padx=(0, 32), pady=(4, 16))
        side.columnconfigure(0, weight=1)
        side.rowconfigure(6, weight=1)
        ttk.Label(side, text="Kit Status", style="PanelHeading.TLabel").grid(
            row=0, column=0, sticky="w")
        self.energy_label = ttk.Label(side, text="", style="PanelValue.TLabel")
        self.energy_label.grid(row=1, column=0, sticky="w", pady=(10, 4))
        self.capacity_bar = CapacityBar(side, config.KIT_CAPACITY)
        self.capacity_bar.grid(row=2, column=0, sticky="ew")
        self.readiness_label = ttk.Label(side, text="", style="PanelAccent.TLabel",
                                         font=styles.font(12, "bold"))
        self.readiness_label.grid(row=3, column=0, sticky="w", pady=(14, 4))
        ttk.Button(side, text="Suggested Kit", style="Accent.TButton",
                   command=self.suggest_kit).grid(row=4, column=0, sticky="ew", pady=(6, 6))
        self.message = ttk.Label(side, text="", style="PanelDim.TLabel", wraplength=250,
                                 justify="left")
        self.message.grid(row=5, column=0, sticky="nw", pady=(4, 0))

        buttons = ttk.Frame(side, style="Panel.TFrame")
        buttons.grid(row=7, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1, uniform="pb")
        buttons.columnconfigure(1, weight=1, uniform="pb")
        ttk.Button(buttons, text="Back", command=lambda: app.show("mission_select")).grid(
            row=0, column=0, sticky="ew", padx=(0, 4))
        self.begin_button = ttk.Button(buttons, text="Begin Mission", style="Accent.TButton",
                                       command=self.begin_mission)
        self.begin_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    # ------------------------------------------------------------ state helpers
    def selected_ids(self) -> tuple:
        return tuple(g for g in GADGET_ORDER if self.rows[g].var.get())

    def chosen_usefulness(self) -> int:
        return sum(self.mission.usefulness[g] for g in self.selected_ids())

    def on_show(self, **kwargs) -> None:
        mission = MISSIONS.get(self.app.mission_id)
        if mission is None:
            self.app.show("mission_select")
            return
        same_mission = self.mission is mission
        self.mission = mission
        self.best = recommend_for_mission(mission)   # needed for readiness %
        self.title_label.configure(text=f"Equipment Preparation — {mission.name}")
        for gadget_id, row in self.rows.items():
            row.show_usefulness(mission.usefulness[gadget_id])
            row.set_recommended(False)
            if not same_mission:
                row.var.set(False)
            else:
                row.var.set(gadget_id in self.app.kit_ids)
        self.set_message("Tick gadgets to pack them, or press Suggested Kit.")
        self.update_status()

    def set_message(self, text: str, warn: bool = False) -> None:
        self.message.configure(text=text, style="PanelWarn.TLabel" if warn
                               else "PanelDim.TLabel")

    def update_status(self) -> None:
        """Refresh energy, capacity bar, readiness and the Begin button."""
        used = kit_energy(self.selected_ids())
        self.energy_label.configure(text=f"Energy used: {used} / {config.KIT_CAPACITY}")
        self.capacity_bar.set_used(used)
        readiness = readiness_percent(self.chosen_usefulness(), self.best.total_usefulness)
        self.readiness_label.configure(text=f"Mission Readiness: {readiness}%")
        valid = used <= config.KIT_CAPACITY
        self.begin_button.state(["!disabled"] if valid else ["disabled"])

    # ------------------------------------------------------------ actions
    def on_toggle(self, row: GadgetRow) -> None:
        """Called on every tick/untick. Refuse ticks that exceed the capacity."""
        if row.var.get():
            used_without = kit_energy(self.selected_ids()) - row.gadget.energy_cost
            left = config.KIT_CAPACITY - used_without
            if row.gadget.energy_cost > left:
                row.var.set(False)
                self.set_message(f"Not enough energy — {left} unit"
                                 f"{'' if left == 1 else 's'} left. Remove an item first.",
                                 warn=True)
                self.update_status()
                return
            self.set_message(f"{row.gadget.name} packed.")
        else:
            self.set_message(f"{row.gadget.name} removed.")
        self.update_status()

    def suggest_kit(self) -> None:
        """Tick exactly the recommended gadgets and tag them."""
        recommended = self.best.selected_ids
        for gadget_id, row in self.rows.items():
            row.var.set(gadget_id in recommended)
            row.set_recommended(gadget_id in recommended)
        self.set_message("Suggested Kit packed: the most useful gear that fits your "
                         "energy. You can still change it.")
        self.update_status()

    def begin_mission(self) -> None:
        kit = self.selected_ids()
        if kit_energy(kit) > config.KIT_CAPACITY:
            self.set_message("This kit is too heavy. Remove an item first.", warn=True)
            return
        if not kit:
            if not messagebox.askyesno("Travel light?",
                                       "You have not packed any gadgets. Start anyway?",
                                       parent=self):
                self.set_message("An empty kit is allowed, but gadgets help.", warn=True)
                return
        self.app.kit_ids = kit
        self.app.best_usefulness = self.best.total_usefulness
        self.app.run = MissionRun(self.app.player_name, self.mission, kit,
                                  self.best.total_usefulness)
        self.app.show("gameplay")
