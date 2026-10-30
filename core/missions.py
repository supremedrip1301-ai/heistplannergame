"""The three fixed missions: maps, briefings and gadget usefulness.

All three maps were verified with a script on 27 Oct 2026 (every walkable
tile reachable, costs as listed in MASTER_PROMPT Section 8) and the unit
tests in tests/test_missions.py and tests/test_pathfinding.py confirm them.

Positions are (row, col): rows counted from the top, columns from the left,
both starting at 0.

Legend
  #  wall (not walkable)
  .  floor (cost 1)
  ~  static field (cost 4, or 2 with Mobility Boots)
  S  start (floor)      O  objective (floor)      E  extraction (floor)
  G  relay gate (floor, cost 1 while open; impassable once sealed)
  k  keycard (floor; stepping on it picks the keycard up)
  D  locked door (impassable until you hold the keycard, then cost 1)
  T  terminal (floor; hack it to switch the lasers off)
  L  laser barrier (impassable until the terminal is hacked, then cost 1)
"""

from core import config
from core.drones import Drone
from core.gadgets import BOOTS

WALL = "#"
FLOOR = "."
STATIC_FIELD = "~"
START = "S"
OBJECTIVE = "O"
EXTRACTION = "E"
GATE = "G"
KEYCARD = "k"
DOOR = "D"
TERMINAL = "T"
LASER = "L"

TILE_NAMES = {
    WALL: "Wall",
    FLOOR: "Floor",
    STATIC_FIELD: "Static field",
    START: "Start",
    OBJECTIVE: "Objective",
    EXTRACTION: "Extraction",
    GATE: "Relay gate",
    KEYCARD: "Keycard",
    DOOR: "Locked door",
    TERMINAL: "Terminal",
    LASER: "Laser barrier",
}


class Mission:
    """One mission: its map, story text and how useful each gadget is."""

    def __init__(self, mission_id: str, name: str, difficulty: str, mission_type: str,
                 hook: str, goal: str, condition: str, extraction: str,
                 objective_name: str, grid: list, usefulness: dict,
                 drones=(), puzzle_kind=None, risk_bonus: int = 0):
        self.mission_id = mission_id
        self.name = name
        self.difficulty = difficulty
        self.mission_type = mission_type
        self.hook = hook                   # one line on the mission card
        self.goal = goal                   # briefing: what to do
        self.condition = condition         # briefing: special map condition
        self.extraction = extraction       # briefing: how extraction works
        self.objective_name = objective_name
        self.grid = tuple(grid)            # read-only map
        self.usefulness = usefulness       # gadget_id -> usefulness (the "value")
        self.start = self.find_tile(START)
        self.objective = self.find_tile(OBJECTIVE)
        self.exit = self.find_tile(EXTRACTION)
        self.gate = self.find_tile(GATE)   # None when the map has no gate
        self.keycard = self.find_tile(KEYCARD)
        self.terminal = self.find_tile(TERMINAL)
        self.drones = list(drones)         # core.drones.Drone objects
        self.puzzle_kind = puzzle_kind     # "power" / "cargo" / None (terminal puzzle)
        self.risk_bonus = risk_bonus       # extra score for the long, dangerous missions

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0])

    @property
    def has_alert(self) -> bool:
        """Only a mission with a relay gate has the alert event."""
        return self.gate is not None

    @property
    def has_keycard(self) -> bool:
        return self.keycard is not None

    @property
    def has_terminal(self) -> bool:
        return self.terminal is not None

    def find_all(self, char: str) -> list:
        """Every (row, col) with this tile character, top to bottom."""
        return [(r, c) for r, line in enumerate(self.grid)
                for c, ch in enumerate(line) if ch == char]

    def laser_tiles(self) -> list:
        return self.find_all(LASER)

    def door_tiles(self) -> list:
        return self.find_all(DOOR)

    def find_tile(self, char: str):
        """Return the (row, col) of the first tile with this character, or None."""
        for row, line in enumerate(self.grid):
            col = line.find(char)
            if col != -1:
                return (row, col)
        return None

    def tile_at(self, pos) -> str:
        return self.grid[pos[0]][pos[1]]

    def tile_types(self) -> list:
        """Friendly names of the special tile types that appear on this map."""
        found = []
        for char in (STATIC_FIELD, GATE, KEYCARD, DOOR, TERMINAL, LASER):
            if any(char in line for line in self.grid):
                found.append(TILE_NAMES[char])
        if self.drones:
            found.append(f"Patrol drones ({len(self.drones)})")
        return found

    def __repr__(self):
        return f"Mission({self.mission_id!r})"


def build_tile_costs(kit_ids=()) -> dict:
    """Cost of entering each walkable tile type for a run with this kit.

    Walls are left out on purpose: a tile type without a cost is not walkable.
    Mobility Boots lower the static-field cost from 4 to 2.
    """
    static_cost = config.STATIC_FIELD_COST
    if BOOTS in kit_ids:
        static_cost = config.STATIC_FIELD_COST_WITH_BOOTS
    return {
        FLOOR: config.FLOOR_COST,
        START: config.FLOOR_COST,
        OBJECTIVE: config.FLOOR_COST,
        EXTRACTION: config.FLOOR_COST,
        GATE: config.FLOOR_COST,
        KEYCARD: config.FLOOR_COST,
        DOOR: config.FLOOR_COST,         # only enterable with the keycard
        TERMINAL: config.FLOOR_COST,
        LASER: config.FLOOR_COST,        # only enterable once the lasers are off
        STATIC_FIELD: static_cost,
    }


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

MISSIONS = {
    "archive": Mission(
        "archive", "The Archive", "Easy", "information",
        hook="Slip into a quiet archive and lift a memory token.",
        goal="Retrieve the memory token from the archive core, then leave.",
        condition="Two corridors lead to the core. Pick the shorter one.",
        extraction="Return to the extraction hatch in the lower-left corner.",
        objective_name="memory token",
        grid=ARCHIVE_MAP,
        usefulness={"scanner": 6, "decoy": 3, "boots": 2,
                    "repair": 2, "lens": 7, "shield": 3},
    ),
    "gallery": Mission(
        "gallery", "The Gallery", "Medium", "mobility",
        hook="Cross a hall of static fields to reach the light sculpture.",
        goal="Reach the light-sculpture core in the upper-right corner.",
        condition="Static fields drain effort fast. The shortest walk is not always the cheapest.",
        extraction="Head back to the extraction pad in the lower-left corner.",
        objective_name="light-sculpture core",
        grid=GALLERY_MAP,
        usefulness={"scanner": 3, "decoy": 2, "boots": 9,
                    "repair": 3, "lens": 2, "shield": 4},
    ),
    "relay": Mission(
        "relay", "The Relay", "Hard", "alert",
        hook="Download a signal key while the relay grid is watching.",
        goal="Download the signal key from the relay room.",
        condition="Taking the key triggers an alert that seals the relay gate.",
        extraction="Get back to the extraction lift on the left, by any route still open.",
        objective_name="signal key",
        grid=RELAY_MAP,
        usefulness={"scanner": 4, "decoy": 8, "boots": 3,
                    "repair": 5, "lens": 1, "shield": 6},
    ),
}

# ---------------------------------------------------------------- hard missions
# Verified with the state-graph planner (tests/test_missions.py and
# tests/test_state_planner.py): every leg has a safe route, every leg needs
# timing (the plain shortest route would be spotted), and the start tile is
# never watched at turn 0.

VAULT_MAP = [
    "############",
    "#S..#......#",
    "#.#.#.####.#",
    "#.#...#....#",
    "#.###.#.####",
    "#...#.#....#",
    "###.#.####.#",
    "#...#...O#.#",
    "#.#####.##.#",
    "#E.........#",
    "############",
]

LAB_MAP = [
    "############",
    "#S..#.....k#",
    "#.#.#.##.###",
    "#.#....#...#",
    "#.####.#.#.#",
    "#......#.#.#",
    "####.###.#.#",
    "#T.D.#.....#",
    "####.#.###L#",
    "#E.....#.O.#",
    "############",
]

PENTHOUSE_MAP = [
    "############",
    "#S.~~..#..k#",
    "#..#.#.#.#.#",
    "##.#.#...#.#",
    "#..#####D#.#",
    "#.##T....#.#",
    "#...######.#",
    "#.##.#.LO#.#",
    "#..#...#L#.#",
    "#E.~~~.....#",
    "############",
]

MISSIONS["vault"] = Mission(
    "vault", "The Vault", "Hard", "patrol",
    hook="Slip between three patrol drones to reach the vault core.",
    goal="Reach the vault core in the middle of the facility.",
    condition="Drones move one tile every turn and see two tiles ahead. Wait to let them pass.",
    extraction="Get back to the extraction hatch in the lower-left corner unseen.",
    objective_name="vault core",
    grid=VAULT_MAP,
    usefulness={"scanner": 7, "decoy": 8, "boots": 1,
                "repair": 1, "lens": 2, "shield": 6},
    drones=[Drone("North sweeper", [(1, 6), (1, 10)]),
            Drone("Shaft guard", [(3, 5), (7, 5)]),
            Drone("Floor patrol", [(9, 2), (9, 10)])],
    risk_bonus=150,
)

MISSIONS["lab"] = Mission(
    "lab", "The Lab", "Expert", "keycard",
    hook="Steal a keycard, crack a power relay and lift the prototype.",
    goal="Take the prototype from the sealed lab in the lower-right corner.",
    condition="The terminal room is locked: find the keycard. Hack the terminal to drop the laser.",
    extraction="Leave by the lower-left lift while the floor patrol looks away.",
    objective_name="prototype",
    grid=LAB_MAP,
    usefulness={"scanner": 5, "decoy": 6, "boots": 1,
                "repair": 6, "lens": 8, "shield": 4},
    drones=[Drone("Key corridor", [(1, 5), (1, 8)]),
            Drone("East shaft", [(3, 10), (7, 10)]),
            Drone("Hall patrol", [(5, 1), (5, 4)]),
            Drone("Exit patrol", [(9, 2), (9, 6)])],
    puzzle_kind="power",
    risk_bonus=350,
)

MISSIONS["penthouse"] = Mission(
    "penthouse", "The Penthouse", "Master", "mastermind",
    hook="Drones, a keycard, lasers and a cargo lock - all at once.",
    goal="Open the penthouse safe in the east wing.",
    condition="Static fields, three drones, and a cargo-lock terminal sealed behind a locked door.",
    extraction="Ride the service shaft down to extraction in the lower-left corner.",
    objective_name="penthouse safe",
    grid=PENTHOUSE_MAP,
    usefulness={"scanner": 5, "decoy": 7, "boots": 6,
                "repair": 3, "lens": 6, "shield": 5},
    drones=[Drone("Atrium guard", [(1, 4), (3, 4)]),
            Drone("Gallery floor", [(9, 5), (9, 9)]),
            Drone("East shaft", [(3, 10), (7, 10)])],
    puzzle_kind="cargo",
    risk_bonus=250,
)

MISSION_ORDER = ("archive", "gallery", "relay", "vault", "lab", "penthouse")
