"""Main Gameplay screen: the map on the left, mission status and controls on the right.

Every move goes through the MissionRun engine; this screen only reacts to
buttons and keys, calls the engine, and redraws.

Real-time clock: every config.TICK_MS (0.5 s) tick() runs one turn. The drones
advance one tile, and the player makes the move chosen since the last tick
(an arrow key, Move Next Step, or Auto Travel) or stands still. Once the player
has planned a route, Dijkstra re-plans it on every tick where it went out of
date, so the route on the map always matches where the drones are now.
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
    ge.CAUGHT: ("Spotted — mission failed", "PanelAlert.TLabel"),
}

ARROW_KEYS = {"Up": (-1, 0), "Right": (0, 1), "Down": (1, 0), "Left": (0, -1)}
SHORTCUTS = {"p": "plan", "space": "step", "a": "auto", "Escape": "stop", "c": "collect",
             "Return": "pause", "h": "hack"}
FOLLOW_ROUTE = "route"      # queued action: take the next step of the planned route
FINISH_DELAY_MS = 600       # short pause on the extraction tile before the debrief


def friendly_position(pos) -> str:
    """(row, col) -> 'Sector C-4' (column letter, row number from 1)."""
    return f"Sector {chr(ord('A') + pos[1])}-{pos[0] + 1}"


class GameplayScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.run = None
        self.tick_id = None           # pending clock tick
        self.finish_id = None         # pending "go to debrief" callback
        self.auto_running = False     # Auto Travel: follow the route on every tick
        self.queued = None            # move for the next tick: a tile or FOLLOW_ROUTE
        self.guided = False           # a route was planned: keep re-planning it live
        self.paused = False

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0, minsize=330)
        self.rowconfigure(0, weight=1)

        # ---- left: map + legend
        left = ttk.Frame(self, padding=(16, 10, 8, 6))
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        self.map_title = ttk.Label(left, text="", style="Heading.TLabel")
        self.map_title.grid(row=0, column=0, sticky="w")
        self.map_view = MapView(left)
        self.map_view.grid(row=1, column=0, sticky="nsew", pady=(4, 4))
        self.legend = Legend(left)
        self.legend.grid(row=2, column=0, sticky="ew")

        # ---- right: sidebar
        side = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        side.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=10)
        side.columnconfigure(0, weight=1)

        self.mission_label = ttk.Label(side, text="", style="PanelHeading.TLabel")
        self.mission_label.grid(row=0, column=0, sticky="w")

        info = ttk.Frame(side, style="Panel.TFrame")
        info.grid(row=1, column=0, sticky="ew", pady=(4, 2))
        info.columnconfigure(1, weight=1)
        self.rows = {}
        names = ("Player", "Objective", "Position", "Route", "Guidance", "Moves", "Effort",
                 "Status", "Security", "Event")
        for i, name in enumerate(names):
            self.rows[name] = InfoRow(info, i, name, wraplength=215)

        self.message = ttk.Label(side, text="", style="PanelDim.TLabel", wraplength=290,
                                 justify="left")
        self.message.grid(row=2, column=0, sticky="ew", pady=(2, 6))

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
            ("pause", "Pause  [Enter]", self.toggle_pause, 2, 0, "TButton"),
            ("collect", "Collect Objective  [C]", self.collect, 2, 1, "Accent.TButton"),
            ("hack", "Hack Terminal  [H]", self.open_terminal, 3, 0, "Accent.TButton"),
            ("restart", "Restart Mission", self.restart, 4, 0, "TButton"),
            ("menu", "Return to Menu", self.return_to_menu, 4, 1, "TButton"),
        ]
        for key, text, command, row, col, style in layout:
            # takefocus=False: a focused button would also react to Space, and
            # Space is already the Move Next Step shortcut.
            button = ttk.Button(buttons, text=text, command=command, style=style,
                                takefocus=False)
            button.grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else 4, 0),
                        pady=2)
            self.buttons[key] = button

        self.hint = ttk.Label(side, text="",
                              style="PanelDim.TLabel", wraplength=290)
        self.hint.grid(row=4, column=0, sticky="w", pady=(6, 0))

    # ------------------------------------------------------------ screen life cycle
    def on_show(self, from_terminal: bool = False, **kwargs) -> None:
        self.cancel_timers()
        self.run = self.app.run
        if self.run is None:
            return
        run = self.run
        mission = run.mission
        pro = "  ·  PRO MODE" if run.pro_mode else ""
        self.map_title.configure(text=f"{mission.name}  ·  {mission.difficulty}{pro}")
        self.mission_label.configure(text=mission.name)
        self.legend.show_for(mission, show_preview=not run.pro_mode)
        if mission.has_terminal:
            self.buttons["hack"].grid()
        else:
            self.buttons["hack"].grid_remove()
        if from_terminal:
            self.set_message(self.app.terminal_message, warn=not run.terminal_solved)
            self.replan_if_guided()
        else:
            self.guided = False
            self.paused = False
            self.queued = None
            if run.pro_mode:
                self.set_message("Pro mode: no route guidance and no preview. Read the "
                                 "drones and move with the arrow keys.")
            else:
                self.set_message("Press Plan Route to see the safest way to your target.")
        if run.pro_mode:
            self.hint.configure(text="Drones move every 0.5 s. Arrow keys: one tile per "
                                     "tick. No key = stand still. Enter pauses.")
        else:
            self.hint.configure(text="Drones move every 0.5 s. Arrow keys: one tile per "
                                     "tick. Enter pauses.")
        self.refresh()
        self.start_clock()

    def on_hide(self) -> None:
        self.cancel_timers()

    def can_leave(self) -> bool:
        """Leaving after at least one move asks "Abandon mission?" and saves it once."""
        if self.app.next_screen == "terminal":
            self.cancel_timers()           # going to the terminal is part of the mission
            return True
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
        """Cancel every pending after() callback (Restart, Menu, terminal, close)."""
        self.auto_running = False
        self.stop_clock()
        if self.finish_id is not None:
            self.after_cancel(self.finish_id)
            self.finish_id = None

    # ------------------------------------------------------------ keyboard
    def handle_key(self, key: str) -> None:
        if self.run is None:
            return
        name = SHORTCUTS.get(key) or SHORTCUTS.get(key.lower())
        if name is not None:
            if self.buttons[name].instate(["!disabled"]) and self.buttons[name].winfo_ismapped():
                self.buttons[name].invoke()
        elif key in ARROW_KEYS and not self.auto_running and self.run.is_active:
            d_row, d_col = ARROW_KEYS[key]
            row, col = self.run.position
            self.queued = (row + d_row, col + d_col)     # made on the next tick

    # ------------------------------------------------------------ clock
    def start_clock(self) -> None:
        """Schedule the next tick (nothing while paused or after the run ended)."""
        self.stop_clock()
        run = self.run
        if run is None or not run.is_active or self.paused:
            return
        token = run.run_token
        self.tick_id = self.after(config.TICK_MS, lambda: self.tick(token))

    def stop_clock(self) -> None:
        if self.tick_id is not None:
            self.after_cancel(self.tick_id)
            self.tick_id = None

    def tick(self, token: int) -> None:
        """Half a second has passed: one turn for the player and the drones.

        The token guard stops a tick of an old (restarted) run.
        """
        self.tick_id = None
        run = self.run
        if run is None or token != run.run_token or not run.is_active or self.paused:
            return
        if self.auto_running or self.queued == FOLLOW_ROUTE:
            target = None if run.has_valid_route() else run.position
        elif self.queued is not None:
            target = self.queued
        else:
            target = run.position                     # no key pressed: stand still
        self.queued = None
        self.do_step(target)
        if run is not self.run or not run.is_active:
            return                                    # caught, completed or left
        if self.auto_running and not run.has_valid_route():
            self.auto_running = False                 # arrived at the end of the route
        self.replan_if_guided()
        self.refresh()
        self.start_clock()

    def replan_if_guided(self) -> None:
        """Dijkstra again from here and now when the planned route is out of date."""
        run = self.run
        if (self.guided and run is not None and run.is_active and not run.pro_mode
                and not run.has_valid_route()):
            run.plan_route(quiet=True)

    # ------------------------------------------------------------ actions
    def plan_route(self) -> None:
        run = self.run
        if run is None or not run.is_active or run.pro_mode:
            return
        result = run.plan_route()
        self.guided = result.found
        if not result.found:
            self.no_route()
        elif run.route_goal == ge.ROUTE_TO_TERMINAL:
            self.set_message("Lasers block every way in. Route planned to the terminal "
                             "first.", warn=True)
        else:
            self.set_message(f"Route planned to {self.target_name()}.")
        self.refresh()

    def move_next_step(self) -> None:
        """Take the next step of the planned route on the next tick."""
        if self.run is not None and not self.auto_running and self.run.has_valid_route():
            self.queued = FOLLOW_ROUTE

    def toggle_pause(self) -> None:
        run = self.run
        if run is None or not run.is_active:
            return
        self.paused = not self.paused
        if self.paused:
            self.stop_clock()
            self.set_message("Paused - the drones are frozen. Press Enter to resume.")
        else:
            self.set_message("Resumed.")
            self.start_clock()
        self.refresh()

    def do_step(self, target) -> bool:
        """One tick in the engine; report a refusal; handle the outcome.

        A refused move (wall, locked door, laser) still uses up the tick:
        the player stands still while the drones move.
        """
        run = self.run
        old_pos = run.position
        result = run.step(target)
        refused = not result.ok
        if refused:
            self.set_message(result.reason, warn=True)
            self.auto_running = False
            result = run.step(run.position)
            if not result.ok:
                self.refresh()
                return False
        if result.caught:
            self.cancel_timers()
            _, self.app.last_save_message = self.app.save_run(run)
            self.set_message(f"{result.reason} Mission failed. Restart Mission to try "
                             "again.", warn=True)
            self.refresh()
            messagebox.showwarning("Spotted!", f"{result.reason}\n\nThe mission has failed. "
                                   "Study the patrol and try again.", parent=self)
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
        if refused or run.position == old_pos:
            pass                       # nothing new to say on a tick spent standing still
        elif result.picked_key:
            self.set_message("Keycard acquired — locked doors will open for you.")
        elif run.can_hack():
            self.set_message("You reached the terminal. Press Hack Terminal [H].")
        elif run.position == run.mission.objective and not run.objective_collected:
            self.set_message(f"You are at the {run.mission.objective_name}. "
                             "Press Collect Objective.")
        elif run.position == run.mission.exit and not run.objective_collected:
            self.set_message("This is the extraction point, but you do not have the "
                             "objective yet.", warn=True)
        elif self.auto_running:
            self.set_message("Auto Travel engaged.")
        else:
            self.set_message("")
        self.refresh()
        return not refused

    def start_auto_travel(self) -> None:
        """Follow the planned route, one step on every tick."""
        run = self.run
        if run is None or self.auto_running or not run.has_valid_route():
            return
        self.auto_running = True
        self.queued = None
        self.set_message("Auto Travel engaged.")
        self.refresh()

    def stop_auto_travel(self) -> None:
        if self.auto_running:
            self.auto_running = False
            self.set_message("Auto Travel stopped.")
            self.refresh()

    def collect(self) -> None:
        run = self.run
        if run is None or not run.can_collect():
            return
        run.collect_objective()
        self.set_message(f"The {run.mission.objective_name} is secured. Now get to "
                         "extraction.")
        self.replan_if_guided()
        self.refresh()

    def open_terminal(self) -> None:
        run = self.run
        if run is None or not run.can_hack():
            return
        self.stop_auto_travel()
        self.app.show("terminal")

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
        if run.moves > 0 and run.is_active:
            if not messagebox.askyesno("Restart mission?",
                                       "Start this mission again from the beginning?",
                                       parent=self):
                return
        self.cancel_timers()
        run.restart()
        self.guided = False
        self.paused = False
        self.queued = None
        self.set_message("Mission restarted. The facility is back to normal.")
        self.refresh()
        self.start_clock()

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

    def security_text(self) -> str:
        """Keycard, lasers and drones in one short line."""
        run = self.run
        mission = run.mission
        parts = []
        if mission.has_keycard:
            parts.append("Keycard ✓" if run.has_key else "Keycard ✕")
        if mission.has_terminal:
            parts.append("Lasers OFF" if run.terminal_solved else "Lasers ON")
        if mission.drones:
            parts.append(f"{len(mission.drones)} drones patrolling")
        return "  ·  ".join(parts) if parts else "-"

    def refresh(self) -> None:
        """Update every sidebar value and every button state, then redraw the map."""
        run = self.run
        if run is None:
            return
        self.rows["Player"].set(run.player_name)
        self.rows["Objective"].set(run.target_label)
        self.rows["Position"].set(friendly_position(run.position))
        if run.pro_mode:
            self.rows["Route"].set("Pro mode — no route guidance", "PanelWarn.TLabel")
            self.rows["Guidance"].set("You are on your own")
        elif run.has_valid_route():
            waits = run.route_waits()
            wait_text = f" ({waits} waits)" if waits else ""
            goal = " to the terminal" if run.route_goal == ge.ROUTE_TO_TERMINAL else ""
            self.rows["Route"].set(f"Planned route{goal}: {run.route.steps} steps{wait_text}, "
                                   f"effort {run.route.cost}", "PanelAccent.TLabel")
            direction = run.next_direction()
            text = "Next: wait" if direction == "Wait" else f"Next: move {direction}"
            self.rows["Guidance"].set(text, "PanelAccent.TLabel")
        else:
            self.rows["Route"].set("No route planned")
            self.rows["Guidance"].set("Press Plan Route" if run.is_active else "-")
        self.rows["Moves"].set(f"{run.moves}" + (f"  ({run.waits} waits)" if run.waits else ""))
        self.rows["Effort"].set(str(run.effort))
        text, style = STATUS_TEXT[run.status]
        if run.status == ge.CAUGHT and run.spotted_by:
            text = f"Spotted by the {run.spotted_by}"
        elif self.paused and run.is_active:
            text, style = "Paused", "PanelWarn.TLabel"
        self.rows["Status"].set(text, style)
        self.rows["Security"].set(self.security_text(), "PanelWarn.TLabel")
        if run.is_caught():
            self.rows["Event"].set("Mission failed", "PanelAlert.TLabel")
        elif (not run.pro_mode and run.is_active
              and run.position in run.watched_next_turn()):
            self.rows["Event"].set("Danger: a drone looks HERE on the next tick!",
                                   "PanelAlert.TLabel")
        else:
            self.rows["Event"].set("All clear", "PanelGood.TLabel")

        active = run.is_active
        guided = active and not run.pro_mode
        route_ok = guided and run.has_valid_route()
        auto = self.auto_running
        self.set_enabled("plan", guided and not auto)
        self.set_enabled("step", route_ok and not auto)
        self.set_enabled("auto", route_ok and not auto)
        self.set_enabled("stop", auto)
        self.set_enabled("pause", active)
        self.buttons["pause"].configure(text="Resume  [Enter]" if self.paused
                                        else "Pause  [Enter]")
        self.set_enabled("collect", run.can_collect() and not auto)
        self.set_enabled("hack", run.can_hack() and not auto)
        self.set_enabled("restart", run.status != ge.COMPLETED)
        self.set_enabled("menu", run.status != ge.COMPLETED)
        self.map_view.show_run(run)

    def set_enabled(self, name: str, enabled: bool) -> None:
        self.buttons[name].state(["!disabled"] if enabled else ["disabled"])
