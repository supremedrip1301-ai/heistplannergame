"""Terminal puzzles. The project's own algorithms are the judges.

Power Relay (judged by Dijkstra)
    A 6 x 6 grid of numbered cells. Draw a path of touching cells from IN
    (top-left) to OUT (bottom-right). The relay load is the sum of every cell
    on the path. Only the minimum possible load opens the terminal; that
    minimum is computed with find_shortest_path() from core/pathfinding.py.

Cargo Lock (judged by 0/1 Knapsack DP)
    Seven crates, each with a mass and a credit worth, and a lift limit.
    Pick crates so the total mass fits and the total worth is as high as
    possible; the maximum is computed with recommend_loadout() from
    core/loadout_optimizer.py.

Both generators throw away puzzles where the obvious greedy idea already
gives the answer (always step to the cheapest next cell / always take the
best credits-per-kg crate). So the player really has to plan - exactly the
reason DAA teaches Dijkstra and DP instead of greedy for these problems.
"""

import random

from core.loadout_optimizer import recommend_loadout
from core.pathfinding import find_shortest_path

POWER = "power"
CARGO = "cargo"
MAX_TRIES = 200                      # generator attempts before accepting any puzzle

DIGIT_COSTS = {str(d): d for d in range(1, 10)}
CRATE_NAMES = "ABCDEFG"


class PowerRelayPuzzle:
    kind = POWER
    title = "Power Relay"

    def __init__(self, seed, size: int = 6):
        rng = random.Random(seed)
        self.size = size
        self.start = (0, 0)
        self.goal = (size - 1, size - 1)
        for _ in range(MAX_TRIES):
            self.grid = ["".join(str(rng.randint(1, 9)) for _ in range(size))
                         for _ in range(size)]
            route = find_shortest_path(self.grid, self.start, self.goal, DIGIT_COSTS)
            # Dijkstra does not charge the start cell, the puzzle does.
            self.best = route.cost + self.cell(self.start)
            self.solution = route.path
            if self.greedy_load() > self.best:
                break                     # greedy is wrong -> a real puzzle

    def cell(self, pos) -> int:
        return int(self.grid[pos[0]][pos[1]])

    def greedy_load(self) -> int:
        """Load of the 'always step right/down to the cheaper cell' path."""
        row, col = self.start
        total = self.cell(self.start)
        while (row, col) != self.goal:
            options = []
            if col + 1 < self.size:
                options.append((self.cell((row, col + 1)), (row, col + 1)))
            if row + 1 < self.size:
                options.append((self.cell((row + 1, col)), (row + 1, col)))
            value, (row, col) = min(options)
            total = total + value
        return total

    def load(self, cells) -> int:
        return sum(self.cell(pos) for pos in cells)

    def check(self, cells) -> tuple:
        """(solved, message) for the cells the player selected, in order."""
        if not cells or cells[0] != self.start or cells[-1] != self.goal:
            return False, "The path must run from IN to OUT."
        if len(set(cells)) != len(cells):
            return False, "A path cannot use the same cell twice."
        for a, b in zip(cells, cells[1:]):
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
                return False, "Cells must touch side by side."
        total = self.load(cells)
        if total == self.best:
            return True, f"Relay stable at load {total}. Lasers offline."
        return False, f"Load {total} overloads the relay. A lighter path exists."

    def hint(self) -> str:
        return f"Clue Lens: the lightest path has load {self.best}."


class CargoLockPuzzle:
    kind = CARGO
    title = "Cargo Lock"

    def __init__(self, seed, count: int = 7):
        rng = random.Random(seed)
        for _ in range(MAX_TRIES):
            self.crates = []
            for i in range(count):
                self.crates.append((CRATE_NAMES[i], rng.randint(2, 9), rng.randint(3, 20)))
            total_mass = sum(c[1] for c in self.crates)
            self.limit = max(5, total_mass // 2)
            result = recommend_loadout(self.crates, self.limit)
            self.best = result.total_usefulness
            self.solution = result.selected_ids
            if self.greedy_worth() < self.best:
                break                     # greedy is wrong -> a real puzzle

    def greedy_worth(self) -> int:
        """Worth of 'take the best credits-per-kg crate that still fits'."""
        mass = worth = 0
        for name, m, w in sorted(self.crates, key=lambda c: c[2] / c[1], reverse=True):
            if mass + m <= self.limit:
                mass, worth = mass + m, worth + w
        return worth

    def totals(self, names) -> tuple:
        mass = sum(c[1] for c in self.crates if c[0] in names)
        worth = sum(c[2] for c in self.crates if c[0] in names)
        return mass, worth

    def check(self, names) -> tuple:
        mass, worth = self.totals(names)
        if mass > self.limit:
            return False, f"{mass} kg is over the {self.limit} kg lift limit."
        if worth == self.best:
            return True, f"Cargo balanced: {worth} credits. Lasers offline."
        return False, f"{worth} credits is not enough. A richer load fits the lift."

    def hint(self) -> str:
        return f"Clue Lens: the richest load is worth {self.best} credits."


def make_puzzle(kind: str, seed):
    if kind == POWER:
        return PowerRelayPuzzle(seed)
    if kind == CARGO:
        return CargoLockPuzzle(seed)
    raise ValueError(f"Unknown puzzle kind: {kind}")
