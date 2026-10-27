"""Chooses the database backend and falls back to SQLite when Oracle cannot be used."""

import logging

from core import config
from database.sqlite_repository import SQLiteRepository

logger = logging.getLogger(__name__)

STATUS_SQLITE = "Local save: SQLite"
STATUS_ORACLE = "Oracle PL/SQL connected"
STATUS_ORACLE_FALLBACK = "Oracle unavailable — using SQLite"
STATUS_NO_SAVE = "Saving unavailable — results will not be stored"


def open_sqlite(db_path=None):
    """Open the local SQLite save. Returns (repository or None, status text)."""
    try:
        repository = SQLiteRepository(db_path) if db_path else SQLiteRepository()
        repository.initialise()
        return repository, STATUS_SQLITE
    except Exception:
        logger.exception("SQLite could not be opened")
        return None, STATUS_NO_SAVE


def create_repository():
    """Return (repository, status_text) for the configured DATABASE_BACKEND.

    If Oracle is requested but the oracledb package is missing, the settings
    are incomplete, or the connection fails, the technical error is logged and
    the game continues with SQLite. The status text says what happened.
    """
    backend = config.get_backend_choice()
    if backend != "oracle":
        return open_sqlite()

    reason = ""
    try:
        # Imported here so the game never needs oracledb in SQLite mode.
        from database.oracle_repository import OracleRepository
        repository = OracleRepository.from_environment()
        repository.initialise()
        logger.info("Oracle backend ready")
        return repository, STATUS_ORACLE
    except Exception as error:
        logger.error("Oracle mode failed, falling back to SQLite: %r", error)
        from database.oracle_repository import friendly_oracle_message
        reason = friendly_oracle_message(error)

    repository, status = open_sqlite()
    if repository is None:
        return None, status
    return repository, f"{STATUS_ORACLE_FALLBACK} ({reason})"
