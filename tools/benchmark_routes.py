"""Optional benchmark: heap Dijkstra (game) vs matrix Dijkstra (my DAA Exp 4).

    python tools\\benchmark_routes.py

Times both versions on growing random grids with time.perf_counter(), in the
same style as my Quick Sort timing experiment (DAA Exp 1). Draws a line graph
only if Matplotlib is installed; otherwise it just prints the table.
This script is never imported by the game.
"""

import random
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from core.missions import build_tile_costs  # noqa: E402
from core.pathfinding import find_shortest_path  # noqa: E402
from tests.reference_algorithms import dijkstra_matrix, grid_to_matrix  # noqa: E402

SIZES = [10, 15, 20, 25, 30, 35]
REPEATS = 3


def random_grid(size: int, rng: random.Random) -> list:
    """Square map with ~15% static fields and ~15% walls (start/goal corners kept open)."""
    rows = []
    for r in range(size):
        line = []
        for c in range(size):
            roll = rng.random()
            if roll < 0.15 and (r, c) not in ((0, 0), (size - 1, size - 1)):
                line.append("#")
            elif roll < 0.30:
                line.append("~")
            else:
                line.append(".")
        rows.append("".join(line))
    return rows


def best_time(function) -> float:
    best = float("inf")
    for _ in range(REPEATS):
        start = time.perf_counter()
        function()
        best = min(best, time.perf_counter() - start)
    return best * 1000


def main() -> None:
    rng = random.Random(2026)
    costs = build_tile_costs()
    results = []
    print(f"{'Grid':>7} {'Tiles':>6} {'Heap (ms)':>10} {'Matrix (ms)':>12} {'Same cost':>10}")
    for size in SIZES:
        grid = random_grid(size, rng)
        start, goal = (0, 0), (size - 1, size - 1)
        matrix, index_of = grid_to_matrix(grid, costs)
        heap_ms = best_time(lambda: find_shortest_path(grid, start, goal, costs))
        matrix_ms = best_time(lambda: dijkstra_matrix(matrix, index_of[start]))
        heap_cost = find_shortest_path(grid, start, goal, costs).cost
        matrix_cost = dijkstra_matrix(matrix, index_of[start])[index_of[goal]]
        same = (heap_cost == matrix_cost) or (heap_cost is None and matrix_cost == float("inf"))
        results.append((len(index_of), heap_ms, matrix_ms))
        print(f"{size:>3}x{size:<3} {len(index_of):>6} {heap_ms:>10.2f} {matrix_ms:>12.2f} "
              f"{str(same):>10}")
    print("(matrix time excludes building the matrix; the heap version needs no matrix)")

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib is not installed - table only.")
        return
    tiles = [r[0] for r in results]
    plt.plot(tiles, [r[1] for r in results], marker="o", label="Heap Dijkstra  O((V+E) log V)")
    plt.plot(tiles, [r[2] for r in results], marker="s", label="Matrix Dijkstra  O(V^2)")
    plt.xlabel("Walkable tiles (V)")
    plt.ylabel("Time (ms)")
    plt.title("Route planning: heap vs matrix Dijkstra")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


if __name__ == "__main__":
    main()
