"""Game state for one attempt at a mission (the MissionRun state machine).

The engine has no Tkinter imports, so every rule can be unit-tested without
opening a window. The UI only calls these methods and redraws.

Status flow
    PLANNING -> IN_PROGRESS -> OBJECTIVE_SECURED -> COMPLETED
    any active status -> ABANDONED (player leaves after moving)
    any active status -> NO_ROUTE  (no safe route left; restart or leave)
"""

import logging

from core.gadgets import GADGETS, DECOY, SCANNER, kit_energy, kit_summary
from core.missions import build_tile_costs
from core.pathfinding import (RouteResult, find_shortest_path, is_walkable,
                              step_direction)
from core import config
from core.scoring import calculate_score

logger = logging.getLogger(__name__)

PLANNING = "PLANNING"
IN_PROGRESS = "IN_PROGRESS"
OBJECTIVE_SECURED = "OBJECTIVE_SECURED"
COMPLETED = "COMPLETED"
ABANDONED = "ABANDONED"
NO_ROUTE = "NO_ROUTE"

ACTIVE_STATUSES = (PLANNING, IN_PROGRESS, OBJECTIVE_SECURED)

RESULT_SUCCESS = "SUCCESS"
RESULT_ABANDONED = "ABANDONED"


class StepResult:
    """What happened when the player tried to move one tile."""

    def __init__(self, ok: bool, reason: str = "", completed: bool = False):
        self.ok = ok
        self.reason = reason          # friendly text when the move was refused
        self.completed = completed    # True when this step finished the mission

    def __bool__(self):
        return self.ok

    def __repr__(self):
        return f"StepResult(ok={self.ok}, reason={self.reason!r}, completed={self.completed})"


def validate_kit(kit_ids) -> tuple:
    """Return the kit as a sorted tuple, or raise ValueError if it is illegal."""
    kit = tuple(sorted(kit_ids))
    if len(set(kit)) != len(kit):
        raise ValueError("A gadget can only be carried once.")
    for gadget_id in kit:
        if gadget_id not in GADGETS:
            raise ValueError(f"Unknown gadget: {gadget_id}")
    if kit_energy(kit) > config.KIT_CAPACITY:
        raise ValueError("The kit uses more energy than the capacity allows.")
    return kit


class MissionRun:
    """All state of one run of one mission, plus the rules that change it."""

    def __init__(self, player_name: str, mission, kit_ids=(), best_usefulness: int = 0):
        self.player_name = player_name
        self.mission = mission                     # read-only map and story
        self.kit_ids = validate_kit(kit_ids)
        self.tile_costs = build_tile_costs(self.kit_ids)   # boots-aware costs
        self.chosen_usefulness = sum(mission.usefulness[g] for g in self.kit_ids)
        self.best_usefulness = best_usefulness
        self.run_token = 0                         # increases on every restart
        self.reset_state()

    # ------------------------------------------------------------ state
    def reset_state(self) -> None:
        """Put every changeable value back to the start of a run."""
        self.position = self.mission.start
        self.objective_collected = False
        self.status = PLANNING
        self.sealed_tiles = set()
        self.alert_triggered = False
        self.moves = 0
        self.effort = 0
        self.route = None                          # RouteResult or None
        self.score = None                          # ScoreBreakdown when completed
        self.result_saved = False

    def restart(self) -> None:
        """Start the same mission again with the same kit (gate re-opened)."""
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
    def carries_decoy(self) -> bool:
        return DECOY in self.kit_ids

    @property
    def weak_point_visible(self) -> bool:
        """Pocket Scanner reveals the gate that the alert will seal."""
        return SCANNER in self.kit_ids and self.mission.has_alert

    @property
    def kit_text(self) -> str:
        return kit_summary(self.kit_ids)

    def blocked_tiles(self) -> set:
        """Tiles that cannot be entered right now.

        The tile the character stands on is never treated as blocked, so the
        character can still walk away if it happened to be on the gate.
        """
        return set(self.sealed_tiles) - {self.position}

    # ------------------------------------------------------------ routes
    def has_valid_route(self) -> bool:
        return (self.route is not None and self.route.found
                and len(self.route.path) >= 2 and self.route.path[0] == self.position)

    def plan_route(self) -> RouteResult:
        """Run Dijkstra from the current position to the current target."""
        if not self.is_active:
            self.route = None
            return RouteResult([], None, False)
        result = find_shortest_path(self.mission.grid, self.position, self.current_target,
                                    self.tile_costs, self.blocked_tiles())
        if result.found:
            self.route = result
        else:
            self.route = None
            self.status = NO_ROUTE
            logger.warning("No route from %s to %s", self.position, self.current_target)
        return result

    def next_direction(self) -> str:
        """Compass direction of the next planned step, or '' without a route."""
        if not self.has_valid_route():
            return ""
        return step_direction(self.route.path[0], self.route.path[1])

    def remaining_route_cost(self) -> int:
        if not self.has_valid_route():
            return 0
        total = 0
        for pos in self.route.path[1:]:
            total = total + self.tile_costs[self.mission.tile_at(pos)]
        return total

    # ------------------------------------------------------------ movement
    def step(self, target=None) -> StepResult:
        """Move one tile. Without a target, follow the planned route.

        Returns StepResult(ok, reason, completed). Every move in the game goes
        through here, so walls and sealed gates can never be entered.
        """
        if not self.is_active:
            return StepResult(False, "The mission is not active.")
        if target is None:
            if not self.has_valid_route():
                return StepResult(False, "Plan a route first.")
            target = self.route.path[1]

        row, col = self.position
        if abs(target[0] - row) + abs(target[1] - col) != 1:
            return StepResult(False, "You can only move one tile up, down, left or right.")
        if target in self.sealed_tiles:
            return StepResult(False, "That gate is sealed.")
        if not is_walkable(self.mission.grid, target, self.tile_costs):
            return StepResult(False, "A wall blocks the way.")

        # The move is legal: update position, counters and the route.
        self.position = target
        self.moves = self.moves + 1
        self.effort = self.effort + self.tile_costs[self.mission.tile_at(target)]
        if self.status == PLANNING:
            self.status = IN_PROGRESS
        if self.route is not None and len(self.route.path) >= 2 and self.route.path[1] == target:
            self.route = RouteResult(self.route.path[1:], self.remaining_cost_after_move(),
                                     True)
        else:
            self.route = None          # the player left the planned route

        if self.objective_collected and self.position == self.mission.exit:
            self.complete()
            return StepResult(True, "", completed=True)
        return StepResult(True)

    def remaining_cost_after_move(self) -> int:
        total = 0
        for pos in self.route.path[2:]:
            total = total + self.tile_costs[self.mission.tile_at(pos)]
        return total

    # ------------------------------------------------------------ objective
    def can_collect(self) -> bool:
        return (self.is_active and not self.objective_collected
                and self.position == self.mission.objective)

    def collect_objective(self) -> bool:
        """Pick up the objective. Returns True if the alert fired because of it."""
        if not self.can_collect():
            return False
        self.objective_collected = True
        self.status = OBJECTIVE_SECURED
        self.route = None              # the target changed, old route is stale
        logger.info("Objective collected in %s", self.mission.mission_id)
        if self.mission.has_alert and not self.alert_triggered:
            self.trigger_alert()
            return True
        return False

    def can_trigger_alert(self) -> bool:
        return self.mission.has_alert and not self.alert_triggered and self.is_active

    def trigger_alert(self) -> bool:
        """Seal the relay gate (at most once per run) and re-plan at once."""
        if not self.can_trigger_alert():
            return False
        self.alert_triggered = True
        self.sealed_tiles.add(self.mission.gate)
        self.route = None              # never keep following a stale path
        logger.info("Alert: gate %s sealed", self.mission.gate)
        self.plan_route()
        return True

    # ------------------------------------------------------------ ending
    def complete(self) -> None:
        self.status = COMPLETED
        self.route = None
        self.score = calculate_score(self.chosen_usefulness, self.best_usefulness,
                                     self.effort, self.alert_triggered, self.carries_decoy)
        logger.info("Mission %s completed, score %d", self.mission.mission_id,
                    self.score.total)

    def is_complete(self) -> bool:
        return self.status == COMPLETED

    def needs_abandon_save(self) -> bool:
        """True when leaving now should record an ABANDONED run."""
        return self.moves > 0 and not self.result_saved and self.status != COMPLETED

    def abandon(self) -> None:
        if self.status != COMPLETED:
            self.status = ABANDONED
            self.route = None

    def build_record(self) -> dict:
        """Plain dictionary that the database repositories know how to save."""
        if self.status == COMPLETED:
            result = RESULT_SUCCESS
            score = self.score.total
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
            "kit_summary": self.kit_text,
            "alert_triggered": self.alert_triggered,
        }

    def save_once(self, save_function):
        """Save this run through save_function(record) exactly once.

        Returns the new run ID, or None if this run was already saved.
        result_saved is only set after the save worked, so a failed save
        can be retried, but a successful one is never repeated.
        """
        if self.result_saved:
            return None
        if self.status not in (COMPLETED, ABANDONED):
            raise ValueError("Only completed or abandoned runs are saved.")
        run_id = save_function(self.build_record())
        self.result_saved = True
        return run_id
