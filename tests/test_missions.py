"""Tests for core/missions.py and core/gadgets.py."""

import unittest

from core.gadgets import GADGETS, GADGET_ORDER, kit_energy, kit_summary
from core.missions import MISSIONS, MISSION_ORDER, build_tile_costs
from tests.reference_algorithms import count_walkable_groups


class TestMissionMaps(unittest.TestCase):

    def test_three_missions(self):
        self.assertEqual(set(MISSIONS), set(MISSION_ORDER))
        self.assertEqual(len(MISSIONS), 3)

    def test_maps_are_rectangular_and_small(self):
        for m in MISSIONS.values():
            with self.subTest(mission=m.mission_id):
                widths = {len(line) for line in m.grid}
                self.assertEqual(widths, {12})
                self.assertLessEqual(len(m.grid), 11)

    def test_exactly_one_start_objective_exit(self):
        for m in MISSIONS.values():
            text = "".join(m.grid)
            with self.subTest(mission=m.mission_id):
                self.assertEqual(text.count("S"), 1)
                self.assertEqual(text.count("O"), 1)
                self.assertEqual(text.count("E"), 1)

    def test_gate_only_in_relay(self):
        self.assertEqual("".join(MISSIONS["relay"].grid).count("G"), 1)
        self.assertTrue(MISSIONS["relay"].has_alert)
        self.assertEqual("".join(MISSIONS["archive"].grid).count("G"), 0)
        self.assertEqual("".join(MISSIONS["gallery"].grid).count("G"), 0)

    def test_only_known_tile_characters(self):
        for m in MISSIONS.values():
            self.assertTrue(set("".join(m.grid)) <= set("#.~SOEG"))

    def test_border_is_wall(self):
        for m in MISSIONS.values():
            self.assertEqual(set(m.grid[0]), {"#"})
            self.assertEqual(set(m.grid[-1]), {"#"})
            for line in m.grid:
                self.assertEqual((line[0], line[-1]), ("#", "#"))

    def test_positions(self):
        self.assertEqual((MISSIONS["archive"].start, MISSIONS["archive"].objective,
                          MISSIONS["archive"].exit), ((1, 1), (5, 7), (7, 1)))
        self.assertEqual(MISSIONS["gallery"].objective, (1, 10))
        self.assertEqual(MISSIONS["relay"].objective, (3, 8))

    def test_all_walkable_tiles_connected_union_find(self):
        # My Experiment 3 find()/union(): one single group means no
        # unreachable room exists in any mission.
        walkable = set(build_tile_costs())
        for m in MISSIONS.values():
            with self.subTest(mission=m.mission_id):
                self.assertEqual(count_walkable_groups(m.grid, walkable), 1)

    def test_usefulness_defined_for_every_gadget(self):
        for m in MISSIONS.values():
            self.assertEqual(set(m.usefulness), set(GADGETS))


class TestGadgets(unittest.TestCase):

    def test_catalogue(self):
        self.assertEqual(len(GADGETS), 6)
        self.assertEqual(set(GADGET_ORDER), set(GADGETS))
        costs = {g: GADGETS[g].energy_cost for g in GADGETS}
        self.assertEqual(costs, {"scanner": 3, "decoy": 4, "boots": 3,
                                 "repair": 2, "lens": 2, "shield": 5})

    def test_kit_helpers(self):
        self.assertEqual(kit_energy(["boots", "repair"]), 5)
        self.assertEqual(kit_energy([]), 0)
        self.assertEqual(kit_summary([]), "None")
        self.assertEqual(kit_summary(["repair", "boots"]), "Mobility Boots, Repair Module")

    def test_boots_change_static_cost(self):
        self.assertEqual(build_tile_costs()["~"], 4)
        self.assertEqual(build_tile_costs(["boots"])["~"], 2)
        self.assertNotIn("#", build_tile_costs())


if __name__ == "__main__":
    unittest.main()
