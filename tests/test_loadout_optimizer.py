"""Tests for core/loadout_optimizer.py (0/1 Knapsack, dynamic programming)."""

import itertools
import random
import unittest

from core.gadgets import GADGETS
from core.loadout_optimizer import (build_usefulness_table, mission_items,
                                    recommend_for_mission, recommend_loadout)
from core.missions import MISSIONS
from tests.reference_algorithms import knapsack_bb

CAPACITY = 8


def brute_force(items, capacity):
    """Try all 2^n subsets; apply the same tie-break rule as the game."""
    best_key, best_ids = None, ()
    for r in range(len(items) + 1):
        for combo in itertools.combinations(items, r):
            cost = sum(item[1] for item in combo)
            if cost > capacity:
                continue
            usefulness = sum(item[2] for item in combo)
            ids = tuple(sorted(item[0] for item in combo))
            # Bigger usefulness, then smaller cost, then alphabetically first.
            key = (-usefulness, cost, ids)
            if best_key is None or key < best_key:
                best_key, best_ids = key, ids
    return best_ids, -best_key[0], best_key[1]


class TestExpectedKits(unittest.TestCase):

    def test_archive(self):
        result = recommend_for_mission(MISSIONS["archive"])
        self.assertEqual(result.selected_ids, ("lens", "repair", "scanner"))
        self.assertEqual((result.total_usefulness, result.total_cost), (15, 7))

    def test_archive_tie_break_prefers_lower_energy(self):
        # scanner + boots + lens is ALSO usefulness 15, but costs 8 energy.
        archive = MISSIONS["archive"].usefulness
        other = ("boots", "lens", "scanner")
        self.assertEqual(sum(archive[g] for g in other), 15)
        self.assertEqual(sum(GADGETS[g].energy_cost for g in other), 8)
        self.assertEqual(recommend_for_mission(MISSIONS["archive"]).total_cost, 7)

    def test_gallery(self):
        result = recommend_for_mission(MISSIONS["gallery"])
        self.assertEqual(result.selected_ids, ("boots", "repair", "scanner"))
        self.assertEqual((result.total_usefulness, result.total_cost), (15, 8))

    def test_relay(self):
        result = recommend_for_mission(MISSIONS["relay"])
        self.assertEqual(result.selected_ids, ("decoy", "lens", "repair"))
        self.assertEqual((result.total_usefulness, result.total_cost), (14, 8))

    def test_alphabetical_tie_break(self):
        # Same usefulness and cost: {a, d} beats {b, c} because ('a','d') < ('b','c').
        items = [("d", 2, 5), ("c", 2, 5), ("b", 2, 5), ("a", 2, 5)]
        self.assertEqual(recommend_loadout(items, 4).selected_ids, ("a", "b"))
        items = [("a", 1, 3), ("d", 3, 4), ("b", 2, 4), ("c", 2, 3)]
        result = recommend_loadout(items, 4)
        self.assertEqual(result.selected_ids, brute_force(items, 4)[0])


class TestRules(unittest.TestCase):

    def test_never_exceeds_capacity_and_no_duplicates(self):
        for mission in MISSIONS.values():
            for capacity in range(0, 20):
                result = recommend_for_mission(mission, capacity)
                cost = sum(GADGETS[g].energy_cost for g in result.selected_ids)
                self.assertLessEqual(cost, capacity)
                self.assertEqual(cost, result.total_cost)
                self.assertEqual(len(set(result.selected_ids)), len(result.selected_ids))

    def test_capacity_zero(self):
        result = recommend_for_mission(MISSIONS["gallery"], 0)
        self.assertEqual((result.selected_ids, result.total_cost, result.total_usefulness),
                         ((), 0, 0))

    def test_empty_item_list(self):
        result = recommend_loadout([], CAPACITY)
        self.assertEqual((result.selected_ids, result.total_cost, result.total_usefulness),
                         ((), 0, 0))

    def test_item_larger_than_capacity(self):
        result = recommend_loadout([("huge", 9, 100), ("small", 2, 1)], CAPACITY)
        self.assertEqual(result.selected_ids, ("small",))
        only_huge = recommend_loadout([("huge", 9, 100)], CAPACITY)
        self.assertEqual(only_huge.selected_ids, ())

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            recommend_loadout([("a", 1, 1), ("a", 2, 2)], CAPACITY)


class TestCrossChecks(unittest.TestCase):
    """DP vs brute force vs my Experiment 6 Branch and Bound."""

    def test_missions_three_methods_agree(self):
        for mission in MISSIONS.values():
            with self.subTest(mission=mission.mission_id):
                items = mission_items(mission)
                dp = recommend_loadout(items, CAPACITY)
                ids, usefulness, cost = brute_force(items, CAPACITY)
                self.assertEqual(dp.selected_ids, ids)
                self.assertEqual(dp.total_usefulness, usefulness)
                self.assertEqual(dp.total_cost, cost)
                weights = [item[1] for item in items]
                profits = [item[2] for item in items]
                bb_profit, _ = knapsack_bb(weights, profits, CAPACITY)
                self.assertEqual(dp.total_usefulness, bb_profit)

    def test_random_instances(self):
        rng = random.Random(2026)
        for _ in range(200):
            n = rng.randint(1, 7)
            items = [(f"g{i}", rng.randint(1, 6), rng.randint(0, 9)) for i in range(n)]
            capacity = rng.randint(0, 12)
            dp = recommend_loadout(items, capacity)
            ids, usefulness, cost = brute_force(items, capacity)
            self.assertEqual((dp.selected_ids, dp.total_usefulness, dp.total_cost),
                             (ids, usefulness, cost), f"{items} cap={capacity}")
            if any(item[2] > 0 for item in items):
                bb_profit, _ = knapsack_bb([i[1] for i in items], [i[2] for i in items],
                                           capacity)
                self.assertEqual(dp.total_usefulness, bb_profit)

    def test_usefulness_table_matches(self):
        items = mission_items(MISSIONS["archive"])
        table = build_usefulness_table(items, CAPACITY)
        self.assertEqual(table[len(items)][CAPACITY], 15)


if __name__ == "__main__":
    unittest.main()
