"""Tests for database/sqlite_repository.py using a temporary database file."""

import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from core import game_engine as ge
from core.missions import MISSIONS
from database.database_manager import create_repository
from database.sqlite_repository import SQLiteRepository


def sample_record(**changes):
    record = {"player_name": "Tester", "mission_id": "gallery", "result": "SUCCESS",
              "score": 810, "moves": 24, "route_cost": 28,
              "kit_summary": "Pocket Scanner, Mobility Boots, Repair Module",
              "alert_triggered": False}
    record.update(changes)
    return record


class TestSQLiteRepository(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.path = Path(self.folder) / "sub" / "test.db"     # 'sub' is created
        self.repo = SQLiteRepository(self.path)
        self.repo.initialise()

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_fresh_database_is_empty(self):
        self.assertTrue(self.path.exists())
        self.assertEqual(self.repo.get_stats(),
                         {"total_runs": 0, "success_runs": 0, "best_score": 0,
                          "avg_score": 0.0})
        self.assertEqual(self.repo.get_stats("Nobody")["total_runs"], 0)
        self.assertEqual(self.repo.get_recent_runs(), [])

    def test_missions_are_seeded_once(self):
        self.repo.close()
        self.repo = SQLiteRepository(self.path)
        self.repo.initialise()                       # second start: INSERT OR IGNORE
        count = self.repo.conn.execute("SELECT COUNT(*) FROM missions").fetchone()[0]
        self.assertEqual(count, 6)

    def test_save_appears_in_history_and_stats(self):
        run_id = self.repo.save_run(sample_record())
        self.assertIsInstance(run_id, int)
        runs = self.repo.get_recent_runs()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["run_id"], run_id)
        self.assertEqual(runs[0]["mission_name"], "The Gallery")
        self.assertEqual(runs[0]["score"], 810)
        self.assertEqual(runs[0]["rank_title"], "Phantom")
        self.assertEqual(runs[0]["alert_triggered"], "N")
        stats = self.repo.get_stats("Tester")
        self.assertEqual((stats["total_runs"], stats["success_runs"], stats["best_score"]),
                         (1, 1, 810))

    def test_stats_ignore_abandoned_in_average(self):
        self.repo.save_run(sample_record(score=600))
        self.repo.save_run(sample_record(result="ABANDONED", score=0))
        stats = self.repo.get_stats("Tester")
        self.assertEqual(stats["total_runs"], 2)
        self.assertEqual(stats["success_runs"], 1)
        self.assertEqual(stats["avg_score"], 600.0)

    def test_player_filter_and_newest_first(self):
        self.repo.save_run(sample_record(player_name="A", score=100))
        self.repo.save_run(sample_record(player_name="B", score=200))
        self.repo.save_run(sample_record(player_name="A", score=300))
        mine = self.repo.get_recent_runs(player_name="A")
        self.assertEqual([r["score"] for r in mine], [300, 100])
        everyone = self.repo.get_recent_runs()
        self.assertEqual([r["score"] for r in everyone], [300, 200, 100])
        self.assertEqual(len(self.repo.get_recent_runs(limit=2)), 2)
        players = self.repo.conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        self.assertEqual(players, 2)                 # 'A' created only once

    def test_records_survive_restart(self):
        self.repo.save_run(sample_record())
        self.repo.close()
        self.repo = SQLiteRepository(self.path)
        self.repo.initialise()
        self.assertEqual(len(self.repo.get_recent_runs()), 1)

    def test_invalid_records_rejected(self):
        with self.assertRaises(ValueError):
            self.repo.save_run(sample_record(score=-5))
        with self.assertRaises(ValueError):
            self.repo.save_run(sample_record(result="WON"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.save_run(sample_record(mission_id="moon"))   # foreign key
        self.assertEqual(self.repo.get_recent_runs(), [])

    def test_sql_injection_text_is_stored_as_plain_text(self):
        name = "x'); DROP TABLE players; --"
        self.repo.save_run(sample_record(player_name=name))
        self.assertEqual(self.repo.get_recent_runs()[0]["player_name"], name)

    def test_engine_save_path_saves_only_once(self):
        run = ge.MissionRun("Tester", MISSIONS["archive"])
        run.plan_route()
        while run.has_valid_route():
            run.step()
        run.collect_objective()
        run.plan_route()
        while run.has_valid_route():
            run.step()
        self.assertTrue(run.is_complete())
        first = run.save_once(self.repo.save_run)
        second = run.save_once(self.repo.save_run)
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(len(self.repo.get_recent_runs()), 1)
        self.assertEqual(self.repo.get_recent_runs()[0]["score"], run.score.total)


class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        self.saved = {k: os.environ.get(k) for k in
                      ("DATABASE_BACKEND", "ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")}

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_oracle_without_settings_falls_back_to_sqlite(self):
        os.environ["DATABASE_BACKEND"] = "oracle"
        os.environ["ORACLE_USER"] = ""
        repo, status = create_repository()
        try:
            self.assertIsInstance(repo, SQLiteRepository)
            self.assertIn("Oracle unavailable", status)
        finally:
            repo.close()

    def test_unknown_backend_means_sqlite(self):
        os.environ["DATABASE_BACKEND"] = "mongo"
        repo, status = create_repository()
        try:
            self.assertIsInstance(repo, SQLiteRepository)
            self.assertEqual(status, "Local save: SQLite")
        finally:
            repo.close()


if __name__ == "__main__":
    unittest.main()
