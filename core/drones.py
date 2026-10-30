"""Patrol drones: deterministic sentries that move one tile per player turn.

Because a drone always follows the same patrol, its position at turn t is
known in advance: position(t) = cycle[t % len(cycle)]. That is what lets the
route planner (core/state_planner.py) plan routes that dodge every drone.

Vision
    A drone sees its own tile plus up to `sight` tiles straight ahead in the
    direction it is about to move. Walls and closed doors block the view.
Detection (checked after every player turn)
    The player is caught if they stand in any drone's vision, or if the player
    and a drone swapped tiles during the turn (they walked through each other).
"""

from math import gcd

SIGHT_BLOCKERS = ("#", "D")       # wall, locked door
DEFAULT_SIGHT = 2


def straight_line(a, b) -> list:
    """Tiles from a to b (both included). a and b must share a row or a column."""
    if a[0] != b[0] and a[1] != b[1]:
        raise ValueError(f"Waypoints {a} and {b} are not in a straight line.")
    d_row = (b[0] > a[0]) - (b[0] < a[0])
    d_col = (b[1] > a[1]) - (b[1] < a[1])
    tiles = [a]
    while tiles[-1] != b:
        last = tiles[-1]
        tiles.append((last[0] + d_row, last[1] + d_col))
    return tiles


class Drone:
    """One patrol drone.

    waypoints - corner tiles of the patrol, joined by straight lines
    mode      - "pingpong" (walk to the end, turn round, walk back) or
                "loop" (after the last waypoint, return to the first one)
    """

    def __init__(self, name: str, waypoints, mode: str = "pingpong",
                 sight: int = DEFAULT_SIGHT):
        self.name = name
        self.mode = mode
        self.sight = sight
        path = [waypoints[0]]
        for a, b in zip(waypoints, waypoints[1:]):
            path.extend(straight_line(a, b)[1:])
        if mode == "loop":
            closing = straight_line(waypoints[-1], waypoints[0])[1:]
            self.cycle = path + closing[:-1]          # do not repeat the first tile
        elif mode == "pingpong":
            self.cycle = path + path[-2:0:-1]         # back again, without the two ends
        else:
            raise ValueError("mode must be 'pingpong' or 'loop'")
        if len(self.cycle) < 2:
            raise ValueError("A patrol needs at least two tiles.")

    @property
    def period(self) -> int:
        return len(self.cycle)

    def position(self, t: int):
        return self.cycle[t % self.period]

    def facing(self, t: int):
        """(d_row, d_col) of the step the drone takes next."""
        here = self.position(t)
        nxt = self.position(t + 1)
        return (nxt[0] - here[0], nxt[1] - here[1])

    def vision(self, t: int, grid) -> set:
        """Tiles this drone can see at turn t."""
        here = self.position(t)
        d_row, d_col = self.facing(t)
        seen = {here}
        row, col = here
        for _ in range(self.sight):
            row, col = row + d_row, col + d_col
            if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
                break
            if grid[row][col] in SIGHT_BLOCKERS:
                break
            seen.add((row, col))
        return seen

    def __repr__(self):
        return f"Drone({self.name!r}, period={self.period})"


def drone_clock_period(drones) -> int:
    """Smallest number of turns after which every drone is back at its start.

    This is the LCM of all patrol lengths (1 when there are no drones), so
    the planner only needs to remember the drone clock modulo this number.
    """
    period = 1
    for drone in drones:
        period = period * drone.period // gcd(period, drone.period)
    return period


def watched_tiles(drones, t: int, grid) -> set:
    """Every tile seen by at least one drone at turn t."""
    tiles = set()
    for drone in drones:
        tiles |= drone.vision(t, grid)
    return tiles


def is_detected(drones, grid, old_pos, new_pos, old_t: int, new_t: int) -> bool:
    """True if the player is spotted after moving old_pos -> new_pos.

    old_t / new_t are the drone clock before and after the turn (they are
    equal while a Signal Decoy keeps the drones frozen).
    """
    for drone in drones:
        if new_pos in drone.vision(new_t, grid):
            return True
        # Walking "through" a drone: we swapped places during this turn.
        if (old_pos != new_pos and drone.position(new_t) == old_pos
                and drone.position(old_t) == new_pos):
            return True
    return False
