"""Tests for core/validation.py (player-name rules from the main menu)."""

import unittest

from core.validation import validate_player_name


class TestPlayerName(unittest.TestCase):

    def test_empty_becomes_agent(self):
        self.assertEqual(validate_player_name(""), ("Agent", ""))
        self.assertEqual(validate_player_name("   "), ("Agent", ""))
        self.assertEqual(validate_player_name(None), ("Agent", ""))

    def test_strip_and_allowed_symbols(self):
        self.assertEqual(validate_player_name("  Anshul_K-1.0 "), ("Anshul_K-1.0", ""))
        self.assertEqual(validate_player_name("Agent   007"), ("Agent 007", ""))

    def test_too_long(self):
        name, error = validate_player_name("x" * 31)
        self.assertNotEqual(error, "")
        self.assertEqual(validate_player_name("x" * 30)[1], "")

    def test_bad_characters(self):
        for bad in ["Robert'); DROP TABLE", "a<b>", "name@mail", "tab\tname"]:
            self.assertNotEqual(validate_player_name(bad)[1], "", bad)


if __name__ == "__main__":
    unittest.main()
