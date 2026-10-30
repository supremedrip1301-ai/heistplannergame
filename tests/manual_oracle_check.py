"""Manual end-to-end Oracle check (NOT auto-discovered: no test_ prefix).

Run it from the project folder only when Oracle is set up:

    python tests\\manual_oracle_check.py

It reads ORACLE_USER / ORACLE_PASSWORD / ORACLE_DSN from .env, connects in
Thin mode, calls HP_SAVE_RUN and HP_GET_STATS, reads history with
HP_RANK_TITLE, checks the audit trigger, and then ROLLS BACK so no test data
is left behind.
"""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from core import config  # noqa: E402
from database.oracle_repository import (OracleRepository,  # noqa: E402
                                        friendly_oracle_message)

TEST_PLAYER = "ORACLE_CHECK"


def check(label: str, condition: bool) -> bool:
    print(("PASS  " if condition else "FAIL  ") + label)
    return condition


def main() -> int:
    config.load_env_file()
    try:
        import oracledb
    except ModuleNotFoundError:
        print("oracledb is not installed. Run: pip install oracledb")
        return 1

    try:
        repo = OracleRepository.from_environment()
        repo.initialise()
    except Exception as error:
        print("Could not connect:", friendly_oracle_message(error))
        print("Technical detail:", error)
        return 1

    conn = repo.conn
    print(f"Connected to Oracle {conn.version} at {repo.dsn} as {repo.user} "
          f"(thin mode: {conn.thin}, driver {oracledb.__version__})")
    ok = True
    try:
        before = repo.get_stats(TEST_PLAYER)
        ok &= check("HP_GET_STATS for a new player returns zeros",
                    before == {"total_runs": 0, "success_runs": 0, "best_score": 0,
                               "avg_score": 0.0})

        record = {"player_name": TEST_PLAYER, "mission_id": "gallery", "result": "SUCCESS",
                  "score": 810, "moves": 24, "route_cost": 28,
                  "kit_summary": "Pocket Scanner, Mobility Boots, Repair Module",
                  "alert_triggered": False}
        # Call the procedure directly (save_run() would COMMIT, we want to roll back).
        with conn.cursor() as cursor:
            run_id = cursor.var(int)
            cursor.callproc("HP_SAVE_RUN", [record["player_name"], record["mission_id"],
                                            record["result"], record["score"],
                                            record["moves"], record["route_cost"],
                                            record["kit_summary"], "N", "N", run_id])
            new_id = run_id.getvalue()
        ok &= check(f"HP_SAVE_RUN returned run ID {new_id}", isinstance(new_id, int))

        after = repo.get_stats(TEST_PLAYER)
        ok &= check(f"HP_GET_STATS after save: {after}",
                    after["total_runs"] == 1 and after["best_score"] == 810)

        runs = repo.get_recent_runs(5, TEST_PLAYER)
        ok &= check("History query with HP_RANK_TITLE shows the run as 'Phantom'",
                    len(runs) == 1 and runs[0]["rank_title"] == "Phantom")

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM hp_run_audit WHERE run_id = :rid",
                           rid=new_id)
            audit_rows = cursor.fetchone()[0]
        ok &= check("Audit trigger wrote one row", audit_rows == 1)

        try:
            with conn.cursor() as cursor:
                cursor.callproc("HP_SAVE_RUN", [TEST_PLAYER, "gallery", "SUCCESS", -1, 1, 1,
                                                "None", "N", "N", cursor.var(int)])
            ok &= check("Negative score rejected", False)
        except oracledb.DatabaseError as error:
            ok &= check(f"Negative score rejected ({str(error).splitlines()[0]})",
                        "ORA-20001" in str(error))
    finally:
        conn.rollback()
        print("Rolled back all test data.")
        repo.close()

    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
