"""Tests for core/missions.py: the three drone missions are valid and fair."""

import unittest

from core.drones import is_detected, watched_tiles
from core.missions import MISSIONS, MISSION_ORDER, build_tile_costs
from core.state_planner import PlanContext, plan_state_route
from tests.reference_algorithms import count_walkable_groups


class TestMissionMaps(unittest.TestCase):

    def test_three_missions(self):
        self.assertEqual(set(MISSIONS), set(MISSION_ORDER))
        self.assertEqual(MISSION_ORDER, ("vault", "lab", "penthouse"))

    def test_maps_are_rectangular_and_small(self):
        for m in MISSIONS.values():
            with self.subTest(mission=m.mission_id):
                self.assertEqual({len(line) for line in m.grid}, {12})
                self.assertLessEqual(len(m.grid), 11)

    def test_exactly_one_start_objective_exit(self):
        for m in MISSIONS.values():
            text = "".join(m.grid)
            with self.subTest(mission=m.mission_id):
                self.assertEqual(text.count("S"), 1)
                self.assertEqual(text.count("O"), 1)
                self.assertEqual(text.count("E"), 1)

    def test_only_known_tile_characters(self):
        for m in MISSIONS.values():
            self.assertTrue(set("".join(m.grid)) <= set("#.~SOEkDTL"))

    def test_border_is_wall(self):
        for m in MISSIONS.values():
            self.assertEqual(set(m.grid[0]), {"#"})
            self.assertEqual(set(m.grid[-1]), {"#"})
            for line in m.grid:
                self.assertEqual((line[0], line[-1]), ("#", "#"))

    def test_all_walkable_tiles_connected_union_find(self):
        # My Experiment 3 find()/union(): one single group means no
        # unreachable room exists in any mission (doors/lasers counted as open).
        walkable = set(build_tile_costs())
        for m in MISSIONS.values():
            with self.subTest(mission=m.mission_id):
                self.assertEqual(count_walkable_groups(m.grid, walkable), 1)

    def test_keycard_door_terminal_lasers(self):
        self.assertFalse(MISSIONS["vault"].has_keycard)
        for mission_id, size in (("lab", 6), ("penthouse", 7)):
            m = MISSIONS[mission_id]
            self.assertTrue(m.has_keycard and m.has_terminal)
            self.assertGreaterEqual(len(m.door_tiles()), 1)
            self.assertGreaterEqual(len(m.laser_tiles()), 1)
            self.assertEqual((m.puzzle_kind, m.puzzle_size), ("power", size))

    def test_static_field_cost(self):
        self.assertEqual(build_tile_costs()["~"], 4)
        self.assertNotIn("#", build_tile_costs())


class TestMissionsAreFair(unittest.TestCase):
    """Solvable, safe start, and timing really matters."""

    def legs(self, mission):
        """(start, goal, blocked) for each part of the mission, lasers on until hacked."""
        lasers = set(mission.laser_tiles())
        if mission.has_terminal:
            return [(mission.start, mission.terminal, lasers),
                    (mission.terminal, mission.objective, set()),
                    (mission.objective, mission.exit, set())]
        return [(mission.start, mission.objective, lasers),
                (mission.objective, mission.exit, set())]

    def test_drones_patrol_walkable_tiles(self):
        for m in MISSIONS.values():
            for drone in m.drones:
                for row, col in drone.cycle:
                    self.assertIn(m.grid[row][col], ".~", f"{drone.name} at {(row, col)}")

    def test_start_is_safe(self):
        for m in MISSIONS.values():
            self.assertNotIn(m.start, watched_tiles(m.drones, 0, m.grid))

    def test_every_leg_solvable_and_needs_timing(self):
        costs = build_tile_costs()
        for m in MISSIONS.values():
            clock, has_key = 0, False
            for start, goal, blocked in self.legs(m):
                with self.subTest(mission=m.mission_id, goal=goal):
                    ctx = PlanContext(m.grid, costs, m.drones, blocked)
                    route = plan_state_route(ctx, start, goal, clock, has_key)
                    self.assertTrue(route.found)
                    # The same leg ignoring the drones would be spotted somewhere.
                    plain = plan_state_route(PlanContext(m.grid, costs, [], blocked),
                                             start, goal, 0, has_key)
                    spotted, c = False, clock
                    for a, b in zip(plain.path, plain.path[1:]):
                        spotted = spotted or is_detected(m.drones, m.grid, a, b, c,
                                                         (c + 1) % ctx.period)
                        c = (c + 1) % ctx.period
                    self.assertTrue(spotted)
                    clock = (clock + route.steps) % ctx.period
                    has_key = has_key or m.keycard in route.path

    def test_keycard_and_terminal_are_needed(self):
        costs = build_tile_costs()
        for mission_id in ("lab", "penthouse"):
            m = MISSIONS[mission_id]
            lasers = set(m.laser_tiles())
            # Without the lasers off the objective is unreachable even with the keycard.
            ctx = PlanContext(m.grid, costs, [], lasers)
            self.assertFalse(plan_state_route(ctx, m.start, m.objective, 0, True).found)
            # The terminal cannot be reached without passing a locked door.
            no_key_ctx = PlanContext(m.grid, costs, [], lasers | {m.keycard})
            self.assertFalse(plan_state_route(no_key_ctx, m.start, m.terminal).found)

    def test_home_route_exists_at_every_clock(self):
        costs = build_tile_costs()
        for m in MISSIONS.values():
            ctx = PlanContext(m.grid, costs, m.drones)
            for clock in range(ctx.period):
                if m.objective in watched_tiles(m.drones, clock, m.grid):
                    continue
                self.assertTrue(plan_state_route(ctx, m.objective, m.exit, clock, True).found)


if __name__ == "__main__":
    unittest.main()
