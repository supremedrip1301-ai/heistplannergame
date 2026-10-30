"""Three plain test grids (no drones, no keycards) for the Dijkstra tests.

These were the first three missions of the game (The Archive, The Gallery and
The Relay). They were removed from the game on 30 Oct 2026, but their
verified minimum costs are still a very good test of core/pathfinding.py and
core/state_planner.py, so they are kept here as test data.

'G' is a gate tile (cost 1) that a test can block to force a detour.
"""

from core.missions import Mission

FLOOR_COSTS = {".": 1, "S": 1, "O": 1, "E": 1, "G": 1, "~": 4}
BOOT_COSTS = dict(FLOOR_COSTS, **{"~": 2})       # static fields at half cost

ARCHIVE_MAP = [
    "############",
    "#S...#.....#",
    "#.##.#.###.#",
    "#.#..#...#.#",
    "#.#.####.#.#",
    "#...#..O.#.#",
    "###.#.####.#",
    "#E.........#",
    "############",
]

GALLERY_MAP = [
    "############",
    "#S..~~~~..O#",
    "#.##~~~~##.#",
    "#.##....##.#",
    "#.########.#",
    "#..........#",
    "#.########.#",
    "#E.........#",
    "############",
]

RELAY_MAP = [
    "############",
    "#S...#.....#",
    "#.##.#.###.#",
    "#.##...#O..#",
    "#.######.#.#",
    "#....G...#.#",
    "#.########.#",
    "#E.......#.#",
    "#.########.#",
    "#..........#",
    "############",
]

CLASSIC_GRIDS = {"archive": ARCHIVE_MAP, "gallery": GALLERY_MAP, "relay": RELAY_MAP}


def find(grid, char):
    for r, line in enumerate(grid):
        if char in line:
            return (r, line.index(char))
    return None


def simple_mission(grid=ARCHIVE_MAP, mission_id="vault"):
    """A Mission object with no drones (for engine tests of the basic rules).

    mission_id defaults to a real mission ID so a finished run can be saved
    into a test database (the foreign key needs an existing mission).
    The relay gate 'G' is turned into floor because the game has no gates.
    """
    return Mission(mission_id, "Test grid", "Easy", "test", "hook", "goal", "condition",
                   "extraction", "test objective", [line.replace("G", ".") for line in grid])


class ClassicMap:
    """Grid plus its special positions (what the old Mission objects offered)."""

    def __init__(self, mission_id, grid):
        self.mission_id = mission_id
        self.grid = grid
        self.start = find(grid, "S")
        self.objective = find(grid, "O")
        self.exit = find(grid, "E")
        self.gate = find(grid, "G")


CLASSIC = {key: ClassicMap(key, grid) for key, grid in CLASSIC_GRIDS.items()}
