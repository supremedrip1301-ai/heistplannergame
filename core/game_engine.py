"""Game state for one attempt at a mission (the MissionRun state machine).

The engine has no Tkinter imports, so every rule can be unit-tested without
opening a window. The UI only calls these methods and redraws.

Status flow
    PLANNING -> IN_PROGRESS -> OBJECTIVE_SECURED -> COMPLETED
    any active status -> ABANDONED (player leaves after moving)
    any active status -> NO_ROUTE  (no safe route left; restart or leave)
    any active status -> CAUGHT    (a patrol drone saw the player)

Turns
    Every move AND every Wait is one turn. After each turn the patrol drones
    advance one tile and the engine checks whether any drone can see the player.
"""

import logging
import random

from core import config
from core.drones import drone_clock_period, is_detected, watched_tiles
from core.missions import DOOR, KEYCARD, LASER, build_tile_costs
from core.pathfinding import RouteResult, is_walkable, step_direction
from core.puzzles import make_puzzle
from core.scoring import calculate_score
from core.state_planner import WAIT_COST, PlanContext, count_waits, plan_state_route

logger = logging.getLogger(__name__)

PLANNING = "PLANNING"
IN_PROGRESS = "IN_PROGRESS"
OBJECTIVE_SECURED = "OBJECTIVE_SECURED"
COMPLETED = "COMPLETED"
ABANDONED = "ABANDONED"
NO_ROUTE = "NO_ROUTE"
CAUGHT = "CAUGHT"

ACTIVE_STATUSES = (PLANNING, IN_PROGRESS, OBJECTIVE_SECURED)
FINISHED_STATUSES = (COMPLETED, ABANDONED, CAUGHT)

RESULT_SUCCESS = "SUCCESS"
RESULT_ABANDONED = "ABANDONED"
RESULT_CAUGHT = "CAUGHT"

ROUTE_TO_TARGET = "target"
ROUTE_TO_TERMINAL = "terminal"

# The database still has the kit / alert columns of the first version of the
# game, so old records stay readable. New runs always store these values.
NO_KIT = "None"


class StepResult:
    """What happened when the player tried to move one tile (or wait)."""

    def __init__(self, ok: bool, reason: str = "", completed: bool = False,
                 caught: bool = False, picked_key: bool = False):
        self.ok = ok
        self.reason = reason          # friendly text when the move was refused
        self.completed = completed    # True when this step finished the mission
        self.caught = caught          # a drone saw the player: mission failed
        self.picked_key = picked_key  # the keycard was picked up on this step

    def __bool__(self):
        return self.ok

    def __repr__(self):
        return (f"StepResult(ok={self.ok}, reason={self.reason!r}, completed={self.completed}, "
                f"caught={self.caught})")


class MissionRun:
    """All state of one run of one mission, plus the rules that change it."""

    def __init__(self, player_name: str, mission, pro_mode: bool = False, puzzle_seed=None):
        self.player_name = player_name
        self.mission = mission                     # read-only map and story
        self.tile_costs = build_tile_costs()
        self.pro_mode = pro_mode                   # no route guidance, bigger score
        if puzzle_seed is None:
            puzzle_seed = random.randrange(1_000_000_000)
        self.puzzle_seed = puzzle_seed             # fixed seed -> same puzzle in tests
        self.drone_period = drone_clock_period(mission.drones)
        self.run_token = 0                         # increases on every restart
        self.reset_state()

    # ------------------------------------------------------------ state
    def reset_state(self) -> None:
        """Put every changeable value back to the start of a run."""
        self.position = self.mission.start
        self.objective_collected = False
        self.status = PLANNING
        self.moves = 0                             # turns taken (moves + waits)
        self.waits = 0
        self.effort = 0
        self.route = None                          # RouteResult or None
        self.route_goal = ROUTE_TO_TARGET
        self.score = None                          # ScoreBreakdown when completed
        self.result_saved = False
        self.clock = 0                             # drone clock = turns taken
        self.has_key = False
        self.terminal_solved = False
        self.puzzle = None                         # created when the terminal is opened
        self.wrong_answers = 0
        self.spotted_by = ""                       # name of the drone that caught us

    def restart(self) -> None:
        """Start the same mission again (drones, keycard, lasers and puzzle reset)."""
        self.run_token = self.run_token + 1
        self.reset_state()
        logger.info("Run restarted: %s (token %d)", self.mission.mission_id, self.run_token)

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    @property
    def current_target(self):
        """The objective until it is collected, then the extraction point."""
        if self.objective_collected:
            return self.mission.exit
        return self.mission.objective

    @property
    def target_label(self) -> str:
        if self.objective_collected:
            return "Reach extraction"
        return f"Reach the {self.mission.objective_name}"

    @property
    def lasers_on(self) -> bool:
        return self.mission.has_terminal and not self.terminal_solved

    def blocked_tiles(self) -> set:
        """Tiles that cannot be entered right now (active lasers).

        Locked doors are handled by the planner through the keycard state.
        The tile the character stands on is never treated as blocked.
        """
        blocked = set()
        if self.lasers_on:
            blocked |= set(self.mission.laser_tiles())
        return blocked - {self.position}

    # ------------------------------------------------------------ drones
    def drone_positions(self) -> list:
        return [(drone, drone.position(self.clock)) for drone in self.mission.drones]

    def watched_now(self) -> set:
        return watched_tiles(self.mission.drones, self.clock, self.mission.grid)

    def watched_next_turn(self) -> set:
        """Where the drones will look after the next turn."""
        return watched_tiles(self.mission.drones, self.clock + 1, self.mission.grid)

    # ------------------------------------------------------------ routes
    def has_valid_route(self) -> bool:
        return (self.route is not None and self.route.found
                and len(self.route.path) >= 2 and self.route.path[0] == self.position)

    def search(self, goal) -> RouteResult:
        """Dijkstra on the state graph from where we are now (see core/state_planner.py)."""
        ctx = PlanContext(self.mission.grid, self.tile_costs, self.mission.drones,
                          self.blocked_tiles())
        return plan_state_route(ctx, self.position, goal, self.clock, self.has_key)

    def plan_route(self) -> RouteResult:
        """Plan the cheapest safe route to the current target.

        If the lasers block every route, plan to the terminal instead.
        Pro mode has no route guidance at all.
        """
        if not self.is_active or self.pro_mode:
            self.route = None
            return RouteResult([], None, False)
        result = self.search(self.current_target)
        self.route_goal = ROUTE_TO_TARGET
        if not result.found and self.lasers_on and self.position != self.mission.terminal:
            result = self.search(self.mission.terminal)
            self.route_goal = ROUTE_TO_TERMINAL
        if result.found:
            self.route = result
        else:
            self.route = None
            self.status = NO_ROUTE
            logger.warning("No route from %s to %s", self.position, self.current_target)
        return result

    def route_waits(self) -> int:
        if not self.has_valid_route():
            return 0
        return count_waits(self.route.path)

    def next_direction(self) -> str:
        """Compass direction of the next planned step, 'Wait', or '' without a route."""
        if not self.has_valid_route():
            return ""
        if self.route.path[1] == self.route.path[0]:
            return "Wait"
        return step_direction(self.route.path[0], self.route.path[1])

    def step_cost(self, old_pos, new_pos) -> int:
        if old_pos == new_pos:
            return WAIT_COST
        return self.tile_costs[self.mission.tile_at(new_pos)]

    def remaining_route_cost(self) -> int:
        if not self.has_valid_route():
            return 0
        total = 0
        for a, b in zip(self.route.path, self.route.path[1:]):
            total = total + self.step_cost(a, b)
        return total

    # ------------------------------------------------------------ movement
    def wait(self) -> StepResult:
        """Stay on the spot for one turn (the drones keep moving)."""
        return self.step(self.position)

    def step(self, target=None) -> StepResult:
        """Move one tile (or wait when target is the current tile).

        Without a target, follow the planned route. Every move in the game
        goes through here, so walls, locked doors and active lasers can never
        be entered.
        """
        if not self.is_active:
            return StepResult(False, "The mission is not active.")
        if target is None:
            if not self.has_valid_route():
                return StepResult(False, "Plan a route first.")
            target = self.route.path[1]

        old_pos = self.position
        if target != old_pos:
            if abs(target[0] - old_pos[0]) + abs(target[1] - old_pos[1]) != 1:
                return StepResult(False, "You can only move one tile up, down, left or right.")
            if not is_walkable(self.mission.grid, target, self.tile_costs):
                return StepResult(False, "A wall blocks the way.")
            tile = self.mission.tile_at(target)
            if tile == LASER and self.lasers_on:
                return StepResult(False, "Laser barrier - hack the terminal to switch it off.")
            if tile == DOOR and not self.has_key:
                return StepResult(False, "Locked door - you need the keycard.")

        # Is this move the next step of the planned route? (checked before moving)
        following = self.has_valid_route() and self.route.path[1] == target

        # The turn happens: move (or wait), pay the effort, drones advance.
        old_clock = self.clock
        self.clock = self.clock + 1
        self.effort = self.effort + self.step_cost(old_pos, target)
        self.position = target
        self.moves = self.moves + 1
        if target == old_pos:
            self.waits = self.waits + 1
        if self.status == PLANNING:
            self.status = IN_PROGRESS

        if following:
            self.route = RouteResult(self.route.path[1:], None, True)
            self.route.cost = self.remaining_route_cost()
        else:
            self.route = None          # the player left the planned route

        picked_key = False
        if self.mission.tile_at(target) == KEYCARD and not self.has_key:
            self.has_key = True
            picked_key = True
            logger.info("Keycard picked up")

        # Drone check: seen in a vision cone, or walked through a drone.
        if self.mission.drones and is_detected(self.mission.drones, self.mission.grid,
                                               old_pos, target, old_clock, self.clock):
            self.status = CAUGHT
            self.route = None
            self.spotted_by = self.drone_that_sees(old_pos, target, old_clock, self.clock)
            logger.info("Caught by %s", self.spotted_by)
            return StepResult(True, f"Spotted by the {self.spotted_by}!", caught=True,
                              picked_key=picked_key)

        if self.objective_collected and self.position == self.mission.exit:
            self.complete()
            return StepResult(True, "", completed=True, picked_key=picked_key)
        return StepResult(True, picked_key=picked_key)

    def drone_that_sees(self, old_pos, new_pos, old_clock, new_clock) -> str:
        for drone in self.mission.drones:
            if is_detected([drone], self.mission.grid, old_pos, new_pos, old_clock, new_clock):
                return drone.name
        return "patrol drone"

    # ------------------------------------------------------------ terminal
    def can_hack(self) -> bool:
        return (self.is_active and self.lasers_on
                and self.position == self.mission.terminal)

    def open_terminal(self):
        """The terminal puzzle for this run (created the first time)."""
        if self.puzzle is None:
            self.puzzle = make_puzzle(self.mission.puzzle_kind,
                                      f"{self.puzzle_seed}-{self.run_token}",
                                      self.mission.puzzle_size)
        return self.puzzle

    def submit_terminal(self, answer) -> tuple:
        """Check the player's answer. Returns (solved, message).

        A wrong answer costs TERMINAL_PENALTY effort (a lockout).
        """
        if not self.can_hack():
            return False, "There is no terminal to hack here."
        solved, message = self.open_terminal().check(answer)
        if solved:
            self.terminal_solved = True
            self.route = None          # lasers off: better routes may exist now
            logger.info("Terminal solved")
            return True, message
        self.wrong_answers = self.wrong_answers + 1
        self.effort = self.effort + config.TERMINAL_PENALTY
        return False, message + f" Lockout: +{config.TERMINAL_PENALTY} effort."

    # ------------------------------------------------------------ objective
    def can_collect(self) -> bool:
        return (self.is_active and not self.objective_collected
                and self.position == self.mission.objective)

    def collect_objective(self) -> bool:
        """Pick up the objective. Returns True if it was collected."""
        if not self.can_collect():
            return False
        self.objective_collected = True
        self.status = OBJECTIVE_SECURED
        self.route = None              # the target changed, old route is stale
        logger.info("Objective collected in %s", self.mission.mission_id)
        return True

    # ------------------------------------------------------------ ending
    def complete(self) -> None:
        self.status = COMPLETED
        self.route = None
        self.score = calculate_score(self.effort, self.mission.risk_bonus, self.pro_mode)
        logger.info("Mission %s completed, score %d", self.mission.mission_id,
                    self.score.total)

    def is_complete(self) -> bool:
        return self.status == COMPLETED

    def is_caught(self) -> bool:
        return self.status == CAUGHT

    def needs_abandon_save(self) -> bool:
        """True when leaving now should record an ABANDONED run."""
        return (self.moves > 0 and not self.result_saved
                and self.status not in (COMPLETED, CAUGHT))

    def abandon(self) -> None:
        if self.status not in (COMPLETED, CAUGHT):
            self.status = ABANDONED
            self.route = None

    def build_record(self) -> dict:
        """Plain dictionary that the database repositories know how to save."""
        if self.status == COMPLETED:
            result = RESULT_SUCCESS
            score = self.score.total
        elif self.status == CAUGHT:
            result = RESULT_CAUGHT
            score = 0
        else:
            result = RESULT_ABANDONED
            score = 0
        return {
            "player_name": self.player_name,
            "mission_id": self.mission.mission_id,
            "result": result,
            "score": score,
            "moves": self.moves,
            "route_cost": self.effort,
            "kit_summary": NO_KIT,            # legacy column (no gadgets any more)
            "alert_triggered": False,         # legacy column (no Relay alert any more)
            "pro_mode": self.pro_mode,
        }

    def save_once(self, save_function):
        """Save this run through save_function(record) exactly once.

        Returns the new run ID, or None if this run was already saved.
        result_saved is only set after the save worked, so a failed save
        can be retried, but a successful one is never repeated.
        """
        if self.result_saved:
            return None
        if self.status not in FINISHED_STATUSES:
            raise ValueError("Only completed, caught or abandoned runs are saved.")
        run_id = save_function(self.build_record())
        self.result_saved = True
        return run_id
