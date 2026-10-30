"""Tests for core/game_engine.py (MissionRun state machine)."""

import unittest

from core import config
from core import game_engine as ge
from core.drones import watched_tiles
from core.missions import MISSIONS
from core.pathfinding import find_shortest_path
from tests.classic_maps import ARCHIVE_MAP, simple_mission


def walk_route(run):
    """Follow the planned route until it ends."""
    while run.has_valid_route():
        result = run.step()
        assert result.ok and not result.caught, result


def play_to_the_end(run, max_turns=400):
    """Let the planner play: route, walk, hack, collect, extract."""
    for _ in range(max_turns):
        if not run.is_active:
            return
        if run.can_hack():
            solved, _ = run.submit_terminal(run.open_terminal().solution)
            assert solved
            continue
        if run.can_collect():
            run.collect_objective()
            continue
        if not run.has_valid_route():
            assert run.plan_route().found, run.status
        result = run.step()
        assert result.ok and not result.caught, result


def next_to_watched_tile(mission):
    """A run standing next to a tile the drones will watch after one turn, and that tile."""
    run = ge.MissionRun("T", mission)
    watched = watched_tiles(mission.drones, 1, mission.grid)
    for target in sorted(watched):
        if mission.tile_at(target) not in ".~":
            continue
        for d_row, d_col in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            near = (target[0] + d_row, target[1] + d_col)
            if mission.tile_at(near) in ".~SOE" and near not in watched:
                run.position = near
                return run, target
    raise AssertionError("no suitable tile")


class TestBasicRules(unittest.TestCase):
    """The basic rules on a plain grid without drones (tests/classic_maps.py)."""

    def setUp(self):
        self.run = ge.MissionRun("Tester", simple_mission(ARCHIVE_MAP))

    def test_starts_in_planning_at_start_tile(self):
        self.assertEqual(self.run.status, ge.PLANNING)
        self.assertEqual(self.run.position, (1, 1))
        self.assertEqual(self.run.current_target, (5, 7))

    def test_cannot_step_into_wall(self):
        result = self.run.step((0, 1))
        self.assertFalse(result.ok)
        self.assertEqual((self.run.position, self.run.moves), ((1, 1), 0))

    def test_cannot_jump_or_move_diagonally(self):
        self.assertFalse(self.run.step((2, 2)).ok)
        self.assertFalse(self.run.step((1, 3)).ok)

    def test_step_without_route_is_refused(self):
        self.assertFalse(self.run.step().ok)

    def test_step_counts_moves_and_effort(self):
        self.assertTrue(self.run.step((1, 2)).ok)
        self.assertEqual((self.run.moves, self.run.effort), (1, 1))
        self.assertEqual(self.run.status, ge.IN_PROGRESS)

    def test_cannot_collect_from_distant_tile(self):
        self.assertFalse(self.run.can_collect())
        self.assertFalse(self.run.collect_objective())

    def test_reaching_exit_before_collecting_is_not_victory(self):
        grid = self.run.mission.grid
        to_exit = find_shortest_path(grid, self.run.position, self.run.mission.exit,
                                     self.run.tile_costs)
        for tile in to_exit.path[1:]:
            self.assertTrue(self.run.step(tile).ok)
        self.assertFalse(self.run.is_complete())
        self.assertEqual(self.run.status, ge.IN_PROGRESS)

    def test_leaving_route_invalidates_it(self):
        self.run.plan_route()
        first = self.run.route.path[1]
        other = (2, 1) if first != (2, 1) else (1, 2)
        self.assertTrue(self.run.step(other).ok)
        self.assertFalse(self.run.has_valid_route())

    def test_full_sequence_and_score(self):
        self.assertEqual(self.run.plan_route().cost, 14)
        walk_route(self.run)
        self.assertTrue(self.run.collect_objective())
        self.assertEqual(self.run.status, ge.OBJECTIVE_SECURED)
        self.assertEqual(self.run.current_target, (7, 1))
        self.assertFalse(self.run.can_collect())                 # only once
        self.assertEqual(self.run.plan_route().cost, 8)
        walk_route(self.run)
        self.assertTrue(self.run.is_complete())
        self.assertEqual((self.run.moves, self.run.effort), (22, 22))
        self.assertEqual(self.run.score.total, 500 + 200 + 100 + 0 - 110)

    def test_restart_restores_original_state(self):
        play_to_the_end(self.run)
        self.run.result_saved = True
        token = self.run.run_token
        self.run.restart()
        self.assertEqual(self.run.position, (1, 1))
        self.assertFalse(self.run.objective_collected)
        self.assertEqual((self.run.moves, self.run.effort, self.run.clock), (0, 0, 0))
        self.assertIsNone(self.run.route)
        self.assertFalse(self.run.result_saved)
        self.assertEqual(self.run.status, ge.PLANNING)
        self.assertEqual(self.run.run_token, token + 1)

    def test_save_once(self):
        play_to_the_end(self.run)
        saved = []

        def fake_save(record):
            saved.append(record)
            return len(saved)

        self.assertEqual(self.run.save_once(fake_save), 1)
        self.assertIsNone(self.run.save_once(fake_save))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["result"], "SUCCESS")
        self.assertEqual(saved[0]["score"], self.run.score.total)
        self.assertEqual((saved[0]["kit_summary"], saved[0]["alert_triggered"]),
                         ("None", False))                      # legacy columns

    def test_abandoned_record(self):
        self.assertFalse(self.run.needs_abandon_save())
        self.run.step((1, 2))
        self.assertTrue(self.run.needs_abandon_save())
        self.run.abandon()
        record = self.run.build_record()
        self.assertEqual((record["result"], record["score"], record["moves"]),
                         ("ABANDONED", 0, 1))

    def test_cannot_save_active_run(self):
        with self.assertRaises(ValueError):
            self.run.save_once(lambda record: 1)


class TestMissionsPlayedThrough(unittest.TestCase):

    def test_each_mission_can_be_completed_unseen(self):
        expected = {"vault": (44, 880), "lab": (94, 830), "penthouse": (91, 845)}
        for mission_id, (effort, score) in expected.items():
            with self.subTest(mission=mission_id):
                run = ge.MissionRun("T", MISSIONS[mission_id], puzzle_seed=1)
                play_to_the_end(run)
                self.assertTrue(run.is_complete())
                self.assertEqual((run.effort, run.score.total), (effort, score))
                if MISSIONS[mission_id].has_keycard:
                    self.assertTrue(run.has_key and run.terminal_solved)

    def test_planner_routes_to_terminal_while_lasers_are_on(self):
        run = ge.MissionRun("T", MISSIONS["lab"], puzzle_seed=1)
        self.assertTrue(run.plan_route().found)
        self.assertEqual(run.route_goal, ge.ROUTE_TO_TERMINAL)
        self.assertIn(MISSIONS["lab"].keycard, run.route.path)   # fetches the keycard


class TestDronesAndWait(unittest.TestCase):

    def test_wait_is_a_turn(self):
        run = ge.MissionRun("T", MISSIONS["vault"])
        self.assertTrue(run.wait().ok)
        self.assertEqual((run.moves, run.waits, run.effort, run.clock), (1, 1, 1, 1))
        self.assertEqual(run.position, MISSIONS["vault"].start)

    def test_walking_into_a_vision_cone_is_caught(self):
        run, target = next_to_watched_tile(MISSIONS["vault"])
        neighbour = run.position
        result = run.step(target)
        self.assertTrue(result.caught)
        self.assertEqual(run.status, ge.CAUGHT)
        self.assertTrue(run.spotted_by)
        self.assertFalse(run.step(neighbour).ok)                # no moves after being caught
        self.assertEqual((run.build_record()["result"], run.build_record()["score"]),
                         ("CAUGHT", 0))
        self.assertFalse(run.needs_abandon_save())

    def test_next_turn_preview(self):
        vault = MISSIONS["vault"]
        run = ge.MissionRun("T", vault)
        self.assertEqual(run.watched_next_turn(), watched_tiles(vault.drones, 1, vault.grid))

    def test_route_with_waits_reports_them(self):
        run = ge.MissionRun("T", MISSIONS["vault"])
        run.plan_route()
        self.assertGreaterEqual(run.route_waits(), 1)
        self.assertEqual(run.route.cost, run.remaining_route_cost())


class TestDoorsTerminalsLasers(unittest.TestCase):

    def test_locked_door_and_laser_refuse(self):
        lab = MISSIONS["lab"]
        run = ge.MissionRun("T", lab)
        door = lab.door_tiles()[0]
        run.position = (door[0], door[1] + 1)
        result = run.step(door)
        self.assertFalse(result.ok)
        self.assertIn("keycard", result.reason)
        laser = lab.laser_tiles()[0]
        run.position = (laser[0] - 1, laser[1])
        result = run.step(laser)
        self.assertFalse(result.ok)
        self.assertIn("Laser", result.reason)

    def test_keycard_pickup(self):
        lab = MISSIONS["lab"]
        run = ge.MissionRun("T", lab)
        run.position = (lab.keycard[0], lab.keycard[1] - 1)
        result = run.step(lab.keycard)
        self.assertTrue(result.picked_key)
        self.assertTrue(run.has_key)

    def on_terminal(self):
        lab = MISSIONS["lab"]
        run = ge.MissionRun("T", lab, puzzle_seed=5)
        run.position = lab.terminal
        run.has_key = True
        return run

    def test_wrong_answer_costs_effort(self):
        run = self.on_terminal()
        self.assertTrue(run.can_hack())
        solved, message = run.submit_terminal([(0, 0)])
        self.assertFalse(solved)
        self.assertEqual((run.effort, run.wrong_answers), (config.TERMINAL_PENALTY, 1))
        self.assertIn("Lockout", message)

    def test_right_answer_switches_lasers_off(self):
        run = self.on_terminal()
        solved, _ = run.submit_terminal(run.open_terminal().solution)
        self.assertTrue(solved)
        self.assertFalse(run.lasers_on)
        self.assertFalse(run.can_hack())

    def test_restart_gives_new_puzzle_and_relocks(self):
        run = self.on_terminal()
        first = run.open_terminal().grid
        run.submit_terminal(run.puzzle.solution)
        run.restart()
        self.assertTrue(run.lasers_on)
        self.assertFalse(run.has_key)
        run.position = MISSIONS["lab"].terminal
        run.has_key = True
        self.assertNotEqual(run.open_terminal().grid, first)


class TestProMode(unittest.TestCase):

    def test_no_route_guidance(self):
        run = ge.MissionRun("T", MISSIONS["vault"], pro_mode=True)
        self.assertFalse(run.plan_route().found)
        self.assertEqual(run.status, ge.PLANNING)               # not a "no route" failure

    def test_pro_bonus_in_score_and_record(self):
        normal = ge.MissionRun("T", MISSIONS["vault"], puzzle_seed=1)
        play_to_the_end(normal)
        # Walk exactly the same tiles by hand in Pro mode.
        guide = ge.MissionRun("T", MISSIONS["vault"])
        pro = ge.MissionRun("T", MISSIONS["vault"], pro_mode=True)
        while guide.is_active:
            if guide.can_collect():
                guide.collect_objective()
                pro.collect_objective()
                continue
            if not guide.has_valid_route():
                guide.plan_route()
            tile = guide.route.path[1]
            guide.step()
            self.assertFalse(pro.step(tile).caught)
        self.assertTrue(pro.is_complete())
        self.assertEqual(pro.score.pro_bonus, round(0.25 * normal.score.total))
        self.assertEqual(pro.score.total, normal.score.total + pro.score.pro_bonus)
        self.assertTrue(pro.build_record()["pro_mode"])


if __name__ == "__main__":
    unittest.main()
