"""Tests for core/scoring.py."""

import unittest

from core import scoring


class TestScoring(unittest.TestCase):

    def test_gallery_example_is_810(self):
        # Suggested kit (usefulness 15 of 15), routes 13 + 15, no alert.
        result = scoring.calculate_score(15, 15, 13 + 15, False, False)
        self.assertEqual(result.prep_bonus, 150)
        self.assertEqual(result.effort_penalty, 140)
        self.assertEqual(result.total, 810)

    def test_breakdown_adds_up(self):
        result = scoring.calculate_score(9, 14, 30, True, False)
        self.assertEqual(sum(amount for _, amount in result.lines()), result.total)

    def test_score_is_clamped_at_zero(self):
        result = scoring.calculate_score(0, 15, 1000, True, False)
        self.assertEqual(result.total, 0)

    def test_decoy_cancels_alert_penalty(self):
        without = scoring.calculate_score(14, 14, 32, True, False)
        with_decoy = scoring.calculate_score(14, 14, 32, True, True)
        self.assertEqual(without.alert_penalty, 50)
        self.assertEqual(with_decoy.alert_penalty, 0)
        self.assertEqual(with_decoy.total - without.total, 50)

    def test_no_alert_no_penalty(self):
        self.assertEqual(scoring.calculate_score(5, 15, 10, False, False).alert_penalty, 0)

    def test_prep_bonus_rounding_and_zero_best(self):
        self.assertEqual(scoring.preparation_bonus(10, 15), 100)
        self.assertEqual(scoring.preparation_bonus(7, 15), 70)
        self.assertEqual(scoring.preparation_bonus(0, 0), 0)
        self.assertEqual(scoring.readiness_percent(15, 15), 100)
        self.assertEqual(scoring.readiness_percent(9, 14), 64)

    def test_risk_bonus_and_pro_bonus(self):
        normal = scoring.calculate_score(15, 15, 40, False, False, risk_bonus=150)
        self.assertEqual(normal.total, 500 + 200 + 100 + 150 + 150 - 200)
        pro = scoring.calculate_score(15, 15, 40, False, False, pro_mode=True, risk_bonus=150)
        self.assertEqual(pro.pro_bonus, round(0.25 * normal.total))
        self.assertEqual(pro.total, normal.total + pro.pro_bonus)
        self.assertEqual(sum(amount for _, amount in pro.lines()), pro.total)
        labels = [label for label, _ in pro.lines()]
        self.assertIn("High-risk bonus", labels)
        self.assertIn("Pro mode bonus (+25%)", labels)

    def test_pro_bonus_never_on_negative(self):
        result = scoring.calculate_score(0, 15, 1000, True, False, pro_mode=True)
        self.assertEqual((result.pro_bonus, result.total), (0, 0))

    def test_old_breakdown_unchanged(self):
        labels = [label for label, _ in scoring.calculate_score(15, 15, 28, False, False).lines()]
        self.assertEqual(labels, ["Mission success", "Objective secured", "Clean extraction",
                                  "Preparation bonus", "Effort spent", "Alert raised"])

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
