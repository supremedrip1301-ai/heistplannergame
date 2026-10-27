"""Mission scoring and rank titles.

This module only receives plain numbers (chosen usefulness, best possible
usefulness, route effort, alert flag, decoy flag). It does not know how the
best kit was found, so it contains no Knapsack code at all.

Example (README): Gallery with the suggested kit and optimal routes:
effort 13 + 15 = 28, so 500 + 200 + 100 + 150 - 28*5 = 810.
"""

from dataclasses import dataclass

BASE_SUCCESS = 500
OBJECTIVE_BONUS = 200
EXTRACTION_BONUS = 100
PREP_BONUS_MAX = 150
EFFORT_PENALTY_PER_UNIT = 5
ALERT_PENALTY = 50

# Rank thresholds, highest first. The Oracle function HP_RANK_TITLE uses the
# same numbers, and the SQLite repository calls rank_title() below.
RANK_THRESHOLDS = (
    (800, "Phantom"),
    (650, "Specialist"),
    (450, "Operative"),
)
LOWEST_RANK = "Rookie"


@dataclass
class ScoreBreakdown:
    """Every part of the final score, so the debrief can show the sum."""
    base: int
    objective_bonus: int
    extraction_bonus: int
    prep_bonus: int
    effort_penalty: int
    alert_penalty: int
    total: int

    def lines(self) -> list:
        """(label, signed amount) pairs for the debrief screen."""
        return [
            ("Mission success", self.base),
            ("Objective secured", self.objective_bonus),
            ("Clean extraction", self.extraction_bonus),
            ("Preparation bonus", self.prep_bonus),
            ("Effort spent", -self.effort_penalty),
            ("Alert raised", -self.alert_penalty),
        ]


def preparation_bonus(chosen_usefulness: int, best_usefulness: int) -> int:
    """round(150 * chosen / best), or 0 when best is 0."""
    if best_usefulness <= 0:
        return 0
    return round(PREP_BONUS_MAX * chosen_usefulness / best_usefulness)


def readiness_percent(chosen_usefulness: int, best_usefulness: int) -> int:
    """Mission readiness shown on the preparation screen (0..100)."""
    if best_usefulness <= 0:
        return 0
    return round(100 * chosen_usefulness / best_usefulness)


def calculate_score(chosen_usefulness: int, best_usefulness: int, total_effort: int,
                    alert_happened: bool, carried_decoy: bool) -> ScoreBreakdown:
    """Final score of a completed mission, as a ScoreBreakdown."""
    prep = preparation_bonus(chosen_usefulness, best_usefulness)
    effort_penalty = EFFORT_PENALTY_PER_UNIT * total_effort
    alert_penalty = 0
    if alert_happened and not carried_decoy:
        alert_penalty = ALERT_PENALTY
    raw = (BASE_SUCCESS + OBJECTIVE_BONUS + EXTRACTION_BONUS + prep
           - effort_penalty - alert_penalty)
    total = max(0, raw)
    return ScoreBreakdown(BASE_SUCCESS, OBJECTIVE_BONUS, EXTRACTION_BONUS, prep,
                          effort_penalty, alert_penalty, total)


def rank_title(score: int) -> str:
    """Turn a score into a rank label (same thresholds as HP_RANK_TITLE)."""
    for threshold, title in RANK_THRESHOLDS:
        if score >= threshold:
            return title
    return LOWEST_RANK
