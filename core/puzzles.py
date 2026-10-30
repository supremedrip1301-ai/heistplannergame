"""Terminal puzzle: the Power Relay. Dijkstra is the judge.

Power Relay
    A square grid of numbered cells (6 x 6 in the Lab, 7 x 7 in the Penthouse).
    Draw a path of touching cells from IN (top-left) to OUT (bottom-right).
    The relay load is the sum of every cell on the path. Only the minimum
    possible load opens the terminal; that minimum is computed with
    find_shortest_path() from core/pathfinding.py.

The generator throws away grids where the obvious greedy idea (always step
right or down to the cheaper next cell) already gives the answer. So the
player really has to plan - exactly the reason DAA teaches Dijkstra instead
of a greedy walk for shortest paths.
"""

import random

from core.pathfinding import find_shortest_path

POWER = "power"
MAX_TRIES = 200                      # generator attempts before accepting any puzzle
DEFAULT_SIZE = 6

DIGIT_COSTS = {str(d): d for d in range(1, 10)}


class PowerRelayPuzzle:
    kind = POWER
    title = "Power Relay"

    def __init__(self, seed, size: int = DEFAULT_SIZE):
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


def make_puzzle(kind: str, seed, size: int = DEFAULT_SIZE):
    if kind == POWER:
        return PowerRelayPuzzle(seed, size)
    raise ValueError(f"Unknown puzzle kind: {kind}")
