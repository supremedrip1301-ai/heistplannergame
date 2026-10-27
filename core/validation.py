"""Input validation in my worksheet style: .strip(), empty default, range checks."""

from core import config

ALLOWED_NAME_SYMBOLS = " _-."


def validate_player_name(text) -> tuple:
    """Check a player name typed on the main menu.

    Returns (clean_name, error_message). error_message is "" when the name is
    fine. An empty name becomes the default "Agent".
    """
    if text is None:
        text = ""
    name = text.strip()
    if name == "":
        return config.DEFAULT_PLAYER_NAME, ""
    if len(name) > config.MAX_PLAYER_NAME_LENGTH:
        return name, f"Name is too long - use at most {config.MAX_PLAYER_NAME_LENGTH} characters."
    for ch in name:
        if not (ch.isalnum() or ch in ALLOWED_NAME_SYMBOLS):
            return name, "Use only letters, digits, spaces, _ - and ."
    # Collapse repeated inner spaces so "Agent   007" and "Agent 007" match.
    name = " ".join(name.split())
    return name, ""
