"""Route planning for the game: Dijkstra's shortest-path algorithm with a heap.

How the map becomes a graph
---------------------------
* Every walkable tile is a vertex, written as a (row, col) tuple.
* From a tile you may step up, right, down or left (no diagonals) into a
  neighbouring walkable tile. Each such step is a directed edge.
* Walls ('#') and sealed tiles (the relay gate after the alert) are not
  vertices at all, so no route can ever pass through them.

Movement-cost model (used everywhere in the game)
-------------------------------------------------
The cost of a step is the cost of the tile being ENTERED. The start tile's
own cost is never charged. All costs are positive integers, which is exactly
the condition Dijkstra needs to be correct.

Complexity
----------
With a binary heap (heapq) Dijkstra runs in O((V + E) log V). On a tile map
every vertex has at most 4 edges, so E <= 4V and this is O(V log V).
My DAA Experiment 4 version used an adjacency matrix and a linear scan for
the closest unvisited vertex, which is O(V^2) - fine for 6 cities, but
wasteful for a sparse map where most matrix cells would be 0.
"""

import heapq
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

WALL = "#"

# Fixed neighbour order: up, right, down, left. A fixed order (together with
# (cost, row, col) heap entries) makes the chosen path deterministic.
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))
DIRECTION_NAMES = {(-1, 0): "North", (0, 1): "East", (1, 0): "South", (0, -1): "West"}


@dataclass
class RouteResult:
    """Answer returned by find_shortest_path().

    path  - list of (row, col) tiles including start and goal ([] if not found)
    cost  - total effort of the path (None if not found)
    found - True when a route exists
    """
    path: list = field(default_factory=list)
    cost: "int | None" = None
    found: bool = False

    @property
    def steps(self) -> int:
        """Number of moves along the path (tiles minus one)."""
        if not self.found:
            return 0
        return len(self.path) - 1


def is_inside(grid, pos) -> bool:
    """True if pos = (row, col) lies inside the grid."""
    row, col = pos
    return 0 <= row < len(grid) and 0 <= col < len(grid[row])


def is_walkable(grid, pos, tile_costs, blocked=frozenset()) -> bool:
    """True if the tile can be entered: inside the map, has a cost, not sealed."""
    if not is_inside(grid, pos):
        return False
    if pos in blocked:
        return False
    tile = grid[pos[0]][pos[1]]
    return tile in tile_costs


def neighbours(grid, pos, tile_costs, blocked=frozenset()):
    """Return the walkable four-direction neighbours of pos, in fixed order."""
    result = []
    for d_row, d_col in DIRECTIONS:
        nxt = (pos[0] + d_row, pos[1] + d_col)
        if is_walkable(grid, nxt, tile_costs, blocked):
            result.append(nxt)
    return result


def step_direction(current, nxt) -> str:
    """Friendly compass name for the step from current to nxt ('East', ...)."""
    delta = (nxt[0] - current[0], nxt[1] - current[1])
    return DIRECTION_NAMES.get(delta, "?")


def find_shortest_path(grid, start, goal, tile_costs, blocked=frozenset()) -> RouteResult:
    """Find the minimum-cost route from start to goal with Dijkstra's algorithm.

    grid       - list of equal-length strings (the mission map)
    start/goal - (row, col) tuples
    tile_costs - dict: tile character -> cost of entering it. A character
                 that is missing from the dict (for example '#') is a wall.
    blocked    - set of (row, col) tiles that are sealed right now

    Returns RouteResult(path, cost, found). Never raises for "no route":
    an unreachable or invalid goal gives RouteResult([], None, False).
    """
    # 1. Validate the input positions instead of crashing on bad data.
    for name, pos in (("start", start), ("goal", goal)):
        if not is_walkable(grid, pos, tile_costs, blocked):
            logger.warning("find_shortest_path: %s %s is outside the map or not walkable",
                           name, pos)
            return RouteResult([], None, False)

    if start == goal:
        return RouteResult([start], 0, True)

    # 2. dist[tile] = cheapest known cost from start; previous[tile] = the tile
    #    we came from on that cheapest route (used to rebuild the path).
    dist = {start: 0}
    previous = {}
    visited = set()

    # The heap holds (cost, row, col). heapq always pops the smallest tuple,
    # so ties on cost are broken by row, then column - deterministic.
    heap = [(0, start[0], start[1])]

    while heap:
        d, row, col = heapq.heappop(heap)
        node = (row, col)

        # Stale entry: we already found a cheaper way to this tile earlier.
        if d > dist.get(node, d):
            continue
        if node in visited:
            continue
        visited.add(node)

        # Early stop: the first time the goal is popped its cost is final.
        if node == goal:
            break

        for nxt in neighbours(grid, node, tile_costs, blocked):
            if nxt in visited:
                continue
            # Entered-tile cost model: pay the cost of the tile we step onto.
            step_cost = tile_costs[grid[nxt[0]][nxt[1]]]
            new_cost = d + step_cost
            # Relaxation: keep the new route only if it is strictly cheaper.
            if new_cost < dist.get(nxt, float("inf")):
                dist[nxt] = new_cost
                previous[nxt] = node
                heapq.heappush(heap, (new_cost, nxt[0], nxt[1]))

    if goal not in visited:
        return RouteResult([], None, False)

    # 3. Rebuild the path by walking backwards from the goal to the start.
    path = [goal]
    while path[-1] != start:
        path.append(previous[path[-1]])
    path.reverse()
    return RouteResult(path, dist[goal], True)


def path_cost(grid, path, tile_costs) -> int:
    """Total effort of an explicit path under the entered-tile cost model."""
    total = 0
    for pos in path[1:]:
        total = total + tile_costs[grid[pos[0]][pos[1]]]
    return total
