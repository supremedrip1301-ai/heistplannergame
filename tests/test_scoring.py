"""Tests for core/scoring.py."""

import unittest

from core import config
from core import scoring


class TestScoring(unittest.TestCase):

    def test_vault_example(self):
        # Planner route in the Vault: effort 44, high-risk bonus 300.
        result = scoring.calculate_score(44, config.RISK_BONUS["vault"])
        self.assertEqual(result.effort_penalty, 220)
        self.assertEqual(result.total, 500 + 200 + 100 + 300 - 220)
        self.assertEqual(result.total, 880)

    def test_breakdown_adds_up(self):
        result = scoring.calculate_score(30, 150)
        self.assertEqual(sum(amount for _, amount in result.lines()), result.total)

    def test_score_is_clamped_at_zero(self):
        self.assertEqual(scoring.calculate_score(1000).total, 0)

    def test_pro_bonus(self):
        normal = scoring.calculate_score(40, 150)
        pro = scoring.calculate_score(40, 150, pro_mode=True)
        self.assertEqual(pro.pro_bonus, round(0.25 * normal.total))
        self.assertEqual(pro.total, normal.total + pro.pro_bonus)
        self.assertEqual(sum(amount for _, amount in pro.lines()), pro.total)
        self.assertIn("Pro mode bonus (+25%)", [label for label, _ in pro.lines()])

    def test_pro_bonus_never_on_negative(self):
        result = scoring.calculate_score(1000, pro_mode=True)
        self.assertEqual((result.pro_bonus, result.total), (0, 0))

    def test_rank_thresholds(self):
        self.assertEqual(scoring.rank_title(810), "Phantom")
        self.assertEqual(scoring.rank_title(800), "Phantom")
        self.assertEqual(scoring.rank_title(799), "Specialist")
        self.assertEqual(scoring.rank_title(650), "Specialist")
        self.assertEqual(scoring.rank_title(649), "Operative")
        self.assertEqual(scoring.rank_title(450), "Operative")
        self.assertEqual(scoring.rank_title(449), "Rookie")
        self.assertEqual(scoring.rank_title(0), "Rookie")


if __name__ == "__main__":
    unittest.main()
