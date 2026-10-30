"""Offline tests for database/oracle_repository.py (no Oracle server needed).

A small fake connection records what the repository sends, so we can check
that HP_SAVE_RUN is called with the right arguments, that Python commits
after success and rolls back after a failure. The real end-to-end check is
tests/manual_oracle_check.py, run only when an Oracle connection exists.
"""

import os
import unittest

from database.oracle_repository import (OracleConfigError, OracleRepository,
                                        friendly_oracle_message)


class FakeVar:
    def __init__(self, value=None):
        self.value = value

    def getvalue(self):
        return self.value


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.conn.cursors_closed += 1

    def var(self, kind):
        return FakeVar()

    def callproc(self, name, args):
        self.conn.calls.append((name, args))
        if self.conn.fail:
            raise RuntimeError("ORA-20001: Score, moves and route cost must be zero or more.")
        if name == "HP_SAVE_RUN":
            args[-1].value = 42
        if name == "HP_GET_STATS":
            args[1].value, args[2].value, args[3].value, args[4].value = 3, 2, 810, None


class FakeConnection:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []
        self.commits = 0
        self.rollbacks = 0
        self.cursors_closed = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


RECORD = {"player_name": "Tester", "mission_id": "relay", "result": "SUCCESS", "score": 760,
          "moves": 32, "route_cost": 32, "kit_summary": "Signal Decoy", "alert_triggered": True}


class TestOracleRepositoryOffline(unittest.TestCase):

    def make_repo(self, fail=False):
        repo = OracleRepository("heist", "secret", "localhost:1521/FREEPDB1")
        repo.conn = FakeConnection(fail)
        return repo

    def test_save_calls_procedure_and_commits(self):
        repo = self.make_repo()
        self.assertEqual(repo.save_run(RECORD), 42)
        name, args = repo.conn.calls[0]
        self.assertEqual(name, "HP_SAVE_RUN")
        self.assertEqual(args[:9], ["Tester", "relay", "SUCCESS", 760, 32, 32,
                                    "Signal Decoy", "Y", "N"])
        self.assertEqual((repo.conn.commits, repo.conn.rollbacks), (1, 0))
        self.assertEqual(repo.conn.cursors_closed, 1)

    def test_failed_save_rolls_back(self):
        repo = self.make_repo(fail=True)
        with self.assertRaises(RuntimeError):
            repo.save_run(RECORD)
        self.assertEqual((repo.conn.commits, repo.conn.rollbacks), (0, 1))

    def test_stats_never_none(self):
        repo = self.make_repo()
        stats = repo.get_stats(None)
        self.assertEqual(stats, {"total_runs": 3, "success_runs": 2, "best_score": 810,
                                 "avg_score": 0.0})
        self.assertEqual(repo.conn.calls[0][0], "HP_GET_STATS")
        self.assertIsNone(repo.conn.calls[0][1][0])          # NULL = all players

    def test_invalid_record_never_reaches_oracle(self):
        repo = self.make_repo()
        with self.assertRaises(ValueError):
            repo.save_run(dict(RECORD, score=-1))
        self.assertEqual(repo.conn.calls, [])


class TestConfigAndMessages(unittest.TestCase):

    def setUp(self):
        self.saved = {k: os.environ.get(k) for k in ("ORACLE_USER", "ORACLE_PASSWORD",
                                                     "ORACLE_DSN")}

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_missing_settings(self):
        os.environ["ORACLE_USER"] = ""
        with self.assertRaises(OracleConfigError):
            OracleRepository.from_environment()

    def test_system_user_refused(self):
        os.environ.update({"ORACLE_USER": "system", "ORACLE_PASSWORD": "x",
                           "ORACLE_DSN": "localhost:1521/FREEPDB1"})
        with self.assertRaises(OracleConfigError):
            OracleRepository.from_environment()

    def test_friendly_messages(self):
        cases = {
            "DPY-6005: cannot connect to database": "could not be reached",
            "ORA-01017: invalid credential or not authorized": "username or password",
            "ORA-00942: table or view does not exist": "setup_oracle.sql",
            "ORA-06550: line 1, column 7: PLS-00201": "setup_oracle.sql",
        }
        for text, expected in cases.items():
            self.assertIn(expected, friendly_oracle_message(RuntimeError(text)))
        self.assertIn("pip install oracledb",
                      friendly_oracle_message(ModuleNotFoundError("oracledb")))


if __name__ == "__main__":
    unittest.main()
