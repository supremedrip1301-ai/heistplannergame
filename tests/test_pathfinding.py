"""Tests for core/pathfinding.py (heap-based Dijkstra)."""

import unittest

from core.missions import MISSIONS, build_tile_costs
from core.pathfinding import find_shortest_path, path_cost, is_walkable
from tests.reference_algorithms import dijkstra_matrix, grid_to_matrix

COSTS = build_tile_costs()
BOOT_COSTS = build_tile_costs(["boots"])


class PathCheckMixin:
    """Helper that checks a path really is a legal walk on the map."""

    def assert_valid_path(self, grid, path, costs, blocked=frozenset()):
        self.assertTrue(len(path) >= 1)
        for pos in path:
            self.assertTrue(is_walkable(grid, pos, costs, blocked), f"{pos} not walkable")
        for a, b in zip(path, path[1:]):
            distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
            self.assertEqual(distance, 1, f"{a} -> {b} is not a four-direction step")


class TestSmallGrids(unittest.TestCase, PathCheckMixin):

    def test_cheaper_longer_route_is_chosen(self):
        # Straight across: 2 steps through a static field = 4 + 1 = 5.
        # Around the bottom: 4 steps of floor = 4. Dijkstra must pick 4.
        grid = ["#####",
                "#.~.#",
                "#...#",
                "#####"]
        result = find_shortest_path(grid, (1, 1), (1, 3), COSTS)
        self.assertTrue(result.found)
        self.assertEqual(result.cost, 4)
        self.assertEqual(result.steps, 4)
        self.assertNotIn((1, 2), result.path)
        self.assert_valid_path(grid, result.path, COSTS)

    def test_start_equals_goal(self):
        grid = ["...", "..."]
        result = find_shortest_path(grid, (0, 0), (0, 0), COSTS)
        self.assertEqual((result.path, result.cost, result.found), ([(0, 0)], 0, True))

    def test_unreachable_goal(self):
        grid = [".#.",
                ".#.",
                ".#."]
        result = find_shortest_path(grid, (0, 0), (0, 2), COSTS)
        self.assertEqual((result.path, result.cost, result.found), ([], None, False))

    def test_invalid_coordinates_give_not_found(self):
        grid = ["...", "..."]
        for bad in [(-1, 0), (5, 5), (0, 3)]:
            result = find_shortest_path(grid, (0, 0), bad, COSTS)
            self.assertFalse(result.found)
            result = find_shortest_path(grid, bad, (0, 0), COSTS)
            self.assertFalse(result.found)

    def test_wall_as_goal_gives_not_found(self):
        grid = ["..#"]
        self.assertFalse(find_shortest_path(grid, (0, 0), (0, 2), COSTS).found)

    def test_sealed_tile_forces_more_expensive_route(self):
        grid = ["#####",
                "#...#",
                "#.#.#",
                "#...#",
                "#####"]
        open_route = find_shortest_path(grid, (1, 1), (1, 3), COSTS)
        self.assertEqual(open_route.cost, 2)
        sealed = find_shortest_path(grid, (1, 1), (1, 3), COSTS, blocked={(1, 2)})
        self.assertEqual(sealed.cost, 6)
        self.assertNotIn((1, 2), sealed.path)
        self.assert_valid_path(grid, sealed.path, COSTS, {(1, 2)})

    def test_same_map_gives_same_path(self):
        grid = MISSIONS["gallery"].grid
        m = MISSIONS["gallery"]
        first = find_shortest_path(grid, m.objective, m.exit, COSTS)
        second = find_shortest_path(grid, m.objective, m.exit, COSTS)
        self.assertEqual(first.path, second.path)


class TestMissionNumbers(unittest.TestCase, PathCheckMixin):
    """The exact Section 8 numbers of MASTER_PROMPT.md."""

    def route(self, mission_id, a, b, costs=COSTS, blocked=frozenset()):
        m = MISSIONS[mission_id]
        result = find_shortest_path(m.grid, a, b, costs, blocked)
        self.assertTrue(result.found)
        self.assert_valid_path(m.grid, result.path, costs, blocked)
        self.assertEqual(path_cost(m.grid, result.path, costs), result.cost)
        self.assertEqual(result.path[0], a)
        self.assertEqual(result.path[-1], b)
        return result

    def test_archive(self):
        m = MISSIONS["archive"]
        to_obj = self.route("archive", m.start, m.objective)
        self.assertEqual((to_obj.cost, to_obj.steps), (14, 14))
        to_exit = self.route("archive", m.objective, m.exit)
        self.assertEqual((to_exit.cost, to_exit.steps), (8, 8))

    def test_gallery_without_boots_takes_long_loop(self):
        m = MISSIONS["gallery"]
        result = self.route("gallery", m.start, m.objective)
        self.assertEqual((result.cost, result.steps), (17, 17))
        self.assertIn((5, 5), result.path)          # goes along row 5

    def test_gallery_direct_route_costs_21(self):
        m = MISSIONS["gallery"]
        direct = [(1, c) for c in range(1, 11)]
        self.assertEqual(len(direct) - 1, 9)
        self.assertEqual(path_cost(m.grid, direct, COSTS), 21)
        self.assertEqual(path_cost(m.grid, direct, BOOT_COSTS), 13)

    def test_gallery_with_boots_takes_direct_route(self):
        m = MISSIONS["gallery"]
        result = self.route("gallery", m.start, m.objective, BOOT_COSTS)
        self.assertEqual((result.cost, result.steps), (13, 9))

    def test_gallery_objective_to_exit(self):
        m = MISSIONS["gallery"]
        self.assertEqual(self.route("gallery", m.objective, m.exit).cost, 15)

    def test_relay(self):
        m = MISSIONS["relay"]
        self.assertEqual(m.gate, (5, 5))
        self.assertEqual(self.route("relay", m.start, m.objective).cost, 13)
        home = self.route("relay", m.objective, m.exit)
        self.assertEqual(home.cost, 11)
        self.assertIn(m.gate, home.path)

    def test_relay_after_gate_sealed(self):
        m = MISSIONS["relay"]
        result = self.route("relay", m.objective, m.exit, blocked={m.gate})
        self.assertEqual((result.cost, result.steps), (19, 19))
        self.assertNotIn(m.gate, result.path)


class TestAgainstWorksheetMatrixVersion(unittest.TestCase):
    """Heap Dijkstra must agree with my (fixed) O(V^2) Experiment 4 version."""

    def compare(self, grid, costs, blocked=frozenset()):
        matrix, index_of = grid_to_matrix(grid, costs, blocked)
        for source in index_of:
            matrix_dist = dijkstra_matrix(matrix, index_of[source])
            for target, idx in index_of.items():
                heap_result = find_shortest_path(grid, source, target, costs, blocked)
                self.assertTrue(heap_result.found)
                self.assertEqual(heap_result.cost, matrix_dist[idx],
                                 f"{source}->{target}")

    def test_worksheet_example_graph(self):
        graph = [[0, 10, 5, 0, 0],
                 [10, 0, 2, 1, 0],
                 [5, 2, 0, 9, 2],
                 [0, 1, 9, 0, 4],
                 [0, 0, 2, 4, 0]]
        self.assertEqual(dijkstra_matrix(graph, 0), [0, 7, 5, 8, 7])

    def test_all_missions_all_pairs(self):
        for mission in MISSIONS.values():
            with self.subTest(mission=mission.mission_id):
                self.compare(mission.grid, COSTS)
                self.compare(mission.grid, BOOT_COSTS)

    def test_relay_with_sealed_gate(self):
        m = MISSIONS["relay"]
        self.compare(m.grid, COSTS, {m.gate})


if __name__ == "__main__":
    unittest.main()
