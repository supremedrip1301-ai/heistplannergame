"""Engine tests for the hard missions: Wait, drones, keycards, terminals, gadgets, Pro mode."""

import unittest

from core import config
from core import game_engine as ge
from core.drones import watched_tiles
from core.missions import MISSIONS


def play_to_the_end(run, max_turns=400):
    """Let the planner play: route, walk, hack, collect, extract."""
    for _ in range(max_turns):
        if not run.is_active:
            return
        if run.can_hack():
            puzzle = run.open_terminal()
            solved, _ = run.submit_terminal(puzzle.solution)
            assert solved
            continue
        if run.can_collect():
            run.collect_objective()
            continue
        if not run.has_valid_route():
            assert run.plan_route().found, run.status
        result = run.step()
        assert result.ok and not result.caught, result


def tile_next_to_watched(mission, kit=()):
    """A run standing next to a tile the drones will watch after one turn, and that tile."""
    run = ge.MissionRun("T", mission, kit)
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


class TestFullHardMissions(unittest.TestCase):

    def test_each_hard_mission_can_be_completed_unseen(self):
        for mission_id in ("vault", "lab", "penthouse"):
            with self.subTest(mission=mission_id):
                run = ge.MissionRun("T", MISSIONS[mission_id], puzzle_seed=1)
                play_to_the_end(run)
                self.assertTrue(run.is_complete())
                self.assertFalse(run.is_caught())
                self.assertGreater(run.score.risk_bonus, 0)
                if MISSIONS[mission_id].has_keycard:
                    self.assertTrue(run.has_key)
                    self.assertTrue(run.terminal_solved)

    def test_planner_routes_to_terminal_while_lasers_are_on(self):
        run = ge.MissionRun("T", MISSIONS["lab"], puzzle_seed=1)
        self.assertTrue(run.plan_route().found)
        self.assertEqual(run.route_goal, ge.ROUTE_TO_TERMINAL)
        self.assertIn(MISSIONS["lab"].keycard, run.route.path)   # fetches the keycard


class TestDronesAndWait(unittest.TestCase):

    def test_wait_is_a_turn(self):
        run = ge.MissionRun("T", MISSIONS["vault"])
        result = run.wait()
        self.assertTrue(result.ok)
        self.assertEqual((run.moves, run.waits, run.effort, run.clock), (1, 1, 1, 1))
        self.assertEqual(run.position, MISSIONS["vault"].start)

    def test_walking_into_a_vision_cone_is_caught(self):
        run, target = tile_next_to_watched(MISSIONS["vault"])
        neighbour = run.position
        result = run.step(target)
        self.assertTrue(result.caught)
        self.assertEqual(run.status, ge.CAUGHT)
        self.assertFalse(run.step(neighbour).ok)                # no moves after being caught
        self.assertEqual(run.build_record()["result"], "CAUGHT")
        self.assertEqual(run.build_record()["score"], 0)
        self.assertFalse(run.needs_abandon_save())

    def test_shield_gives_one_second_chance(self):
        run, target = tile_next_to_watched(MISSIONS["vault"], ("shield",))
        result = run.step(target)
        self.assertTrue(result.shielded)
        self.assertTrue(run.is_active)
        self.assertTrue(run.shield_used)

    def test_decoy_freezes_the_drones(self):
        run = ge.MissionRun("T", MISSIONS["vault"], ("decoy",))
        self.assertTrue(run.deploy_decoy())
        self.assertFalse(run.deploy_decoy())                     # once per run
        for _ in range(config.DECOY_FREEZE_TURNS):
            run.wait()
        self.assertEqual(run.clock, 0)                           # drones did not move
        run.wait()
        self.assertEqual(run.clock, 1)

    def test_decoy_needs_drones_and_the_gadget(self):
        self.assertFalse(ge.MissionRun("T", MISSIONS["vault"]).can_deploy_decoy())
        self.assertFalse(ge.MissionRun("T", MISSIONS["gallery"], ("decoy",)).can_deploy_decoy())

    def test_scanner_predicts_next_turn(self):
        vault = MISSIONS["vault"]
        plain = ge.MissionRun("T", vault)
        self.assertEqual(plain.watched_next_turn(), set())
        scanned = ge.MissionRun("T", vault, ("scanner",))
        self.assertEqual(scanned.watched_next_turn(), watched_tiles(vault.drones, 1, vault.grid))

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

    def put_on_terminal(self, kit=()):
        lab = MISSIONS["lab"]
        run = ge.MissionRun("T", lab, kit, puzzle_seed=5)
        run.position = lab.terminal
        run.has_key = True
        return run

    def test_wrong_answer_costs_effort(self):
        run = self.put_on_terminal()
        self.assertTrue(run.can_hack())
        solved, message = run.submit_terminal([(0, 0)])
        self.assertFalse(solved)
        self.assertEqual(run.effort, config.TERMINAL_PENALTY)
        self.assertIn("Lockout", message)

    def test_repair_absorbs_first_wrong_answer(self):
        run = self.put_on_terminal(("repair",))
        run.submit_terminal([(0, 0)])
        self.assertEqual(run.effort, 0)
        run.submit_terminal([(0, 0)])
        self.assertEqual(run.effort, config.TERMINAL_PENALTY)

    def test_right_answer_switches_lasers_off(self):
        run = self.put_on_terminal()
        solved, _ = run.submit_terminal(run.open_terminal().solution)
        self.assertTrue(solved)
        self.assertFalse(run.lasers_on)
        self.assertFalse(run.can_hack())

    def test_lens_shows_the_target(self):
        self.assertEqual(self.put_on_terminal().lens_hint(), "")
        run = self.put_on_terminal(("lens",))
        run.open_terminal()
        self.assertIn(str(run.puzzle.best), run.lens_hint())

    def test_restart_gives_new_puzzle_and_relocks(self):
        run = self.put_on_terminal()
        first = run.open_terminal().grid
        run.submit_terminal(run.puzzle.solution)
        run.restart()
        self.assertTrue(run.lasers_on)
        self.assertFalse(run.has_key)
        self.assertEqual(run.clock, 0)
        run.position = MISSIONS["lab"].terminal
        run.has_key = True
        self.assertNotEqual(run.open_terminal().grid, first)


class TestProMode(unittest.TestCase):

    def test_no_route_guidance(self):
        run = ge.MissionRun("T", MISSIONS["vault"], pro_mode=True)
        self.assertFalse(run.plan_route().found)
        self.assertEqual(run.status, ge.PLANNING)               # not a "no route" failure

    def test_pro_bonus_in_score_and_record(self):
        archive = MISSIONS["archive"]
        normal = ge.MissionRun("T", archive)
        play_to_the_end(normal)
        # Walk exactly the same tiles by hand in Pro mode.
        pro = ge.MissionRun("T", archive, pro_mode=True)
        guide = ge.MissionRun("T", archive)
        guide.plan_route()
        for tile in guide.route.path[1:]:
            pro.step(tile)
        pro.collect_objective()
        guide.position = archive.objective
        guide.objective_collected = True
        guide.plan_route()
        for tile in guide.route.path[1:]:
            pro.step(tile)
        self.assertTrue(pro.is_complete())
        self.assertEqual(pro.score.pro_bonus, round(0.25 * normal.score.total))
        self.assertEqual(pro.score.total, normal.score.total + pro.score.pro_bonus)
        self.assertTrue(pro.build_record()["pro_mode"])

    def test_relay_alert_in_pro_mode_does_not_plan(self):
        run = ge.MissionRun("T", MISSIONS["relay"], pro_mode=True)
        self.assertTrue(run.trigger_alert())
        self.assertIsNone(run.route)
        self.assertTrue(run.is_active)


if __name__ == "__main__":
    unittest.main()
