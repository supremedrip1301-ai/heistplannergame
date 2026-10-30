"""Mission scoring and rank titles.

This module only receives plain numbers (route effort, the mission's
high-risk bonus, Pro mode flag), so it can be tested on its own.

Score = 500 (success) + 200 (objective) + 100 (extraction)
        + high-risk bonus of the mission - 5 x effort,
        then +25% in Pro mode, never below 0.
"""

from dataclasses import dataclass

BASE_SUCCESS = 500
OBJECTIVE_BONUS = 200
EXTRACTION_BONUS = 100
EFFORT_PENALTY_PER_UNIT = 5
PRO_BONUS_RATE = 0.25        # Pro mode (no route guidance): +25% of the score

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
    risk_bonus: int
    effort_penalty: int
    pro_bonus: int
    total: int

    def lines(self) -> list:
        """(label, signed amount) pairs for the debrief screen."""
        lines = [
            ("Mission success", self.base),
            ("Objective secured", self.objective_bonus),
            ("Clean extraction", self.extraction_bonus),
            ("High-risk bonus", self.risk_bonus),
            ("Effort spent", -self.effort_penalty),
        ]
        if self.pro_bonus:
            lines.append(("Pro mode bonus (+25%)", self.pro_bonus))
        return lines


def calculate_score(total_effort: int, risk_bonus: int = 0,
                    pro_mode: bool = False) -> ScoreBreakdown:
    """Final score of a completed mission, as a ScoreBreakdown.

    Pro mode adds 25% of the score earned so far (only when it is positive).
    """
    effort_penalty = EFFORT_PENALTY_PER_UNIT * total_effort
    raw = BASE_SUCCESS + OBJECTIVE_BONUS + EXTRACTION_BONUS + risk_bonus - effort_penalty
    pro_bonus = 0
    if pro_mode and raw > 0:
        pro_bonus = round(PRO_BONUS_RATE * raw)
    total = max(0, raw + pro_bonus)
    return ScoreBreakdown(BASE_SUCCESS, OBJECTIVE_BONUS, EXTRACTION_BONUS, risk_bonus,
                          effort_penalty, pro_bonus, total)


def rank_title(score: int) -> str:
    """Turn a score into a rank label (same thresholds as HP_RANK_TITLE)."""
    for threshold, title in RANK_THRESHOLDS:
        if score >= threshold:
            return title
    return LOWEST_RANK
