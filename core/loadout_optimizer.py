"""Suggested Kit: the 0/1 Knapsack problem solved with dynamic programming.

Mapping to the textbook problem
    item      = gadget (each one can be taken at most once -> "0/1")
    weight    = energy cost
    value     = usefulness of that gadget for the chosen mission
    capacity  = 8 energy units

DP table
    best[i][c] = the best result using only the first i items with at most c
                 energy. Each cell stores a pair (usefulness, -energy), and
                 pairs are compared like tuples: higher usefulness wins, and
                 for equal usefulness the LOWER energy wins (because -energy
                 is then higher).

    best[i][c] = best[i-1][c]                              (skip item i)
              or best[i-1][c - cost_i] + (value_i, -cost_i)  (take item i)

Tie-break rule (documented and tested)
    1. maximum usefulness
    2. then the lower total energy cost
    3. then the selection whose sorted ID tuple comes first alphabetically.
    Rule 3 is handled in the traceback: items are placed in the table in
    reverse alphabetical order, so the traceback decides about the
    alphabetically FIRST gadget first, and takes it whenever taking it still
    reaches the optimum.

Complexity: O(n * C) time and space (n items, capacity C) - 6 x 9 cells here.
My DAA Experiment 6 used Branch and Bound; the tests check that both (and a
brute-force search) reach the same best usefulness.
"""

from dataclasses import dataclass

from core import config
from core.gadgets import GADGETS, GADGET_ORDER


@dataclass
class LoadoutResult:
    """The recommended kit."""
    selected_ids: tuple
    total_cost: int
    total_usefulness: int


def add_pair(pair, usefulness, cost):
    """(usefulness, -energy) + one item."""
    return (pair[0] + usefulness, pair[1] - cost)


def recommend_loadout(items, capacity: int) -> LoadoutResult:
    """Best kit from items = [(gadget_id, energy_cost, usefulness), ...].

    Empty item lists, capacity 0 and items that never fit simply give an
    empty selection with zeros.
    """
    capacity = max(0, int(capacity))
    ids = [item[0] for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError("Each gadget may appear only once.")
    for gadget_id, cost, usefulness in items:
        if cost <= 0 or usefulness < 0:
            raise ValueError(f"Invalid numbers for {gadget_id}.")

    # Reverse alphabetical order inside the table -> alphabetical traceback.
    ordered = sorted(items, key=lambda item: item[0], reverse=True)
    n = len(ordered)

    # Row 0 = no items at all: (0 usefulness, 0 energy) for every capacity.
    best = [[(0, 0)] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        gadget_id, cost, usefulness = ordered[i - 1]
        for c in range(capacity + 1):
            skip = best[i - 1][c]
            if cost <= c:
                take = add_pair(best[i - 1][c - cost], usefulness, cost)
                best[i][c] = max(skip, take)
            else:
                best[i][c] = skip

    # Traceback: walk from the last row to the first, deciding each item.
    selected = []
    c = capacity
    for i in range(n, 0, -1):
        gadget_id, cost, usefulness = ordered[i - 1]
        if cost <= c and add_pair(best[i - 1][c - cost], usefulness, cost) == best[i][c]:
            selected.append(gadget_id)      # taking it still reaches the optimum
            c = c - cost

    total_usefulness, negative_cost = best[n][capacity]
    return LoadoutResult(tuple(sorted(selected)), -negative_cost, total_usefulness)


def mission_items(mission) -> list:
    """The catalogue as (id, energy cost, usefulness for this mission) triples."""
    return [(g, GADGETS[g].energy_cost, mission.usefulness[g]) for g in GADGET_ORDER]


def recommend_for_mission(mission, capacity: int = config.KIT_CAPACITY) -> LoadoutResult:
    """Suggested Kit for one mission."""
    return recommend_loadout(mission_items(mission), capacity)


def build_usefulness_table(items, capacity: int) -> list:
    """Plain usefulness-only DP table (rows in the given item order).

    Used by the docs/viva notes to print a small table excerpt; the game
    itself uses recommend_loadout().
    """
    n = len(items)
    table = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        _, cost, usefulness = items[i - 1]
        for c in range(capacity + 1):
            table[i][c] = table[i - 1][c]
            if cost <= c:
                table[i][c] = max(table[i][c], table[i - 1][c - cost] + usefulness)
    return table
