"""Mission Debrief: final score with its breakdown and the outcome sentence."""

import tkinter as tk
from tkinter import ttk

from core.gadgets import BOOTS, DECOY
from core.scoring import rank_title
from ui import styles
from ui.base_screen import BaseScreen


def outcome_sentence(run) -> str:
    """A short, friendly summary of how the mission went."""
    if run.pro_mode:
        return "Pro mode, no guidance, and nobody saw a thing. That was real planning."
    if run.mission.drones and run.waits:
        return f"Clean extraction. You waited {run.waits} turn(s) in the shadows and the drones never knew."
    if run.alert_triggered and run.carries_decoy:
        return "The alarm screamed, but your decoy took the blame. Smooth work."
    if run.alert_triggered:
        return "You made it out through the alert. A decoy would have kept your record clean."
    if BOOTS in run.kit_ids and any("~" in line for line in run.mission.grid):
        return "Clean extraction. Your boots made the static fields easy."
    if run.score.prep_bonus == 150:
        return "Clean extraction with a perfectly prepared kit."
    return "Clean extraction. The facility never knew you were there."


class DebriefScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(40, 22, 40, 8))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="MISSION DEBRIEF", style="Dim.TLabel",
                  font=styles.font(10, "bold")).grid(row=0, column=0, sticky="w")
        self.title_label = ttk.Label(header, text="", style="Title.TLabel")
        self.title_label.grid(row=1, column=0, sticky="w")
        self.outcome = ttk.Label(header, text="", style="Subtitle.TLabel", wraplength=900)
        self.outcome.grid(row=2, column=0, sticky="w", pady=(2, 0))

        body = ttk.Frame(self, padding=(40, 6, 40, 6))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1, uniform="d")
        body.columnconfigure(1, weight=1, uniform="d")
        body.rowconfigure(0, weight=1)

        # Left panel: score and rank
        score_panel = ttk.Frame(body, style="Panel.TFrame", padding=20)
        score_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        score_panel.columnconfigure(0, weight=1)
        ttk.Label(score_panel, text="Final score", style="PanelDim.TLabel").grid(
            row=0, column=0, sticky="w")
        self.score_label = ttk.Label(score_panel, text="0", style="Big.TLabel")
        self.score_label.grid(row=1, column=0, sticky="w")
        self.rank_label = ttk.Label(score_panel, text="", style="PanelWarn.TLabel")
        self.rank_label.grid(row=2, column=0, sticky="w", pady=(0, 12))
        self.breakdown = tk.Frame(score_panel, bg=styles.PANEL)
        self.breakdown.grid(row=3, column=0, sticky="ew")
        self.breakdown.columnconfigure(0, weight=1)

        # Right panel: run facts
        facts = ttk.Frame(body, style="Panel.TFrame", padding=20)
        facts.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        facts.columnconfigure(1, weight=1)
        self.facts = {}
        for i, name in enumerate(("Mission", "Operative", "Result", "Moves", "Total effort",
                                  "Kit used", "Alert", "Record")):
            ttk.Label(facts, text=name, style="PanelDim.TLabel").grid(
                row=i, column=0, sticky="nw", padx=(0, 16), pady=4)
            value = ttk.Label(facts, text="", style="PanelValue.TLabel", wraplength=300,
                              justify="left")
            value.grid(row=i, column=1, sticky="nw", pady=4)
            self.facts[name] = value

        buttons = ttk.Frame(self, padding=(40, 8, 40, 20))
        buttons.grid(row=2, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        ttk.Button(buttons, text="Main Menu", command=lambda: app.show("menu")).grid(
            row=0, column=1, padx=(0, 10))
        ttk.Button(buttons, text="Choose Another Mission",
                   command=self.choose_another).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(buttons, text="Play Again", style="Accent.TButton",
                   command=self.play_again).grid(row=0, column=3)

    def on_show(self, **kwargs) -> None:
        run = self.app.run
        if run is None or run.score is None:
            return
        score = run.score
        self.title_label.configure(text=f"{run.mission.name} — Success")
        self.outcome.configure(text=outcome_sentence(run))
        self.score_label.configure(text=str(score.total))
        self.rank_label.configure(text=f"Rank: {rank_title(score.total)}")

        for child in self.breakdown.winfo_children():
            child.destroy()
        for row, (label, amount) in enumerate(score.lines()):
            colour = styles.TEXT if amount >= 0 else styles.AMBER
            tk.Label(self.breakdown, text=label, bg=styles.PANEL, fg=styles.TEXT_DIM,
                     font=styles.font(10)).grid(row=row, column=0, sticky="w", pady=1)
            sign = "+" if amount >= 0 else "−"
            tk.Label(self.breakdown, text=f"{sign}{abs(amount)}", bg=styles.PANEL, fg=colour,
                     font=styles.font(10, "bold")).grid(row=row, column=1, sticky="e")
        last = len(score.lines())
        tk.Frame(self.breakdown, bg=styles.BORDER, height=1).grid(
            row=last, column=0, columnspan=2, sticky="ew", pady=4)
        tk.Label(self.breakdown, text="Total (never below 0)", bg=styles.PANEL, fg=styles.TEXT,
                 font=styles.font(10, "bold")).grid(row=last + 1, column=0, sticky="w")
        tk.Label(self.breakdown, text=str(score.total), bg=styles.PANEL, fg=styles.ACCENT,
                 font=styles.font(10, "bold")).grid(row=last + 1, column=1, sticky="e")

        self.facts["Mission"].configure(text=f"{run.mission.name} ({run.mission.difficulty})")
        self.facts["Operative"].configure(text=run.player_name)
        self.facts["Result"].configure(text="Objective secured and extracted",
                                       style="PanelGood.TLabel")
        self.facts["Moves"].configure(text=str(run.moves))
        self.facts["Total effort"].configure(text=str(run.effort))
        self.facts["Kit used"].configure(text=run.kit_text)
        if run.alert_triggered:
            alert = "Yes — penalty cancelled by decoy" if DECOY in run.kit_ids else "Yes"
            self.facts["Alert"].configure(text=alert, style="PanelAlert.TLabel")
        else:
            self.facts["Alert"].configure(text="No", style="PanelValue.TLabel")
        self.facts["Record"].configure(text=self.app.last_save_message or "-")

    def play_again(self) -> None:
        """Same mission, back to the preparation screen."""
        self.app.run = None
        self.app.show("preparation")

    def choose_another(self) -> None:
        self.app.run = None
        self.app.show("mission_select")
