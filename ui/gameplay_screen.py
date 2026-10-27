"""Main Gameplay screen: the map on the left, mission status and controls on the right.

Every move goes through the MissionRun engine; this screen only reacts to
buttons and keys, calls the engine, and redraws.
"""

from tkinter import messagebox, ttk

from core import config
from core import game_engine as ge
from ui.base_screen import BaseScreen
from ui.map_view import Legend, MapView
from ui.widgets import InfoRow

STATUS_TEXT = {
    ge.PLANNING: ("Ready — plan your route", "PanelValue.TLabel"),
    ge.IN_PROGRESS: ("In progress", "PanelAccent.TLabel"),
    ge.OBJECTIVE_SECURED: ("Objective secured", "PanelWarn.TLabel"),
    ge.COMPLETED: ("Mission complete", "PanelGood.TLabel"),
    ge.ABANDONED: ("Abandoned", "PanelAlert.TLabel"),
    ge.NO_ROUTE: ("No safe route from here", "PanelAlert.TLabel"),
}

ARROW_KEYS = {"Up": (-1, 0), "Right": (0, 1), "Down": (1, 0), "Left": (0, -1)}
FINISH_DELAY_MS = 600       # short pause on the extraction tile before the debrief


def friendly_position(pos) -> str:
    """(row, col) -> 'Sector C-4' (column letter, row number from 1)."""
    return f"Sector {chr(ord('A') + pos[1])}-{pos[0] + 1}"


class GameplayScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.run = None
        self.after_id = None          # pending Auto Travel callback
        self.finish_id = None         # pending "go to debrief" callback
        self.auto_running = False

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0, minsize=330)
        self.rowconfigure(0, weight=1)

        # ---- left: map + legend
        left = ttk.Frame(self, padding=(16, 12, 8, 8))
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        self.map_title = ttk.Label(left, text="", style="Heading.TLabel")
        self.map_title.grid(row=0, column=0, sticky="w")
        self.map_view = MapView(left)
        self.map_view.grid(row=1, column=0, sticky="nsew", pady=(6, 6))
        self.legend = Legend(left)
        self.legend.grid(row=2, column=0, sticky="ew")

        # ---- right: sidebar
        side = ttk.Frame(self, style="Panel.TFrame", padding=(16, 12))
        side.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=12)
        side.columnconfigure(0, weight=1)

        self.mission_label = ttk.Label(side, text="", style="PanelHeading.TLabel")
        self.mission_label.grid(row=0, column=0, sticky="w")

        info = ttk.Frame(side, style="Panel.TFrame")
        info.grid(row=1, column=0, sticky="ew", pady=(6, 4))
        info.columnconfigure(1, weight=1)
        self.rows = {}
        names = ("Player", "Objective", "Position", "Route", "Guidance", "Moves", "Effort",
                 "Status", "Kit", "Event")
        for i, name in enumerate(names):
            self.rows[name] = InfoRow(info, i, name, wraplength=215)

        self.message = ttk.Label(side, text="", style="PanelDim.TLabel", wraplength=290,
                                 justify="left")
        self.message.grid(row=2, column=0, sticky="ew", pady=(4, 8))

        buttons = ttk.Frame(side, style="Panel.TFrame")
        buttons.grid(row=3, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1, uniform="btn")
        buttons.columnconfigure(1, weight=1, uniform="btn")
        self.buttons = {}
        layout = [
            ("plan", "Plan Route  [P]", self.plan_route, 0, 0, "Accent.TButton"),
            ("step", "Move Next Step  [Space]", self.move_next_step, 0, 1, "TButton"),
            ("auto", "Auto Travel  [A]", self.start_auto_travel, 1, 0, "TButton"),
            ("stop", "Stop  [Esc]", self.stop_auto_travel, 1, 1, "TButton"),
            ("collect", "Collect Objective  [C]", self.collect, 2, 0, "Accent.TButton"),
            ("alert", "Trigger Alert", self.trigger_alert, 2, 1, "Danger.TButton"),
            ("restart", "Restart Mission", self.restart, 3, 0, "TButton"),
            ("menu", "Return to Menu", self.return_to_menu, 3, 1, "TButton"),
        ]
        for key, text, command, row, col, style in layout:
            button = ttk.Button(buttons, text=text, command=command, style=style)
            button.grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else 4, 0),
                        pady=3)
            self.buttons[key] = button

        ttk.Label(side, text="Arrow keys move one tile by hand.",
                  style="PanelDim.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 0))

    # ------------------------------------------------------------ screen life cycle
    def on_show(self, **kwargs) -> None:
        self.cancel_timers()
        self.run = self.app.run
        if self.run is None:
            return
        mission = self.run.mission
        self.map_title.configure(text=f"{mission.name}  ·  {mission.difficulty}")
        self.mission_label.configure(text=mission.name)
        if mission.has_alert:
            self.buttons["alert"].grid()
        else:
            self.buttons["alert"].grid_remove()
        self.set_message("Press Plan Route to see the safest way to your target.")
        self.refresh()

    def on_hide(self) -> None:
        self.cancel_timers()

    def can_leave(self) -> bool:
        """Leaving after at least one move asks "Abandon mission?" and saves it once."""
        run = self.run
        if run is None or not run.needs_abandon_save():
            self.cancel_timers()
            return True
        was_running = self.auto_running
        self.stop_auto_travel()
        if not messagebox.askyesno("Abandon mission?",
                                   "Leave this mission now? It will be recorded as "
                                   "abandoned with a score of 0.", parent=self):
            if was_running:
                self.set_message("Auto Travel paused.")
            return False
        run.abandon()
        run_id, text = self.app.save_run(run)
        if run_id is None:
            messagebox.showwarning("Not saved", text, parent=self)
        self.app.run = None
        self.run = None
        return True

    def cancel_timers(self) -> None:
        """Cancel every pending after() callback (Stop, Restart, Menu, close)."""
        self.auto_running = False
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
        if self.finish_id is not None:
            self.after_cancel(self.finish_id)
            self.finish_id = None

    # ------------------------------------------------------------ keyboard
    def handle_key(self, key: str) -> None:
        if self.run is None:
            return
        shortcuts = {"p": "plan", "P": "plan", "space": "step", "a": "auto", "A": "auto",
                     "Escape": "stop", "c": "collect", "C": "collect"}
        if key in shortcuts:
            name = shortcuts[key]
            if self.buttons[name].instate(["!disabled"]):
                self.buttons[name].invoke()
        elif key in ARROW_KEYS and not self.auto_running:
            d_row, d_col = ARROW_KEYS[key]
            row, col = self.run.position
            self.do_step((row + d_row, col + d_col))

    # ------------------------------------------------------------ actions
    def plan_route(self) -> None:
        run = self.run
        if run is None or not run.is_active:
            return
        result = run.plan_route()
        if result.found:
            self.set_message(f"Route planned to {self.target_name()}.")
        else:
            self.no_route()
        self.refresh()

    def move_next_step(self) -> None:
        if self.run is not None and not self.auto_running:
            self.do_step(None)

    def do_step(self, target) -> bool:
        """Ask the engine for one move; report a refusal; handle completion."""
        run = self.run
        result = run.step(target)
        if not result.ok:
            self.set_message(result.reason, warn=True)
            self.refresh()
            return False
        if result.completed:
            self.cancel_timers()
            # Save right away (exactly once), so the result is never lost even
            # if the player leaves before the debrief appears.
            _, self.app.last_save_message = self.app.save_run(run)
            self.set_message("Extraction reached. Mission complete!")
            self.refresh()
            token = run.run_token
            self.finish_id = self.after(FINISH_DELAY_MS, lambda: self.open_debrief(token))
            return True
        if run.position == run.mission.objective and not run.objective_collected:
            self.set_message(f"You are at the {run.mission.objective_name}. "
                             "Press Collect Objective.")
        elif run.position == run.mission.exit and not run.objective_collected:
            self.set_message("This is the extraction point, but you do not have the "
                             "objective yet.", warn=True)
        else:
            self.set_message("")
        self.refresh()
        return True

    def start_auto_travel(self) -> None:
        run = self.run
        if run is None or self.auto_running or not run.has_valid_route():
            return
        self.auto_running = True
        self.set_message("Auto Travel engaged.")
        self.refresh()
        self.schedule_auto_step(run.run_token)

    def schedule_auto_step(self, token: int) -> None:
        self.after_id = self.after(config.AUTO_TRAVEL_DELAY_MS,
                                   lambda: self.auto_step(token))

    def auto_step(self, token: int) -> None:
        """One animated step. The token guard stops callbacks from an old run."""
        self.after_id = None
        run = self.run
        if not self.auto_running or run is None or token != run.run_token:
            return
        moved = self.do_step(None)
        if moved and self.auto_running and run.has_valid_route():
            self.schedule_auto_step(token)
        else:
            self.auto_running = False
            self.refresh()

    def stop_auto_travel(self) -> None:
        if self.auto_running or self.after_id is not None:
            self.auto_running = False
            if self.after_id is not None:
                self.after_cancel(self.after_id)
                self.after_id = None
            self.set_message("Auto Travel stopped.")
            self.refresh()

    def collect(self) -> None:
        run = self.run
        if run is None or not run.can_collect():
            return
        alert_fired = run.collect_objective()
        name = run.mission.objective_name
        if alert_fired:
            self.after_alert(f"The {name} is yours — but an ALERT sealed the relay "
                             "gate! Route to extraction recalculated.")
        else:
            self.set_message(f"The {name} is secured. Now plan your route to extraction.")
            self.refresh()

    def trigger_alert(self) -> None:
        run = self.run
        if run is None or not run.can_trigger_alert():
            return
        self.stop_auto_travel()
        run.trigger_alert()
        self.after_alert("ALERT raised early — the relay gate is sealed. "
                         "Route recalculated.")

    def after_alert(self, text: str) -> None:
        """The engine already sealed the gate and re-planned; show the result."""
        self.cancel_timers()
        if self.run.status == ge.NO_ROUTE:
            self.no_route()
        else:
            self.set_message(text, warn=True)
        self.refresh()

    def no_route(self) -> None:
        self.cancel_timers()
        self.set_message("No safe route from here. Restart the mission or return to "
                         "the menu.", warn=True)
        messagebox.showwarning("No safe route", "No safe route from here.\n"
                               "Use Restart Mission or Return to Menu.", parent=self)

    def restart(self) -> None:
        run = self.run
        if run is None:
            return
        if run.moves > 0 and run.status != ge.COMPLETED:
            if not messagebox.askyesno("Restart mission?",
                                       "Start this mission again from the beginning?",
                                       parent=self):
                return
        self.cancel_timers()
        run.restart()
        self.set_message("Mission restarted. The facility is back to normal.")
        self.refresh()

    def return_to_menu(self) -> None:
        self.app.show("menu")

    def open_debrief(self, token: int) -> None:
        self.finish_id = None
        if self.run is None or self.run.run_token != token or not self.run.is_complete():
            return
        self.app.show("debrief")

    # ------------------------------------------------------------ display
    def target_name(self) -> str:
        if self.run.objective_collected:
            return "extraction"
        return f"the {self.run.mission.objective_name}"

    def set_message(self, text: str, warn: bool = False) -> None:
        self.message.configure(text=text, style="PanelWarn.TLabel" if warn
                               else "PanelDim.TLabel")

    def refresh(self) -> None:
        """Update every sidebar value and every button state, then redraw the map."""
        run = self.run
        if run is None:
            return
        self.rows["Player"].set(run.player_name)
        self.rows["Objective"].set(run.target_label)
        self.rows["Position"].set(friendly_position(run.position))
        if run.has_valid_route():
            self.rows["Route"].set(f"Planned route: {run.route.steps} steps, "
                                   f"effort {run.route.cost}", "PanelAccent.TLabel")
            self.rows["Guidance"].set(f"Next: move {run.next_direction()}",
                                      "PanelAccent.TLabel")
        else:
            self.rows["Route"].set("No route planned")
            self.rows["Guidance"].set("Press Plan Route" if run.is_active else "-")
        self.rows["Moves"].set(str(run.moves))
        self.rows["Effort"].set(str(run.effort))
        text, style = STATUS_TEXT[run.status]
        self.rows["Status"].set(text, style)
        self.rows["Kit"].set(run.kit_text)
        if run.alert_triggered:
            self.rows["Event"].set("ALERT — relay gate sealed, route recalculated",
                                   "PanelAlert.TLabel")
        elif run.weak_point_visible:
            self.rows["Event"].set("All clear — weak point spotted at the relay gate",
                                   "PanelWarn.TLabel")
        else:
            self.rows["Event"].set("All clear", "PanelGood.TLabel")

        active = run.is_active
        route_ok = active and run.has_valid_route()
        auto = self.auto_running
        self.set_enabled("plan", active and not auto)
        self.set_enabled("step", route_ok and not auto)
        self.set_enabled("auto", route_ok and not auto)
        self.set_enabled("stop", auto)
        self.set_enabled("collect", run.can_collect() and not auto)
        self.set_enabled("alert", run.can_trigger_alert())
        self.set_enabled("restart", run.status != ge.COMPLETED)
        self.set_enabled("menu", run.status != ge.COMPLETED)
        self.map_view.show_run(run)

    def set_enabled(self, name: str, enabled: bool) -> None:
        self.buttons[name].state(["!disabled"] if enabled else ["disabled"])
