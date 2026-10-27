"""Tests for core/game_engine.py (MissionRun state machine)."""

import unittest

from core import game_engine as ge
from core.missions import MISSIONS


def walk_route(run):
    """Follow the planned route until it ends (helper for the tests)."""
    while run.has_valid_route():
        result = run.step()
        assert result.ok, result.reason


def finish_mission(run):
    """Plan, walk, collect, plan again, walk to extraction."""
    run.plan_route()
    walk_route(run)
    run.collect_objective()
    if not run.has_valid_route():
        run.plan_route()
    walk_route(run)


class TestMovementRules(unittest.TestCase):

    def setUp(self):
        self.run = ge.MissionRun("Tester", MISSIONS["archive"])

    def test_starts_in_planning_at_start_tile(self):
        self.assertEqual(self.run.status, ge.PLANNING)
        self.assertEqual(self.run.position, (1, 1))
        self.assertEqual(self.run.current_target, (5, 7))

    def test_cannot_step_into_wall(self):
        result = self.run.step((0, 1))
        self.assertFalse(result.ok)
        self.assertEqual(self.run.position, (1, 1))
        self.assertEqual(self.run.moves, 0)

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
        self.assertFalse(self.run.objective_collected)

    def test_reaching_exit_before_collecting_is_not_victory(self):
        route = self.run.plan_route()
        self.assertTrue(route.found)
        # Walk to the exit directly, ignoring the objective.
        from core.pathfinding import find_shortest_path
        to_exit = find_shortest_path(self.run.mission.grid, self.run.position,
                                     self.run.mission.exit, self.run.tile_costs)
        for tile in to_exit.path[1:]:
            self.assertTrue(self.run.step(tile).ok)
        self.assertEqual(self.run.position, self.run.mission.exit)
        self.assertFalse(self.run.is_complete())
        self.assertEqual(self.run.status, ge.IN_PROGRESS)

    def test_leaving_route_invalidates_it(self):
        self.run.plan_route()
        first = self.run.route.path[1]
        other = (2, 1) if first != (2, 1) else (1, 2)
        self.assertTrue(self.run.step(other).ok)
        self.assertFalse(self.run.has_valid_route())


class TestFullMissions(unittest.TestCase):

    def test_archive_full_sequence(self):
        run = ge.MissionRun("Tester", MISSIONS["archive"])
        route = run.plan_route()
        self.assertEqual(route.cost, 14)
        walk_route(run)
        self.assertEqual(run.position, (5, 7))
        self.assertTrue(run.can_collect())
        self.assertFalse(run.collect_objective())       # no alert in the Archive
        self.assertEqual(run.status, ge.OBJECTIVE_SECURED)
        self.assertEqual(run.current_target, (7, 1))
        self.assertFalse(run.can_collect())             # only once
        self.assertEqual(run.plan_route().cost, 8)
        walk_route(run)
        self.assertTrue(run.is_complete())
        self.assertEqual((run.moves, run.effort), (22, 22))
        self.assertEqual(run.score.total, 500 + 200 + 100 + 0 - 110)

    def test_gallery_with_boots_scores_810(self):
        kit = ("scanner", "boots", "repair")
        run = ge.MissionRun("Tester", MISSIONS["gallery"], kit, best_usefulness=15)
        self.assertEqual(run.chosen_usefulness, 15)
        self.assertEqual(run.plan_route().cost, 13)
        finish_mission(run)
        self.assertTrue(run.is_complete())
        self.assertEqual(run.effort, 28)
        self.assertEqual(run.score.total, 810)

    def test_gallery_without_boots_uses_long_route(self):
        run = ge.MissionRun("Tester", MISSIONS["gallery"])
        route = run.plan_route()
        self.assertEqual((route.cost, route.steps), (17, 17))

    def test_invalid_kit_rejected(self):
        with self.assertRaises(ValueError):
            ge.MissionRun("T", MISSIONS["relay"], ("shield", "decoy"))   # 9 energy
        with self.assertRaises(ValueError):
            ge.MissionRun("T", MISSIONS["relay"], ("ghost",))


class TestRelayAlert(unittest.TestCase):

    def setUp(self):
        self.run = ge.MissionRun("Tester", MISSIONS["relay"])

    def test_alert_fires_on_collection_and_reroutes(self):
        self.assertEqual(self.run.plan_route().cost, 13)
        walk_route(self.run)
        self.assertTrue(self.run.collect_objective())   # alert fired
        self.assertTrue(self.run.alert_triggered)
        self.assertIn((5, 5), self.run.sealed_tiles)
        self.assertTrue(self.run.has_valid_route())    # re-planned automatically
        self.assertEqual(self.run.route.cost, 19)
        self.assertNotIn((5, 5), self.run.route.path)
        walk_route(self.run)
        self.assertTrue(self.run.is_complete())
        self.assertEqual(self.run.score.alert_penalty, 50)

    def test_cannot_step_into_sealed_gate(self):
        self.assertTrue(self.run.trigger_alert())
        self.run.position = (5, 4)                     # next to the gate
        result = self.run.step((5, 5))
        self.assertFalse(result.ok)
        self.assertEqual(self.run.position, (5, 4))

    def test_alert_happens_only_once(self):
        self.assertTrue(self.run.trigger_alert())
        self.assertFalse(self.run.trigger_alert())
        self.assertFalse(self.run.can_trigger_alert())

    def test_early_alert_changes_route_home(self):
        self.run.trigger_alert()
        walk_route(self.run)
        self.assertFalse(self.run.collect_objective())   # alert already happened
        self.assertEqual(self.run.plan_route().cost, 19)

    def test_alert_invalidates_current_route(self):
        self.run.plan_route()
        walk_route(self.run)
        self.run.collect_objective()
        self.run.plan_route()                         # same as automatic re-plan
        self.assertEqual(self.run.route.cost, 19)

    def test_decoy_cancels_penalty(self):
        run = ge.MissionRun("T", MISSIONS["relay"], ("decoy", "repair", "lens"), 14)
        finish_mission(run)
        self.assertEqual(run.score.alert_penalty, 0)
        self.assertEqual(run.score.total, 500 + 200 + 100 + 150 - 5 * (13 + 19))

    def test_no_alert_in_archive(self):
        run = ge.MissionRun("T", MISSIONS["archive"])
        self.assertFalse(run.can_trigger_alert())
        self.assertFalse(run.trigger_alert())

    def test_scanner_reveals_weak_point(self):
        self.assertFalse(self.run.weak_point_visible)
        run = ge.MissionRun("T", MISSIONS["relay"], ("scanner",))
        self.assertTrue(run.weak_point_visible)

    def test_no_route_status(self):
        # Seal the only way out of a dead end to force a "no safe route".
        self.run.position = (5, 4)
        self.run.sealed_tiles.update({(5, 5), (4, 1), (6, 1)})
        result = self.run.plan_route()
        self.assertFalse(result.found)
        self.assertEqual(self.run.status, ge.NO_ROUTE)
        self.assertFalse(self.run.step((5, 3)).ok)


class TestRestartAndSaving(unittest.TestCase):

    def test_restart_restores_original_state(self):
        run = ge.MissionRun("T", MISSIONS["relay"])
        finish_mission(run)
        run.result_saved = True
        token = run.run_token
        run.restart()
        self.assertEqual(run.position, (1, 1))
        self.assertEqual(run.sealed_tiles, set())          # gate open again
        self.assertFalse(run.alert_triggered)
        self.assertFalse(run.objective_collected)
        self.assertEqual((run.moves, run.effort), (0, 0))
        self.assertIsNone(run.route)
        self.assertFalse(run.result_saved)
        self.assertEqual(run.status, ge.PLANNING)
        self.assertEqual(run.run_token, token + 1)
        self.assertEqual(run.plan_route().cost, 13)

    def test_save_once(self):
        run = ge.MissionRun("T", MISSIONS["archive"])
        finish_mission(run)
        saved = []

        def fake_save(record):
            saved.append(record)
            return len(saved)

        self.assertEqual(run.save_once(fake_save), 1)
        self.assertIsNone(run.save_once(fake_save))
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["result"], "SUCCESS")
        self.assertEqual(saved[0]["score"], run.score.total)

    def test_abandoned_record(self):
        run = ge.MissionRun("T", MISSIONS["archive"])
        self.assertFalse(run.needs_abandon_save())
        run.step((1, 2))
        self.assertTrue(run.needs_abandon_save())
        run.abandon()
        record = run.build_record()
        self.assertEqual((record["result"], record["score"], record["moves"]),
                         ("ABANDONED", 0, 1))

    def test_cannot_save_active_run(self):
        run = ge.MissionRun("T", MISSIONS["archive"])
        with self.assertRaises(ValueError):
            run.save_once(lambda record: 1)


if __name__ == "__main__":
    unittest.main()
