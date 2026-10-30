"""Tests for core/drones.py (patrol routes, vision, detection)."""

import unittest

from core.drones import (Drone, drone_clock_period, is_detected, straight_line,
                         watched_tiles)

GRID = ["#######",
        "#.....#",
        "#.#D..#",
        "#.....#",
        "#######"]


class TestPatrols(unittest.TestCase):

    def test_straight_line(self):
        self.assertEqual(straight_line((1, 1), (1, 4)), [(1, 1), (1, 2), (1, 3), (1, 4)])
        self.assertEqual(straight_line((3, 2), (1, 2)), [(3, 2), (2, 2), (1, 2)])
        with self.assertRaises(ValueError):
            straight_line((1, 1), (2, 2))

    def test_pingpong_cycle(self):
        drone = Drone("a", [(1, 1), (1, 4)])
        self.assertEqual(drone.cycle, [(1, 1), (1, 2), (1, 3), (1, 4), (1, 3), (1, 2)])
        self.assertEqual(drone.period, 6)
        self.assertEqual(drone.position(6), (1, 1))      # back at the start
        self.assertEqual(drone.position(9), (1, 4))

    def test_loop_cycle(self):
        drone = Drone("b", [(1, 1), (1, 3), (3, 3), (3, 1)], mode="loop")
        self.assertEqual(drone.period, 8)
        self.assertEqual(drone.cycle[0], (1, 1))
        self.assertEqual(drone.cycle[-1], (2, 1))
        # Every step of the loop moves exactly one tile, including the wrap-around.
        for t in range(drone.period):
            a, b = drone.position(t), drone.position(t + 1)
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_facing_turns_round_at_the_end(self):
        drone = Drone("a", [(1, 1), (1, 4)])
        self.assertEqual(drone.facing(0), (0, 1))        # heading East
        self.assertEqual(drone.facing(3), (0, -1))       # at the end, heading West

    def test_clock_period_is_lcm(self):
        a = Drone("a", [(1, 1), (1, 4)])                  # 6
        b = Drone("b", [(1, 1), (1, 3), (3, 3), (3, 1)], mode="loop")   # 8
        self.assertEqual(drone_clock_period([a, b]), 24)
        self.assertEqual(drone_clock_period([]), 1)


class TestVision(unittest.TestCase):

    def test_sees_two_tiles_ahead(self):
        drone = Drone("a", [(1, 1), (1, 5)])
        self.assertEqual(drone.vision(0, GRID), {(1, 1), (1, 2), (1, 3)})

    def test_walls_and_doors_block_sight(self):
        drone = Drone("a", [(3, 1), (1, 1)])              # heading North at t=0
        self.assertEqual(drone.vision(0, GRID), {(3, 1), (2, 1), (1, 1)})
        door = Drone("d", [(2, 4), (2, 5)])               # heading East, away from the door
        self.assertNotIn((2, 3), door.vision(0, GRID))
        # At (2,5) facing West: (2,4) is visible, but the door at (2,3) stops the view.
        self.assertEqual(Drone("w", [(2, 5), (2, 4)]).vision(0, GRID), {(2, 5), (2, 4)})

    def test_watched_tiles_union(self):
        a = Drone("a", [(1, 1), (1, 5)])
        b = Drone("b", [(3, 5), (3, 1)])
        tiles = watched_tiles([a, b], 0, GRID)
        self.assertIn((1, 3), tiles)
        self.assertIn((3, 3), tiles)


class TestDetection(unittest.TestCase):

    def test_seen_in_front(self):
        drone = Drone("a", [(1, 1), (1, 5)])
        # Player steps into (1,4); at t=1 the drone is at (1,2) looking at (1,3),(1,4).
        self.assertTrue(is_detected([drone], GRID, (2, 4), (1, 4), 0, 1))

    def test_behind_is_safe(self):
        drone = Drone("a", [(1, 2), (1, 5)])
        self.assertFalse(is_detected([drone], GRID, (2, 1), (1, 1), 0, 1))

    def test_swap_counts_as_caught(self):
        drone = Drone("a", [(1, 2), (1, 3)], sight=0)     # sight 0: only its own tile
        # Drone goes (1,2)->(1,3) while the player goes (1,3)->(1,2).
        self.assertTrue(is_detected([drone], GRID, (1, 3), (1, 2), 0, 1))

    def test_frozen_drones_do_not_move(self):
        drone = Drone("a", [(1, 1), (1, 5)])
        # Clock stays at 0: drone still at (1,1) seeing (1,2),(1,3); (1,4) is safe.
        self.assertFalse(is_detected([drone], GRID, (2, 4), (1, 4), 0, 0))


if __name__ == "__main__":
    unittest.main()
