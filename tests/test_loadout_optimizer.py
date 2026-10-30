"""Tests for core/loadout_optimizer.py (0/1 Knapsack, dynamic programming).

The game uses this DP to judge the Cargo Lock puzzle. Items are
(id, weight, value) triples: crate name, mass in kg, worth in credits.
"""

import itertools
import random
import unittest

from core.loadout_optimizer import build_value_table, recommend_loadout
from core.puzzles import CargoLockPuzzle
from tests.reference_algorithms import knapsack_bb

# A small fixed example (used in the README): limit 8.
EXAMPLE = [("A", 3, 6), ("B", 4, 3), ("C", 3, 2), ("D", 2, 2), ("E", 2, 7), ("F", 5, 3)]


def brute_force(items, capacity):
    """Try all 2^n subsets; apply the same tie-break rule as the DP."""
    best_key, best_ids = None, ()
    for r in range(len(items) + 1):
        for combo in itertools.combinations(items, r):
            weight = sum(item[1] for item in combo)
            if weight > capacity:
                continue
            value = sum(item[2] for item in combo)
            ids = tuple(sorted(item[0] for item in combo))
            # Bigger value, then smaller weight, then alphabetically first.
            key = (-value, weight, ids)
            if best_key is None or key < best_key:
                best_key, best_ids = key, ids
    return best_ids, -best_key[0], best_key[1]


class TestExample(unittest.TestCase):

    def test_example_best_and_tie_break(self):
        # A + D + E and A + C + E both give 15; A + D + E is lighter (7 < 8).
        result = recommend_loadout(EXAMPLE, 8)
        self.assertEqual(result.selected_ids, ("A", "D", "E"))
        self.assertEqual((result.total_usefulness, result.total_cost), (15, 7))

    def test_alphabetical_tie_break(self):
        # Same value and weight: {a, b} beats {c, d}.
        items = [("d", 2, 5), ("c", 2, 5), ("b", 2, 5), ("a", 2, 5)]
        self.assertEqual(recommend_loadout(items, 4).selected_ids, ("a", "b"))

    def test_value_table(self):
        table = build_value_table(EXAMPLE, 8)
        self.assertEqual(table[len(EXAMPLE)][8], 15)
        self.assertEqual(table[len(EXAMPLE)][7], 15)
        self.assertEqual(table[0], [0] * 9)


class TestRules(unittest.TestCase):

    def test_never_exceeds_capacity_and_no_duplicates(self):
        for capacity in range(0, 20):
            result = recommend_loadout(EXAMPLE, capacity)
            weight = sum(w for i, w, _ in EXAMPLE if i in result.selected_ids)
            self.assertLessEqual(weight, capacity)
            self.assertEqual(weight, result.total_cost)
            self.assertEqual(len(set(result.selected_ids)), len(result.selected_ids))

    def test_capacity_zero_and_empty_list(self):
        for items, capacity in ((EXAMPLE, 0), ([], 8)):
            result = recommend_loadout(items, capacity)
            self.assertEqual((result.selected_ids, result.total_cost, result.total_usefulness),
                             ((), 0, 0))

    def test_item_larger_than_capacity(self):
        result = recommend_loadout([("huge", 9, 100), ("small", 2, 1)], 8)
        self.assertEqual(result.selected_ids, ("small",))
        self.assertEqual(recommend_loadout([("huge", 9, 100)], 8).selected_ids, ())

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            recommend_loadout([("a", 1, 1), ("a", 2, 2)], 8)


class TestCrossChecks(unittest.TestCase):
    """DP vs brute force vs my Experiment 6 Branch and Bound."""

    def test_random_instances(self):
        rng = random.Random(2026)
        for _ in range(200):
            n = rng.randint(1, 7)
            items = [(f"g{i}", rng.randint(1, 6), rng.randint(0, 9)) for i in range(n)]
            capacity = rng.randint(0, 12)
            dp = recommend_loadout(items, capacity)
            ids, value, weight = brute_force(items, capacity)
            self.assertEqual((dp.selected_ids, dp.total_usefulness, dp.total_cost),
                             (ids, value, weight), f"{items} cap={capacity}")
            if any(item[2] > 0 for item in items):
                bb_value, _ = knapsack_bb([i[1] for i in items], [i[2] for i in items],
                                          capacity)
                self.assertEqual(dp.total_usefulness, bb_value)

    def test_cargo_puzzles_three_methods_agree(self):
        for seed in range(30):
            puzzle = CargoLockPuzzle(seed)
            dp = recommend_loadout(puzzle.crates, puzzle.limit)
            bb_value, _ = knapsack_bb([c[1] for c in puzzle.crates],
                                      [c[2] for c in puzzle.crates], puzzle.limit)
            self.assertEqual(dp.total_usefulness, bb_value)
            self.assertEqual(dp.total_usefulness, brute_force(puzzle.crates, puzzle.limit)[1])
            self.assertEqual(puzzle.best, dp.total_usefulness)


if __name__ == "__main__":
    unittest.main()
