"""Project-wide configuration: folder paths, game constants, .env loading and logging.

Every path is built from Path(__file__).resolve(), so the game works no matter
which folder the terminal was opened in.
"""

import logging
import os
from pathlib import Path

# ---------------------------------------------------------------- paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = PROJECT_DIR / "logs"
SQLITE_FILE = DATA_DIR / "heist_planner.db"
LOG_FILE = LOG_DIR / "heist_planner.log"
ENV_FILE = PROJECT_DIR / ".env"

# ---------------------------------------------------------------- game constants
APP_TITLE = "Heist Planner Game | Mission Strategy Simulator"
WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 760
MIN_WIDTH = 1000
MIN_HEIGHT = 680

TICK_MS = 500                 # game clock: drones advance one tile every 0.5 seconds
DEFAULT_PLAYER_NAME = "Agent"
MAX_PLAYER_NAME_LENGTH = 30
HISTORY_LIMIT = 100

TERMINAL_PENALTY = 5          # effort added by a wrong terminal answer (lockout)

# Fixed score bonus per mission: the drone missions need long routes, and
# 5 points are taken off per effort unit, so a perfect run still earns a
# good rank (see core/scoring.py).
RISK_BONUS = {"vault": 300, "lab": 500, "penthouse": 500}

# Tile costs (cost of ENTERING a tile).
FLOOR_COST = 1
STATIC_FIELD_COST = 4

VALID_BACKENDS = ("sqlite", "oracle")


def load_env_file(path: Path = ENV_FILE) -> int:
    """Read KEY=VALUE lines from a .env file into os.environ.

    A tiny replacement for python-dotenv: blank lines and lines starting with
    '#' are skipped, each line is split on the first '=', and variables that
    are already set in the real environment are NOT overridden.
    Returns how many variables were set (0 when the file does not exist).
    """
    if not path.exists():
        return 0
    count = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "" or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key != "" and key not in os.environ:
            os.environ[key] = value
            count = count + 1
    return count


def get_backend_choice() -> str:
    """Return 'sqlite' or 'oracle' from DATABASE_BACKEND (default 'sqlite')."""
    choice = os.environ.get("DATABASE_BACKEND", "sqlite").strip().lower()
    if choice not in VALID_BACKENDS:
        logging.getLogger(__name__).warning(
            "Unknown DATABASE_BACKEND %r, using sqlite", choice)
        return "sqlite"
    return choice


def setup_logging(level: int = logging.INFO) -> None:
    """Send log messages to logs/heist_planner.log and to the console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if root.handlers:          # already configured (for example by a test)
        return
    root.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
