"""Tests for core/puzzles.py (terminal puzzles judged by Dijkstra and Knapsack DP)."""

import itertools
import unittest

from core.puzzles import (CARGO, POWER, CargoLockPuzzle, PowerRelayPuzzle,
                          make_puzzle)


def brute_force_min_load(puzzle):
    """Smallest load over every simple path IN -> OUT (DFS, small grids only)."""
    best = [float("inf")]

    def dfs(pos, seen, total):
        if total >= best[0]:
            return
        if pos == puzzle.goal:
            best[0] = total
            return
        for d_row, d_col in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            nxt = (pos[0] + d_row, pos[1] + d_col)
            if 0 <= nxt[0] < puzzle.size and 0 <= nxt[1] < puzzle.size and nxt not in seen:
                seen.add(nxt)
                dfs(nxt, seen, total + puzzle.cell(nxt))
                seen.remove(nxt)

    dfs(puzzle.start, {puzzle.start}, puzzle.cell(puzzle.start))
    return best[0]


class TestPowerRelay(unittest.TestCase):

    def test_same_seed_same_puzzle(self):
        self.assertEqual(PowerRelayPuzzle("x").grid, PowerRelayPuzzle("x").grid)

    def test_solution_is_accepted(self):
        for seed in range(20):
            puzzle = PowerRelayPuzzle(seed)
            ok, _ = puzzle.check(puzzle.solution)
            self.assertTrue(ok, seed)
            self.assertEqual(puzzle.load(puzzle.solution), puzzle.best)

    def test_greedy_path_is_not_enough(self):
        for seed in range(20):
            puzzle = PowerRelayPuzzle(seed)
            self.assertGreater(puzzle.greedy_load(), puzzle.best, seed)

    def test_dijkstra_best_equals_brute_force(self):
        for seed in range(5):
            puzzle = PowerRelayPuzzle(seed, size=4)
            self.assertEqual(puzzle.best, brute_force_min_load(puzzle), seed)

    def test_bad_paths_rejected(self):
        puzzle = PowerRelayPuzzle(1)
        self.assertFalse(puzzle.check([])[0])
        self.assertFalse(puzzle.check([(0, 0), (1, 1), (5, 5)])[0])        # not touching
        straight = [(0, c) for c in range(6)] + [(r, 5) for r in range(1, 6)]
        ok, message = puzzle.check(straight)
        self.assertEqual(ok, puzzle.load(straight) == puzzle.best)
        self.assertIn("Load", message)


class TestCargoLock(unittest.TestCase):

    def test_best_equals_brute_force(self):
        for seed in range(20):
            puzzle = CargoLockPuzzle(seed)
            best = 0
            for r in range(len(puzzle.crates) + 1):
                for combo in itertools.combinations(puzzle.crates, r):
                    if sum(c[1] for c in combo) <= puzzle.limit:
                        best = max(best, sum(c[2] for c in combo))
            self.assertEqual(puzzle.best, best, seed)

    def test_solution_accepted_and_greedy_not_enough(self):
        for seed in range(20):
            puzzle = CargoLockPuzzle(seed)
            self.assertTrue(puzzle.check(puzzle.solution)[0])
            self.assertLess(puzzle.greedy_worth(), puzzle.best, seed)

    def test_too_heavy_rejected(self):
        puzzle = CargoLockPuzzle(3)
        everything = [c[0] for c in puzzle.crates]
        ok, message = puzzle.check(everything)
        self.assertFalse(ok)
        self.assertIn("limit", message)

    def test_factory(self):
        self.assertEqual(make_puzzle(POWER, 1).kind, POWER)
        self.assertEqual(make_puzzle(CARGO, 1).kind, CARGO)
        with self.assertRaises(ValueError):
            make_puzzle("chess", 1)


if __name__ == "__main__":
    unittest.main()
