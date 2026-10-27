"""Gadget catalogue: the single place where every gadget is defined.

The catalogue is a dictionary keyed by gadget ID (the Worksheet 2.B style),
so membership checks are simply `if gadget_id in GADGETS`.
How useful each gadget is depends on the mission, so those numbers live in
the mission definitions (core/missions.py), not here.
"""


class Gadget:
    """One piece of equipment the player can carry."""

    def __init__(self, gadget_id: str, name: str, energy_cost: int,
                 description: str, effect: str):
        self.gadget_id = gadget_id
        self.name = name
        self.energy_cost = energy_cost      # "weight" in the Knapsack model
        self.description = description      # one line shown on the prep screen
        self.effect = effect                # what it really does in the game

    def __repr__(self):
        return f"Gadget({self.gadget_id!r}, cost={self.energy_cost})"


SCANNER = "scanner"
DECOY = "decoy"
BOOTS = "boots"
REPAIR = "repair"
LENS = "lens"
SHIELD = "shield"

GADGETS = {
    SCANNER: Gadget(SCANNER, "Pocket Scanner", 3,
                    "Spots weak points in the facility before you enter.",
                    "Relay: the gate that will be sealed is outlined in amber."),
    DECOY: Gadget(DECOY, "Signal Decoy", 4,
                  "Absorbs the blame when an alarm goes off.",
                  "Cancels the alert penalty in the score."),
    BOOTS: Gadget(BOOTS, "Mobility Boots", 3,
                  "Light boots that glide over static fields.",
                  "Static fields cost 2 effort instead of 4."),
    REPAIR: Gadget(REPAIR, "Repair Module", 2,
                   "Patches up worn gear between rooms.",
                   "Counts toward mission readiness."),
    LENS: Gadget(LENS, "Clue Lens", 2,
                 "Reveals hidden markings on panels and files.",
                 "Counts toward mission readiness."),
    SHIELD: Gadget(SHIELD, "Shield Patch", 5,
                   "A bulky barrier against stray sparks.",
                   "Counts toward mission readiness."),
}

# Display order on the preparation screen.
GADGET_ORDER = (SCANNER, DECOY, BOOTS, REPAIR, LENS, SHIELD)


def kit_energy(kit_ids) -> int:
    """Total energy cost of a collection of gadget IDs (unknown IDs ignored)."""
    total = 0
    for gadget_id in kit_ids:
        if gadget_id in GADGETS:
            total = total + GADGETS[gadget_id].energy_cost
    return total


def kit_summary(kit_ids) -> str:
    """Readable kit text such as 'Mobility Boots, Repair Module' ('None' if empty)."""
    names = [GADGETS[g].name for g in GADGET_ORDER if g in kit_ids]
    if not names:
        return "None"
    return ", ".join(names)
