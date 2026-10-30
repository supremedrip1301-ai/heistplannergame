"""The 0/1 Knapsack problem solved with dynamic programming.

The game uses it as the judge of the Cargo Lock terminal puzzle
(core/puzzles.py): the player must load the lift with the richest set of
crates, and this DP computes what "richest" is.

Mapping to the textbook problem
    item      = crate (each one can be taken at most once -> "0/1")
    weight    = mass of the crate (kg)
    value     = credits the crate is worth
    capacity  = the lift limit (kg)

DP table
    best[i][c] = the best result using only the first i items with at most c
                 mass. Each cell stores a pair (worth, -mass), and pairs are
                 compared like tuples: higher worth wins, and for equal worth
                 the LOWER mass wins (because -mass is then higher).

    best[i][c] = best[i-1][c]                              (skip item i)
              or best[i-1][c - mass_i] + (worth_i, -mass_i)  (take item i)

Tie-break rule (documented and tested)
    1. maximum worth
    2. then the lower total mass
    3. then the selection whose sorted ID tuple comes first alphabetically.
    Rule 3 is handled in the traceback: items are placed in the table in
    reverse alphabetical order, so the traceback decides about the
    alphabetically FIRST item first, and takes it whenever taking it still
    reaches the optimum.

Complexity: O(n * C) time and space (n items, capacity C).
My DAA Experiment 6 used Branch and Bound; the tests check that both (and a
brute-force search) reach the same best worth.
"""

from dataclasses import dataclass


@dataclass
class LoadoutResult:
    """The best selection of items."""
    selected_ids: tuple
    total_cost: int            # total weight (mass)
    total_usefulness: int      # total value (credits)


def add_pair(pair, worth, mass):
    """(worth, -mass) + one item."""
    return (pair[0] + worth, pair[1] - mass)


def recommend_loadout(items, capacity: int) -> LoadoutResult:
    """Best selection from items = [(item_id, weight, value), ...].

    Empty item lists, capacity 0 and items that never fit simply give an
    empty selection with zeros.
    """
    capacity = max(0, int(capacity))
    ids = [item[0] for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError("Each item may appear only once.")
    for item_id, weight, value in items:
        if weight <= 0 or value < 0:
            raise ValueError(f"Invalid numbers for {item_id}.")

    # Reverse alphabetical order inside the table -> alphabetical traceback.
    ordered = sorted(items, key=lambda item: item[0], reverse=True)
    n = len(ordered)

    # Row 0 = no items at all: (0 value, 0 weight) for every capacity.
    best = [[(0, 0)] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        item_id, weight, value = ordered[i - 1]
        for c in range(capacity + 1):
            skip = best[i - 1][c]
            if weight <= c:
                take = add_pair(best[i - 1][c - weight], value, weight)
                best[i][c] = max(skip, take)
            else:
                best[i][c] = skip

    # Traceback: walk from the last row to the first, deciding each item.
    selected = []
    c = capacity
    for i in range(n, 0, -1):
        item_id, weight, value = ordered[i - 1]
        if weight <= c and add_pair(best[i - 1][c - weight], value, weight) == best[i][c]:
            selected.append(item_id)        # taking it still reaches the optimum
            c = c - weight

    total_value, negative_weight = best[n][capacity]
    return LoadoutResult(tuple(sorted(selected)), -negative_weight, total_value)


def build_value_table(items, capacity: int) -> list:
    """Plain value-only DP table (rows in the given item order).

    Used by the README and viva notes to print a small table excerpt.
    """
    n = len(items)
    table = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        _, weight, value = items[i - 1]
        for c in range(capacity + 1):
            table[i][c] = table[i - 1][c]
            if weight <= c:
                table[i][c] = max(table[i][c], table[i - 1][c - weight] + value)
    return table
