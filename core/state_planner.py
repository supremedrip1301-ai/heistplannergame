"""Route planning for the hard missions: Dijkstra on a STATE graph.

In the first three missions a vertex is simply a tile. In the new missions
that is not enough, because whether a move is safe depends on more than
where you stand:

    * WHEN you move  - drones are somewhere else at every turn
    * WHAT you carry - a locked door opens only if you hold the keycard
    * decoy          - while a Signal Decoy is active the drones are frozen

So a vertex here is a state:

    (row, col, drone_clock, has_key, freeze_left)

drone_clock is the turn number modulo the drone period (the LCM of all
patrol lengths; core/drones.py), because after that many turns every drone
is back where it started and the situation repeats exactly.

Edges (one player turn each)
    * move up / right / down / left  - cost = cost of the tile entered
    * wait on the spot               - cost = WAIT_COST
    An edge is left out if it walks into a wall, a sealed tile, a locked door
    without the keycard, or if any drone would see the player afterwards.

All edge costs are positive, so Dijkstra is still correct; it just works on
a bigger graph. With 132 tiles x 12 clock values x 2 x 4 there are at most
about 12,700 states, which takes a few milliseconds.
Time complexity: O((S + T) log S) for S states and T transitions (T <= 5S).
"""

import heapq

from core.drones import drone_clock_period, is_detected
from core.pathfinding import DIRECTIONS, RouteResult

KEYCARD = "k"
DOOR = "D"
WAIT_COST = 1


class PlanContext:
    """Everything about the map that does not change during one search."""

    def __init__(self, grid, tile_costs, drones=(), blocked=frozenset()):
        self.grid = grid
        self.tile_costs = tile_costs
        self.drones = list(drones)
        self.blocked = frozenset(blocked)
        self.period = drone_clock_period(self.drones)

    def can_enter(self, pos, has_key: bool) -> bool:
        row, col = pos
        if not (0 <= row < len(self.grid) and 0 <= col < len(self.grid[0])):
            return False
        if pos in self.blocked:
            return False
        tile = self.grid[row][col]
        if tile not in self.tile_costs:
            return False                     # wall
        if tile == DOOR and not has_key:
            return False                     # locked door
        return True


def successors(ctx: PlanContext, state):
    """All (next_state, cost) pairs reachable in one turn from state."""
    row, col, clock, has_key, freeze = state
    # The drone clock only ticks when no decoy is freezing the drones.
    if freeze > 0:
        next_clock, next_freeze = clock, freeze - 1
    else:
        next_clock, next_freeze = (clock + 1) % ctx.period, 0

    options = []
    for d_row, d_col in DIRECTIONS:
        options.append((row + d_row, col + d_col))
    if ctx.drones:
        options.append((row, col))           # waiting only matters when drones move

    result = []
    for new_pos in options:
        if new_pos == (row, col):
            cost = WAIT_COST
        else:
            if not ctx.can_enter(new_pos, has_key):
                continue
            cost = ctx.tile_costs[ctx.grid[new_pos[0]][new_pos[1]]]
        if ctx.drones and is_detected(ctx.drones, ctx.grid, (row, col), new_pos,
                                      clock, next_clock):
            continue
        new_key = has_key or ctx.grid[new_pos[0]][new_pos[1]] == KEYCARD
        result.append(((new_pos[0], new_pos[1], next_clock, new_key, next_freeze), cost))
    return result


def plan_state_route(ctx: PlanContext, start, goal, clock: int = 0,
                     has_key: bool = False, freeze: int = 0) -> RouteResult:
    """Cheapest safe route from start to goal, starting at the given drone clock.

    Returns RouteResult(path, cost, found). The path lists the tile occupied
    after every turn; a tile repeated twice in a row means "wait".
    """
    if not ctx.can_enter(goal, True) or start is None:
        return RouteResult([], None, False)
    start_state = (start[0], start[1], clock % ctx.period, has_key, freeze)
    if start == goal:
        return RouteResult([start], 0, True)

    dist = {start_state: 0}
    previous = {}
    visited = set()
    heap = [(0, start_state)]
    end_state = None

    while heap:
        d, state = heapq.heappop(heap)
        if state in visited:
            continue                         # stale entry
        visited.add(state)
        if (state[0], state[1]) == goal:
            end_state = state                # first time popped = cheapest
            break
        for nxt, cost in successors(ctx, state):
            if nxt in visited:
                continue
            new_cost = d + cost
            if new_cost < dist.get(nxt, float("inf")):
                dist[nxt] = new_cost
                previous[nxt] = state
                heapq.heappush(heap, (new_cost, nxt))

    if end_state is None:
        return RouteResult([], None, False)

    states = [end_state]
    while states[-1] != start_state:
        states.append(previous[states[-1]])
    states.reverse()
    path = [(s[0], s[1]) for s in states]
    return RouteResult(path, dist[end_state], True)


def count_waits(path) -> int:
    """How many turns of a path are spent waiting."""
    waits = 0
    for a, b in zip(path, path[1:]):
        if a == b:
            waits = waits + 1
    return waits
