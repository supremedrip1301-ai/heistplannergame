"""BaseRepository: the interface every database backend must provide.

SQLiteRepository and OracleRepository inherit from this class and override
its methods (inheritance + method overriding). The game only talks to this
interface, so the game logic never depends on which database is used.

A run record is a plain dict with the keys:
    player_name, mission_id, result ('SUCCESS'/'ABANDONED'), score, moves,
    route_cost, kit_summary, alert_triggered (bool)
"""

RESULT_VALUES = ("SUCCESS", "ABANDONED")


def check_record(record: dict) -> None:
    """Basic checks before saving (the Oracle procedure re-checks on the server)."""
    required = ("player_name", "mission_id", "result", "score", "moves", "route_cost",
                "kit_summary", "alert_triggered")
    for key in required:
        if key not in record:
            raise ValueError(f"Missing field: {key}")
    if record["result"] not in RESULT_VALUES:
        raise ValueError("Result must be SUCCESS or ABANDONED.")
    if record["score"] < 0 or record["moves"] < 0 or record["route_cost"] < 0:
        raise ValueError("Score, moves and effort cannot be negative.")
    if not str(record["player_name"]).strip():
        raise ValueError("Player name is empty.")


def empty_stats() -> dict:
    return {"total_runs": 0, "success_runs": 0, "best_score": 0, "avg_score": 0.0}


class BaseRepository:
    """Methods every repository overrides."""

    def initialise(self) -> None:
        """Create tables / check the schema."""
        raise NotImplementedError

    def save_run(self, record: dict) -> int:
        """Store one run and return its new run ID."""
        raise NotImplementedError

    def get_stats(self, player_name=None) -> dict:
        """total_runs, success_runs, best_score, avg_score (of successful runs).

        player_name=None means all players. Never returns None values.
        """
        raise NotImplementedError

    def get_recent_runs(self, limit: int = 100, player_name=None) -> list:
        """Newest runs first, as dicts (includes the rank title)."""
        raise NotImplementedError

    def backend_label(self) -> str:
        """Short name shown to the player."""
        raise NotImplementedError

    def close(self) -> None:
        """Release the connection."""
        raise NotImplementedError

    def friendly_error(self, error: Exception) -> str:
        """Turn a technical database error into a short message for the player."""
        return "The result could not be saved."
