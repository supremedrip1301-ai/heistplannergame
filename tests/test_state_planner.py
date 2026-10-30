"""Tests for core/state_planner.py (Dijkstra on the state graph)."""

import unittest

from core.drones import Drone, is_detected
from core.missions import MISSIONS, build_tile_costs
from core.pathfinding import find_shortest_path
from core.state_planner import (PlanContext, count_waits, plan_state_route,
                                successors)
from tests.classic_maps import CLASSIC, FLOOR_COSTS
from tests.reference_algorithms import bellman_ford

COSTS = build_tile_costs()


def simulate(ctx, path, clock=0):
    """Walk a planned path turn by turn; return (cost, ever_seen)."""
    cost, seen = 0, False
    has_key = False
    for a, b in zip(path, path[1:]):
        new_clock = (clock + 1) % ctx.period
        if a == b:
            cost += 1
        else:
            assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1, "not a 4-direction step"
            assert ctx.can_enter(b, has_key), f"{b} cannot be entered"
            cost += ctx.tile_costs[ctx.grid[b[0]][b[1]]]
        has_key = has_key or ctx.grid[b[0]][b[1]] == "k"
        if ctx.drones and is_detected(ctx.drones, ctx.grid, a, b, clock, new_clock):
            seen = True
        clock = new_clock
    return cost, seen


def bellman_ford_cost(ctx, start, goal, clock=0, has_key=False):
    start_state = (start[0], start[1], clock, has_key)
    dist = bellman_ford(start_state, lambda s: successors(ctx, s))
    costs = [d for s, d in dist.items() if (s[0], s[1]) == goal]
    return min(costs) if costs else None


class TestMatchesTileDijkstra(unittest.TestCase):
    """With no drones and no keycards the state graph is just the tile graph."""

    def test_classic_grids_same_costs(self):
        for grid in CLASSIC.values():
            ctx = PlanContext(grid.grid, FLOOR_COSTS)
            for target in (grid.objective, grid.exit):
                with self.subTest(grid=grid.mission_id, target=target):
                    a = find_shortest_path(grid.grid, grid.start, target, FLOOR_COSTS)
                    b = plan_state_route(ctx, grid.start, target)
                    self.assertEqual(a.cost, b.cost)
                    self.assertEqual(count_waits(b.path), 0)

    def test_blocked_gate_same_cost(self):
        relay = CLASSIC["relay"]
        ctx = PlanContext(relay.grid, FLOOR_COSTS, blocked={relay.gate})
        self.assertEqual(plan_state_route(ctx, relay.objective, relay.exit).cost, 19)


class TestDrones(unittest.TestCase):

    GRID = ["#########",
            "#S......#",
            "###.#####",
            "#E......#",
            "#########"]

    def test_waits_for_the_drone_to_pass(self):
        # A drone sweeps the bottom corridor; the player must time the crossing.
        drone = Drone("a", [(3, 1), (3, 7)])
        ctx = PlanContext(self.GRID, COSTS, [drone])
        route = plan_state_route(ctx, (1, 1), (3, 1))
        self.assertTrue(route.found)
        cost, seen = simulate(ctx, route.path)
        self.assertFalse(seen)
        self.assertEqual(cost, route.cost)
        self.assertEqual(route.cost, bellman_ford_cost(ctx, (1, 1), (3, 1)))

    def test_start_clock_changes_the_plan(self):
        drone = Drone("a", [(3, 1), (3, 7)])
        ctx = PlanContext(self.GRID, COSTS, [drone])
        for clock in range(drone.period):
            route = plan_state_route(ctx, (1, 1), (3, 1), clock=clock)
            self.assertTrue(route.found)
            self.assertEqual(route.cost, bellman_ford_cost(ctx, (1, 1), (3, 1), clock))
            self.assertFalse(simulate(ctx, route.path, clock)[1])

    def test_unbeatable_guard_means_no_route(self):
        grid = ["#####",
                "#S.E#",
                "#####"]
        guard = Drone("g", [(1, 2), (1, 3)], sight=3)      # sits on the only corridor
        ctx = PlanContext(grid, COSTS, [guard])
        self.assertFalse(plan_state_route(ctx, (1, 1), (1, 3)).found)


class TestKeycards(unittest.TestCase):

    GRID = ["#######",
            "#S.D.E#",
            "#.#####",
            "#..k..#",
            "#######"]

    def test_fetches_the_keycard_first(self):
        ctx = PlanContext(self.GRID, COSTS)
        route = plan_state_route(ctx, (1, 1), (1, 5))
        self.assertTrue(route.found)
        self.assertIn((3, 3), route.path)                  # went to the keycard
        door_index = route.path.index((1, 3))
        self.assertLess(route.path.index((3, 3)), door_index)
        self.assertEqual(route.cost, bellman_ford_cost(ctx, (1, 1), (1, 5)))
        self.assertEqual(simulate(ctx, route.path)[0], route.cost)

    def test_with_keycard_goes_straight(self):
        ctx = PlanContext(self.GRID, COSTS)
        route = plan_state_route(ctx, (1, 1), (1, 5), has_key=True)
        self.assertEqual(route.cost, 4)
        self.assertNotIn((3, 3), route.path)

    def test_count_waits(self):
        self.assertEqual(count_waits([(1, 1), (1, 1), (1, 2), (1, 2), (1, 2)]), 3)


class TestNewMissionsAgainstBellmanFord(unittest.TestCase):

    def test_every_new_mission(self):
        for mission in MISSIONS.values():
            with self.subTest(mission=mission.mission_id):
                blocked = set(mission.laser_tiles())               # lasers still on
                ctx = PlanContext(mission.grid, COSTS, mission.drones, blocked)
                first = mission.terminal if mission.has_terminal else mission.objective
                route = plan_state_route(ctx, mission.start, first)
                self.assertTrue(route.found)
                self.assertEqual(route.cost, bellman_ford_cost(ctx, mission.start, first))
                cost, seen = simulate(ctx, route.path)
                self.assertFalse(seen)
                self.assertEqual(cost, route.cost)


if __name__ == "__main__":
    unittest.main()
