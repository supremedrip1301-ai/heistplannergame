"""Oracle repository: saves runs through real PL/SQL stored procedures.

* Uses the python-oracledb driver in its default THIN mode, so no Oracle
  Instant Client is needed (oracledb.init_oracle_client() is never called).
* Credentials come from the environment or the local .env file:
  ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN (for example localhost:1521/FREEPDB1).
* HP_SAVE_RUN and HP_GET_STATS are called with cursor.callproc(); OUT
  parameters are cursor.var() objects. The history query uses bind variables
  (:player, :lim) and the PL/SQL function HP_RANK_TITLE.
* The procedures do NOT commit. Python owns the transaction: it commits after
  a successful call and rolls back on any error.
"""

import logging
import os

from database.base_repository import BaseRepository, check_record

logger = logging.getLogger(__name__)


class OracleConfigError(Exception):
    """ORACLE_USER / ORACLE_PASSWORD / ORACLE_DSN are not filled in."""


# Error code -> friendly text. Checked in this order against str(error).
FRIENDLY_ERRORS = (
    ("DPY-6005", "Oracle server could not be reached"),
    ("DPY-6000", "Oracle server could not be reached"),
    ("ORA-12541", "Oracle server could not be reached"),
    ("ORA-12514", "Oracle service name not found — check ORACLE_DSN"),
    ("DPY-6001", "Oracle service name not found — check ORACLE_DSN"),
    ("ORA-01017", "Oracle username or password is wrong"),
    ("ORA-28000", "The Oracle account is locked"),
    ("ORA-00942", "Oracle tables or procedures not found — run database/setup_oracle.sql first"),
    ("ORA-06550", "Oracle tables or procedures not found — run database/setup_oracle.sql first"),
    ("PLS-00201", "Oracle tables or procedures not found — run database/setup_oracle.sql first"),
    ("ORA-00904", "Oracle tables or procedures not found — run database/setup_oracle.sql first"),
    ("ORA-20001", "The result had invalid numbers and was rejected"),
    ("ORA-20002", "Unknown mission — run database/setup_oracle.sql again"),
    ("ORA-20003", "The result type was rejected"),
)


def friendly_oracle_message(error: Exception) -> str:
    """Short, non-technical text for an Oracle-related error."""
    if isinstance(error, ModuleNotFoundError):
        return "Oracle driver not installed — run: pip install oracledb"
    if isinstance(error, OracleConfigError):
        return str(error)
    text = str(error)
    for code, message in FRIENDLY_ERRORS:
        if code in text:
            return message
    if "refused" in text.lower() or "timed out" in text.lower():
        return "Oracle server could not be reached"
    return "Oracle error — see logs/heist_planner.log"


class OracleRepository(BaseRepository):

    def __init__(self, user: str, password: str, dsn: str):
        self.user = user
        self.password = password
        self.dsn = dsn
        self.conn = None

    @classmethod
    def from_environment(cls):
        """Build the repository from ORACLE_USER / ORACLE_PASSWORD / ORACLE_DSN."""
        user = os.environ.get("ORACLE_USER", "").strip()
        password = os.environ.get("ORACLE_PASSWORD", "")
        dsn = os.environ.get("ORACLE_DSN", "").strip()
        if not user or not password or not dsn:
            raise OracleConfigError("Oracle settings missing — fill ORACLE_USER, "
                                    "ORACLE_PASSWORD and ORACLE_DSN in .env")
        if user.upper() in ("SYS", "SYSTEM"):
            raise OracleConfigError("Do not use SYS or SYSTEM — use the HEIST user")
        return cls(user, password, dsn)

    def initialise(self) -> None:
        """Connect (Thin mode) and check that the PL/SQL objects exist."""
        import oracledb        # optional package, imported only in Oracle mode
        self.conn = oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM hp_missions")
            cursor.fetchone()
            cursor.execute("SELECT HP_RANK_TITLE(0) FROM dual")
            cursor.fetchone()
        logger.info("Connected to Oracle %s at %s", self.conn.version, self.dsn)

    def save_run(self, record: dict) -> int:
        check_record(record)
        try:
            with self.conn.cursor() as cursor:
                run_id = cursor.var(int)
                cursor.callproc("HP_SAVE_RUN", [
                    record["player_name"],
                    record["mission_id"],
                    record["result"],
                    record["score"],
                    record["moves"],
                    record["route_cost"],
                    record["kit_summary"],
                    "Y" if record["alert_triggered"] else "N",
                    run_id,
                ])
            self.conn.commit()           # Python owns the transaction
        except Exception:
            self.conn.rollback()
            raise
        new_id = int(run_id.getvalue())
        logger.info("Saved run %d in Oracle", new_id)
        return new_id

    def get_stats(self, player_name=None) -> dict:
        with self.conn.cursor() as cursor:
            total = cursor.var(int)
            success = cursor.var(int)
            best = cursor.var(int)
            average = cursor.var(float)
            cursor.callproc("HP_GET_STATS", [player_name, total, success, best, average])
        return {
            "total_runs": int(total.getvalue() or 0),
            "success_runs": int(success.getvalue() or 0),
            "best_score": int(best.getvalue() or 0),
            "avg_score": float(average.getvalue() or 0.0),
        }

    def get_recent_runs(self, limit: int = 100, player_name=None) -> list:
        limit = max(1, min(int(limit), 1000))
        sql = """
            SELECT r.run_id, p.player_name, m.mission_name, r.result, r.score, r.moves,
                   r.route_cost, r.kit_summary, r.alert_triggered,
                   TO_CHAR(r.played_at, 'YYYY-MM-DD HH24:MI:SS') AS played_at,
                   HP_RANK_TITLE(r.score) AS rank_title
              FROM hp_mission_runs r
              JOIN hp_players p ON p.player_id = r.player_id
              JOIN hp_missions m ON m.mission_id = r.mission_id
             WHERE (:player IS NULL OR p.player_name = :player)
             ORDER BY r.run_id DESC
             FETCH FIRST :lim ROWS ONLY"""
        with self.conn.cursor() as cursor:
            cursor.execute(sql, player=player_name, lim=limit)
            columns = [d[0].lower() for d in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def backend_label(self) -> str:
        return "Oracle PL/SQL"

    def close(self) -> None:
        if self.conn is not None:
            try:
                self.conn.close()
            finally:
                self.conn = None

    def friendly_error(self, error: Exception) -> str:
        return friendly_oracle_message(error)
