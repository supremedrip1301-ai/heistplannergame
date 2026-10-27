"""SQLite repository: the default local save, no server and no setup needed.

SQLite does NOT run PL/SQL. The same rules that Oracle keeps in stored
procedures (validation, find-or-create player, rank thresholds) are done
here in Python, with parameterised queries ('?' placeholders) only.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from core import config
from core.missions import MISSIONS
from core.scoring import rank_title
from database.base_repository import BaseRepository, check_record, empty_stats

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    player_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL UNIQUE,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS missions (
    mission_id   TEXT PRIMARY KEY,
    mission_name TEXT NOT NULL,
    difficulty   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mission_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id       INTEGER NOT NULL REFERENCES players(player_id),
    mission_id      TEXT NOT NULL REFERENCES missions(mission_id),
    result          TEXT NOT NULL CHECK (result IN ('SUCCESS', 'ABANDONED')),
    score           INTEGER NOT NULL CHECK (score >= 0),
    moves           INTEGER NOT NULL,
    route_cost      INTEGER NOT NULL,
    kit_summary     TEXT,
    alert_triggered TEXT NOT NULL CHECK (alert_triggered IN ('Y', 'N')),
    played_at       TEXT NOT NULL
);
"""


class SQLiteRepository(BaseRepository):

    def __init__(self, db_path: Path = config.SQLITE_FILE):
        self.db_path = Path(db_path)
        self.conn = None

    def initialise(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)   # creates data/
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        with self.conn:                       # one transaction: commit or roll back
            self.conn.executescript(SCHEMA)
            for mission in MISSIONS.values():
                self.conn.execute(
                    "INSERT OR IGNORE INTO missions (mission_id, mission_name, difficulty) "
                    "VALUES (?, ?, ?)",
                    (mission.mission_id, mission.name, mission.difficulty))
        logger.info("SQLite ready at %s", self.db_path)

    def save_run(self, record: dict) -> int:
        check_record(record)
        now = datetime.now().isoformat(timespec="seconds")
        with self.conn:
            # Find or create the player (same idea as HP_SAVE_RUN in Oracle).
            self.conn.execute(
                "INSERT OR IGNORE INTO players (player_name, created_at) VALUES (?, ?)",
                (record["player_name"], now))
            row = self.conn.execute("SELECT player_id FROM players WHERE player_name = ?",
                                    (record["player_name"],)).fetchone()
            cursor = self.conn.execute(
                "INSERT INTO mission_runs (player_id, mission_id, result, score, moves, "
                "route_cost, kit_summary, alert_triggered, played_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["player_id"], record["mission_id"], record["result"], record["score"],
                 record["moves"], record["route_cost"], record["kit_summary"],
                 "Y" if record["alert_triggered"] else "N", now))
            run_id = cursor.lastrowid
        logger.info("Saved run %d (%s, %s, score %d)", run_id, record["player_name"],
                    record["mission_id"], record["score"])
        return run_id

    def get_stats(self, player_name=None) -> dict:
        sql = ("SELECT COUNT(*) AS total_runs, "
               "COALESCE(SUM(CASE WHEN r.result = 'SUCCESS' THEN 1 ELSE 0 END), 0) "
               "AS success_runs, "
               "COALESCE(MAX(r.score), 0) AS best_score, "
               "COALESCE(AVG(CASE WHEN r.result = 'SUCCESS' THEN r.score END), 0) "
               "AS avg_score "
               "FROM mission_runs r JOIN players p ON p.player_id = r.player_id")
        params = ()
        if player_name is not None:
            sql = sql + " WHERE p.player_name = ?"
            params = (player_name,)
        row = self.conn.execute(sql, params).fetchone()
        if row is None:
            return empty_stats()
        return {"total_runs": row["total_runs"], "success_runs": row["success_runs"],
                "best_score": row["best_score"], "avg_score": float(row["avg_score"])}

    def get_recent_runs(self, limit: int = 100, player_name=None) -> list:
        limit = max(1, min(int(limit), 1000))
        sql = ("SELECT r.run_id, p.player_name, m.mission_name, r.result, r.score, r.moves, "
               "r.route_cost, r.kit_summary, r.alert_triggered, r.played_at "
               "FROM mission_runs r "
               "JOIN players p ON p.player_id = r.player_id "
               "JOIN missions m ON m.mission_id = r.mission_id")
        params = []
        if player_name is not None:
            sql = sql + " WHERE p.player_name = ?"
            params.append(player_name)
        sql = sql + " ORDER BY r.run_id DESC LIMIT ?"
        params.append(limit)
        runs = []
        for row in self.conn.execute(sql, params):
            run = dict(row)
            run["rank_title"] = rank_title(run["score"])   # same thresholds as Oracle
            run["played_at"] = run["played_at"].replace("T", " ")
            runs.append(run)
        return runs

    def backend_label(self) -> str:
        return "Local save: SQLite"

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def friendly_error(self, error: Exception) -> str:
        return "The local save file could not be written. See logs/heist_planner.log."
