"""Heist Planner Game | Mission Strategy Simulator - start the game from here.

    python app.py

This file only configures logging, loads the configuration, creates the
database repository, builds the main window and starts mainloop().
"""

import logging
import tkinter as tk

from core import config
from database.database_manager import create_repository
from ui.main_window import MainWindow


def main() -> None:
    config.setup_logging()
    config.load_env_file()
    logger = logging.getLogger("app")
    logger.info("Starting %s", config.APP_TITLE)

    repository, db_status = create_repository()
    logger.info("Database: %s", db_status)

    root = tk.Tk()
    MainWindow(root, repository, db_status)
    root.mainloop()


if __name__ == "__main__":
    main()
