# Heist Planner Game — Mission Strategy Simulator

A top-down stealth-puzzle game written in **Python + Tkinter**. Guide an operative
through three fictional facilities guarded by patrol drones, keycard doors, laser
barriers and hacking terminals, collect the objective and reach extraction unseen.

Under the hood:

- **Dijkstra's shortest-path algorithm on a state graph** plans every route: the vertex
  is (tile, drone clock, keycard held), so the planner knows *when* to move and when to
  wait so that no drone ever sees you.
- **Dijkstra** also judges the **Power Relay** terminal puzzle (lightest path).
- **0/1 Knapsack (dynamic programming)** judges the **Cargo Lock** terminal puzzle
  (richest load within a mass limit).

Results are saved in **SQLite** by default, or in **Oracle Database through real PL/SQL
stored procedures** when Oracle mode is on.

> Everything in the game is fictional: invented places, drones, keycards and devices.
> It is an entertainment puzzle, not a guide to any real security system.

Project by **Anshul Kaushik** — MCA (AI & ML), Chandigarh University.

---

## 1. Features

- Three missions with fixed, verified maps: **The Vault** (Hard), **The Lab** (Expert)
  and **The Penthouse** (Master).
- **Patrol drones** move one tile per turn on fixed patrols and watch two tiles ahead;
  being seen fails the mission. **Wait** lets a patrol pass. Amber outlines preview where
  the drones will look after your next turn.
- **Keycards and locked doors**, **laser barriers** and **hacking terminals** with two
  puzzle types: **Power Relay** (judged by Dijkstra) and **Cargo Lock** (judged by the
  Knapsack DP). A greedy answer never works.
- **Plan Route** finds the cheapest route no drone can see, including the turns to wait
  (amber badges on the map). **Move Next Step**, **Auto Travel** (animated with `after()`),
  **Stop**, arrow keys for manual moves.
- **Pro mode**: no Plan Route, no Auto Travel, no preview — read the patrols yourself for
  +25% score.
- Map, rooms, drones, vision cones, route overlay and character are all drawn with
  `tkinter.Canvas` shapes (no image files).
- Score with breakdown, rank titles, save-exactly-once, abandoned and caught records.
- **Mission History** with statistics (current player or all players).
- SQLite by default (zero setup). Optional Oracle mode with tables, identity keys,
  a sequence, an audit trigger, two procedures, a report procedure and a function.
- 125 automated `unittest` tests.

## 2. Screens

| Screen | What it shows |
|---|---|
| Main Menu | Title, story, operative-name field (validated), Start Mission, Mission History, How to Play, About Project, Exit, and a drawn preview of the Vault with its drones and the planner's safe route. |
| How to Play | Drones, Wait, keycards, terminals, Pro mode, effort, score, keyboard shortcuts. Readable without starting a mission. |
| About Project | Technologies, the algorithm names (credits page for the teacher), active database mode. |
| Mission Select & Briefing | Three cards with drawn thumbnails (red dots = drones), difficulty and a hook; the briefing shows goal, special condition, extraction and terrain; the **Pro mode** switch and **Start Mission**. |
| Gameplay | Map + legend on the left (red stippled tiles = drone vision, amber outlines = next-turn vision, amber badges = waits on the route); sidebar with player, objective, position (e.g. "Sector C-4"), planned route ("Planned route: 25 steps (4 waits), effort 25"), next move, moves and waits, effort, status, security (keycard, lasers, drones) and event; buttons with correct enable/disable rules. |
| Terminal | Power Relay (6 × 6 numbered grid, click a path from IN to OUT) or Cargo Lock (7 crates with mass and credits), readout, Submit / Clear / Back to Map. |
| Mission Debrief | Final score and breakdown, rank, moves (waits), effort (lockouts), mode, outcome sentence, save status; Play Again / Choose Another Mission / Main Menu. |
| Mission History | Statistics tiles and a scrollable table (Player, Mission, Result incl. "Caught", Score, Rank, Moves, Effort, Mode, Date/Time), newest first, last 100 records, "All players" toggle, Refresh, Back. |

Menu bar: **Game** → Main Menu / Mission History / Exit, **Help** → How to Play / About.

## 3. Project structure

```
heist_planner_game\
├── app.py                  start the game: python app.py (logging, config, repository, window)
├── run_tests.bat           double-click to run all tests
├── requirements.txt        nothing needed for SQLite; oracledb optional
├── .env.example            copy to .env for Oracle mode (.env is git-ignored)
├── README.md  PROJECT_REPORT.md  VIVA_QUESTIONS.md
├── PROGRESS.md  progress_state.json  SESSION_LOG.md   (build progress / resume files)
├── core\
│   ├── config.py           paths (pathlib), constants, .env loader, logging setup
│   ├── missions.py         the three maps, drones, briefings, tile costs
│   ├── drones.py           patrol drones: patrol cycle, facing, vision, detection
│   ├── pathfinding.py      Dijkstra with heapq on a tile grid -> RouteResult
│   ├── state_planner.py    Dijkstra on the state graph (tile, clock, keycard) + Wait
│   ├── loadout_optimizer.py 0/1 Knapsack DP     -> LoadoutResult (Cargo Lock judge)
│   ├── puzzles.py          terminal puzzles: Power Relay and Cargo Lock
│   ├── scoring.py          score constants, calculate_score(), rank_title()
│   ├── game_engine.py      MissionRun state machine (no Tkinter inside)
│   └── validation.py       player-name validation
├── ui\
│   ├── styles.py           every colour + font + ttk Style in one place
│   ├── base_screen.py      BaseScreen(ttk.Frame) with on_show()/on_hide()/can_leave()
│   ├── main_window.py      one window, screen container, menu bar, saving, close/error handlers
│   ├── widgets.py          the sidebar info row
│   ├── map_view.py         tile drawing, drones, vision, route overlay, character, legend
│   └── menu_screen.py, info_screens.py, mission_select_screen.py, gameplay_screen.py,
│       terminal_screen.py, debrief_screen.py, history_screen.py
├── database\
│   ├── base_repository.py  BaseRepository (interface)
│   ├── sqlite_repository.py, oracle_repository.py   (both inherit BaseRepository)
│   ├── database_manager.py chooses the backend, Oracle -> SQLite fallback
│   ├── create_oracle_user.sql, setup_oracle.sql, oracle_manual_test.sql
├── data\                   heist_planner.db is created here automatically
├── logs\                   heist_planner.log
├── tools\                  benchmark_routes.py (optional, never imported by the game)
└── tests\                  unittest files + reference_algorithms.py (my DAA worksheet code)
                            + classic_maps.py (three plain test grids)
                            + manual_oracle_check.py (manual, not auto-discovered)
```

## 4. Technology stack

| Part | Technology | Standard library? |
|---|---|---|
| GUI | `tkinter`, `tkinter.ttk` (theme `clam`), `tkinter.Canvas`, `messagebox` | Yes |
| Algorithms | `heapq` (Dijkstra), plain lists (DP table), `math.gcd` (LCM of patrols) | Yes |
| Data / state | `dataclasses`, classes, dictionaries, sets, tuples | Yes |
| Local save | `sqlite3` | Yes |
| Paths, logs, config | `pathlib`, `logging`, own tiny `.env` loader | Yes |
| Tests | `unittest`, `tempfile`, `itertools`, `random` | Yes |
| Oracle mode (optional) | Oracle AI Database 26ai Free / 19c, PL/SQL, **`oracledb`** (Thin mode) | **No** — `pip install oracledb` |

No NumPy, Pandas, Matplotlib, Pygame, `keyboard` or `pynput` inside the game.

## 5. Installation aur game chalana (SQLite mode)

**Step 1 — environment check.** Pehle project folder `D:\DAA\heist_planner_game` mein
terminal kholo (File Explorer mein folder kholo, address bar mein `cmd` likho, Enter).
Phir yeh commands chalao:

```bash
python --version
```

Python 3.11 ya usse naya version dikhna chahiye (3.12, 3.13, 3.14 bhi chalega).

```bash
python -m tkinter
```

Ek chhoti si test window khulni chahiye. Agar khul gayi, to Tkinter theek hai — window band kar do.

**Step 2 — game chalao.** Bas yeh likho:

```bash
python app.py
```

Terminal hamesha project folder (`D:\DAA\heist_planner_game`) mein khulna chahiye. Agar
terminal kisi aur folder mein hai, to pehle `cd /d D:\DAA\heist_planner_game` likho, ya
seedha poora path do: `python D:\DAA\heist_planner_game\app.py` (yeh bhi chalega, kyunki
saare paths `pathlib` se project folder ke hisaab se bante hain). Kisi `pip install` ki
zaroorat nahi hai.

**Save file kahan hai?** Pehli baar chalane pe game khud `data\heist_planner.db` (SQLite
file) bana deta hai. Saare results isi file mein save hote hain aur game band karke
dobara kholne pe bhi rehte hain. Agar history saaf karni ho to game band karke yeh
file delete kar sakte ho — agli baar nayi khaali file ban jaayegi.

**Tests chalane ke liye:**

```bash
python -m unittest discover -s tests -v
```

Ya `run_tests.bat` pe double-click karo. Last run: **125 tests, sab OK**.

## 6. Oracle mode (optional, PL/SQL)

SQLite mode mein **koi PL/SQL nahi chalta** — SQLite sirf ek local file database hai.
Oracle mode mein game sach mein Oracle ke stored procedures `HP_SAVE_RUN`,
`HP_GET_STATS` aur function `HP_RANK_TITLE` ko call karta hai.

**Mere laptop ke facts (Windows 11 Home):** Oracle ki Windows installation guide kehti
hai "Windows Home is not supported", aur Docker Desktop ki requirements mein bhi sirf
Windows 11 Enterprise / Pro / Education (23H2+) hain. Isliye do routes hain, dono ka
result same hai — `localhost:1521/FREEPDB1` pe user `HEIST`:

- **Route A (abhi use ho raha hai):** Windows zip installer
  `oracle-ai-database-free-26ai-23.26.3.windows.x64.zip`. Officially Home pe supported
  nahi hai, lekin mere laptop pe install ho gaya (`D:\app\oracle26ai\dbhomeFree`, `sqlplus`
  bhi wahin hai). Listener `localhost:1521/FREEPDB1` pe jawab de raha hai.
- **Route B (backup):** Oracle ki official image
  `container-registry.oracle.com/database/free:latest-lite` ko **Podman ke saath Ubuntu
  (WSL 2)** mein chalana. Container ka naam `oracle26ai`, port 1521, data volume `oradata`.
  Windows wala Python WSL ke localhost forwarding se `localhost:1521/FREEPDB1` tak pahunchta hai.
- **Aur backups:** FreeSQL.com (Oracle ka free browser database, woh bhi 26ai chalata hai)
  ya college ka server — bas `ORACLE_DSN` badalna padega.

Poori step-by-step setup `D:\DAA\SETUP_GUIDE.md` **Part 8** mein hai. Short mein:

1. **Database start karo.** Route A: Windows service `OracleServiceFREE` chal rahi honi
   chahiye. Route B: Ubuntu mein `podman start oracle26ai`, phir `podman logs -f oracle26ai`
   mein **"DATABASE IS READY TO USE!"** aane tak ruko.
2. **HEIST user banao (sirf ek baar, SYSTEM se).** Agar user pehle se bana hai to skip karo.
   ```bash
   sqlplus system@localhost:1521/FREEPDB1 @database\create_oracle_user.sql
   ```
   Script HEIST ka password poochhegi (file mein koi password nahi likha).
   Route B mein: `podman exec -it oracle26ai sqlplus system@FREEPDB1 @/tmp/create_oracle_user.sql`
   (pehle `podman cp` se file container mein copy karo).
3. **Tables aur procedures banao (HEIST se).**
   ```bash
   sqlplus heist@localhost:1521/FREEPDB1 @database\setup_oracle.sql
   ```
   Script dobara chalane pe bhi safe hai (purane objects pehle drop hote hain, missions `MERGE`
   se). **Dhyan do:** tables drop hoti hain, to purane saved runs chale jaate hain — pehle
   backup lo agar rakhne hain.
4. **Manual test (optional, data rollback ho jaata hai):**
   ```bash
   sqlplus heist@localhost:1521/FREEPDB1 @database\oracle_manual_test.sql
   ```
5. **Driver install karo:**
   ```bash
   pip install oracledb
   ```
   `oracledb` default **Thin mode** mein chalta hai — Oracle Instant Client ki zaroorat nahi.
6. **`.env` banao:** `.env.example` ko copy karke `.env` naam do aur values bharo:
   ```
   DATABASE_BACKEND=oracle
   ORACLE_USER=HEIST
   ORACLE_PASSWORD=<tumhara HEIST password>
   ORACLE_DSN=localhost:1521/FREEPDB1
   ```
   `.env` `.gitignore` mein hai, password code mein kabhi nahi jaata. Game kabhi SYS/SYSTEM
   se connect nahi karta (aisa likhoge to game mana kar dega).
7. **Python check:** `python tests\manual_oracle_check.py` — saari lines `PASS` aani chahiye.
8. **Game chalao** aur **About Project** screen pe dekho: "Oracle PL/SQL connected" likha
   aana chahiye. Agar Oracle nahi mila, game ek chhota message dikha ke **SQLite pe chalta
   rahega** ("Oracle unavailable — using SQLite (...reason...)").

Friendly error messages: server nahi mila → "Oracle server could not be reached";
`ORA-01017` → "Oracle username or password is wrong"; `ORA-00942` / `ORA-06550` /
`PLS-00201` → "Oracle tables or procedures not found — run database/setup_oracle.sql first".

**Oracle status — tested live** against my Oracle AI Database 26ai Free (23.26.3, Route A,
`FREEPDB1`, user `heist`, `oracledb` Thin mode):

- 27 Oct 2026: `setup_oracle.sql` ran three times without errors; all 15 objects VALID
  (4 tables, 1 sequence, 1 trigger, 3 procedures, 1 function, 5 indexes); a real game in
  Oracle mode saved through `HP_SAVE_RUN` and read back with `HP_RANK_TITLE`.
- 30 Oct 2026 (after the three-mission update): `oracle_manual_test.sql` — saves on the
  Vault, Lab and Penthouse (incl. a CAUGHT Pro-mode run), stats 3 / 1 / 880 / 880, unknown
  player all 0, `ORA-20001` and `ORA-20002` rejections, rank titles, audit rows and the
  cursor report; `python tests\manual_oracle_check.py`: **ALL CHECKS PASSED**. Test rows
  are rolled back; the real runs already saved in Oracle were not touched.

## 7. Controls

| Action | Button | Key |
|---|---|---|
| Plan the cheapest safe route to the current target | Plan Route | `P` |
| Take the next turn of the route (a move or a wait) | Move Next Step | `Space` |
| Walk the whole route (animated) | Auto Travel | `A` |
| Pause Auto Travel | Stop | `Esc` |
| Stay on the spot for one turn (drones keep moving) | Wait | `W` |
| Pick up the objective (only while standing on it) | Collect Objective | `C` |
| Open the terminal puzzle (standing on it, lasers on) | Hack Terminal | `H` |
| Move one tile by hand (walls, locked doors, lasers refuse) | — | Arrow keys |
| Start again (drones, keycard, lasers and puzzle reset) | Restart Mission | — |
| Leave (asks "Abandon mission?" after a move) | Return to Menu | — |

## 8. Algorithm design

### 8.1 Dijkstra on a tile grid (`core/pathfinding.py`)

- **Graph:** every walkable tile `(row, col)` is a **vertex**. A step up, right, down or
  left (no diagonals) into a walkable neighbour is a directed **edge**. Walls (`#`) and
  blocked tiles are not vertices at all, so no route can cross them.
- **Cost model (entered-tile):** a step costs the cost of the tile you **enter**: floor,
  start, objective, extraction, keycard, open door, terminal, switched-off laser = 1;
  static field `~` = 4. The start tile is never charged. All costs are positive, which is
  why Dijkstra is correct here.
- **Heap:** `heapq` holds `(cost, row, col)`. The smallest cost is popped first; ties are
  broken by row then column, and neighbours are explored in the fixed order up, right,
  down, left — so the same map always gives the same path.
- **Stale entries:** `if d > dist[node]: continue` skips old, more expensive entries.
  The search **stops early** when the goal is popped.
- **Path reconstruction:** `previous[tile]` remembers where we came from on the cheapest
  route; walking back from the goal and reversing gives the path.
- **No route:** returns `RouteResult([], None, False)` instead of raising.
- **Complexity:** O((V + E) log V); on a tile map E ≤ 4V. My DAA Experiment 4 used an
  adjacency matrix and a linear scan, O(V²).

**Hand-worked example** (test grid "Gallery" in `tests/classic_maps.py`):

```
############
#S..~~~~..O#      direct route along row 1: 9 steps
#.##~~~~##.#        enters 2 floor + 4 static + 3 floor
#.##....##.#        = 2 + 4×4 + 3 = 21 effort
#.########.#
#..........#      long loop: down column 1, along row 5, up column 10
#.########.#        17 steps, all floor = 17 effort  ← cheapest
#E.........#
############      with half-cost static fields: 2 + 4×2 + 3 = 13 in 9 steps ← new best
```

So the shortest route (9 steps) is **not** the cheapest (17 steps). The tests check these
numbers and more (Archive 14 / 8, Relay 13 / 11 → 19 with its gate blocked) on the three
test grids, and compare every pair of tiles with my matrix Dijkstra.

### 8.2 Dijkstra on a state graph — Route Guidance (`core/state_planner.py`)

With drones, a tile is not enough to describe "where you are": a move into tile X is safe
at turn 4 and deadly at turn 5, and a door is a wall until you hold the keycard. So the
planner's **vertex is a state**:

```
(row, col, drone_clock, has_key)
```

- **Drones are periodic** (`core/drones.py`): a ping-pong patrol of n tiles repeats every
  2(n − 1) turns, so `position(t) = cycle[t mod period]`. After LCM(all periods) turns
  every drone is back at the start, so the clock is stored modulo that LCM
  (Vault 16, Lab 24, Penthouse 8).
- **Edges** = one turn: four moves (cost of the entered tile) and **Wait** (cost 1).
  An edge is removed if it enters a wall, a locked door without the keycard or an active
  laser, if any drone can see the new tile after the turn (own tile + 2 tiles ahead,
  blocked by walls/doors), or if the player and a drone swap tiles.
- Stepping on `k` sets `has_key`.
- It is **the same Dijkstra** (heap, stale-entry skip, `previous` map), just on a graph of
  at most 132 × 24 × 2 ≈ 6,300 states. O((S + T) log S).
- If lasers block every route, the planner routes to the terminal first.
- **Correctness checks:** with no drones and no keycard the state planner gives exactly the
  tile Dijkstra costs; with drones it matches **Bellman-Ford** (an O(V·E) algorithm without
  a priority queue) on every mission, and every planned path is replayed turn by turn to
  prove no drone ever sees it.

**The missions were verified with the planner too:** every part of every mission is
solvable, every part needs timing (the plain shortest path would be spotted), the keycard
and the terminal are really required, the start is never watched, and a route home exists
from the objective at every clock value. The Penthouse patrols were chosen by an exhaustive
search over drone triples. One design rule came out of this: you can never pass a drone
inside a one-tile-wide corridor that it patrols end to end.

| Mission | Drones (clock) | Planner legs: steps (waits) / effort | Plain route (seen!) | Total | Score |
|---|---|---|---|---|---|
| Vault | 3 (16) | start→core 25 (4) / 25 · core→exit 19 (2) / 19 | 13 · 9 | 44 | 880 |
| Lab | 4 (24) | start→terminal 52 (2) / 52 · →prototype 22 (2) / 22 · →exit 20 (2) / 20 | 30 · 16 · 14 | 94 | 830 |
| Penthouse | 3 (8) | start→terminal 25 (2) / 31 · →safe 32 (0) / 44 · →exit 10 (1) / 16 | 29 · 22 · 15 | 91 | 845 |

### 8.3 Terminal puzzles (`core/puzzles.py`)

- **Power Relay (Lab) — Dijkstra:** a 6 × 6 grid of numbers 1–9. The player clicks a path
  of touching cells from IN to OUT. It is accepted only if its load equals the minimum,
  which `find_shortest_path()` computes (the start cell's own number is added, because
  Dijkstra never charges the start).
- **Cargo Lock (Penthouse) — 0/1 Knapsack DP:** 7 crates with mass 2–9 kg and worth 3–20
  credits, lift limit = half the total mass. Accepted only if the credits equal the
  maximum from `recommend_loadout()` (`core/loadout_optimizer.py`).
- **No greedy shortcuts:** the generator throws away puzzles where "always step to the
  cheaper next cell" or "always take the best credits-per-kg crate" already gives the best
  answer — the classic reason why DAA uses Dijkstra and DP instead of greedy. Tests compare
  the Power Relay minimum with a brute-force DFS over all simple paths and the Cargo maximum
  with brute force over all subsets.
- A wrong answer is a lockout (+5 effort). Each run gets a new random puzzle (fixed seeds in
  tests).

### 8.4 0/1 Knapsack DP (`core/loadout_optimizer.py`)

- **Mapping:** item = crate (taken at most once → "0/1"), weight = **mass**, value =
  **credits**, capacity = **lift limit**.
- **Table:** `best[i][c]` = best result using only the first `i` crates with at most `c`
  kg. Recurrence: skip crate `i` → `best[i-1][c]`; take it (if it fits) →
  `best[i-1][c-mass] + credits`. Each cell stores the pair `(credits, -mass)`, compared like
  tuples.
- **Traceback:** start at `best[n][limit]` and walk up the rows: if taking crate `i` still
  reaches the cell's value, it was taken and the remaining capacity drops by its mass.
- **Tie-break (tested):** (1) most credits, (2) then the **lower total mass**, (3) then the
  alphabetically first sorted ID tuple.
- **Complexity:** O(n × C). Brute force is O(2ⁿ); my Experiment 6 Branch and Bound is also
  exponential in the worst case but prunes with a fractional bound.

**Worked example** (from `tests/test_loadout_optimizer.py`, limit 8): A (3 kg, 6 cr),
B (4, 3), C (3, 2), D (2, 2), E (2, 7), F (5, 3). Value-only DP table:

| i (item added) | c=0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| 0 (none) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 A (3, 6) | 0 | 0 | 0 | 6 | 6 | 6 | 6 | 6 | 6 |
| 2 B (4, 3) | 0 | 0 | 0 | 6 | 6 | 6 | 6 | 9 | 9 |
| 3 C (3, 2) | 0 | 0 | 0 | 6 | 6 | 6 | 8 | 9 | 9 |
| 4 D (2, 2) | 0 | 0 | 2 | 6 | 6 | 8 | 8 | 9 | 10 |
| 5 E (2, 7) | 0 | 0 | 7 | 7 | 9 | 13 | 13 | **15** | **15** |
| 6 F (5, 3) | 0 | 0 | 7 | 7 | 9 | 13 | 13 | 15 | **15** |

The best worth is **15**, already reached with only **7** kg (`best[6][7] = 15`). Two loads
give 15: **A + D + E (7 kg)** and **A + C + E (8 kg)**; the tie-break picks the lighter one.

### 8.5 Scoring (`core/scoring.py`)

`500 (success) + 200 (objective) + 100 (extraction) + high-risk bonus (Vault 300, Lab 500,
Penthouse 500) − 5 × effort`, then **+25% in Pro mode** (only when positive), never below 0.
Example: Vault with the planner's route, effort 44 → 500 + 200 + 100 + 300 − 220 = **880**
(a test checks this; the debrief, the saved record and the history table show the same
number). A caught run is saved as `CAUGHT` with score 0.
Ranks (same thresholds in Python and in `HP_RANK_TITLE`): Phantom ≥ 800, Specialist ≥ 650,
Operative ≥ 450, Rookie below.

## 9. Database design

| SQLite (default) | Oracle | Columns / notes |
|---|---|---|
| `players` | `HP_PLAYERS` | player_id (PK, autoincrement / identity), player_name UNIQUE NOT NULL, created_at |
| `missions` | `HP_MISSIONS` | mission_id PK ('vault', 'lab', 'penthouse'), mission_name, difficulty — seeded with `INSERT OR IGNORE` / `MERGE` |
| `mission_runs` | `HP_MISSION_RUNS` | run_id PK, player_id FK, mission_id FK, result CHECK SUCCESS/ABANDONED/CAUGHT, score CHECK ≥ 0, moves, route_cost, kit_summary, alert_triggered CHECK Y/N, played_at, pro_mode CHECK Y/N |
| — | `HP_RUN_AUDIT` + `HP_AUDIT_SEQ` | filled by trigger `HP_TRG_RUN_AUDIT` (AFTER INSERT ... FOR EACH ROW, uses `:NEW`, `USER`, `SYSDATE`) |

Relationships: one player → many runs; one mission → many runs.

**Legacy columns:** the first version of the game had gadget kits and a Relay alert.
`kit_summary` and `alert_triggered` are kept so that runs saved by that version (and the
old mission rows 'archive', 'gallery', 'relay' in existing databases) stay readable in
History. New runs always store `'None'` and `'N'` there.

Oracle PL/SQL objects (`database/setup_oracle.sql`, works on 26ai and 19c):

- **`HP_SAVE_RUN`** (9 IN incl. `p_pro_mode` + `p_run_id OUT`): validates input (named
  exceptions → `RAISE_APPLICATION_ERROR -20001/-20003/-20004`), checks the mission with
  `SELECT ... INTO` + `NO_DATA_FOUND` (→ `-20002`), finds or creates the player (safe
  against the UNIQUE constraint), inserts the run with `RETURNING run_id INTO p_run_id`.
- **`HP_GET_STATS`** (IN player or NULL for all; 4 OUT): `COUNT` + `NVL`, so an unknown
  player or empty table returns zeros.
- **`HP_RANK_TITLE(p_score)`**: `CASE` → Phantom / Specialist / Operative / Rookie, used
  inside the history `SELECT`.
- **`HP_PRINT_RECENT_RUNS(p_limit)`**: explicit cursor report with `DBMS_OUTPUT` for demos.

**Three deliberate differences from my college PL/SQL programs** (also commented in the SQL file):

1. My college procedures call `COMMIT`. Here the **procedures never commit** — Python owns
   the transaction: it commits after a successful call and rolls back on any error.
2. My college programs end with `WHEN OTHERS THEN DBMS_OUTPUT.PUT_LINE(...)`, which hides
   failures. Here bad input raises `RAISE_APPLICATION_ERROR(-200xx, ...)`, which `oracledb`
   receives as a real exception.
3. Some lines in my notes are plain sentences without `--` (e.g. "Validate minimum
   balance"), which would not compile. Every comment in the new scripts starts with `--`.

**Upgrading old save files:** SQLite cannot change a CHECK constraint, so an old
`data/heist_planner.db` (without `pro_mode` and without `CAUGHT`) is rebuilt once on start-up:
rename the table, create the new one, copy every row, drop the old one, all in one
transaction.

Both repositories use only parameterised queries (`?` in SQLite, `:player` / `:lim` binds
in Oracle). Player text is never concatenated into SQL.

## 10. From my college worksheets to this game

| Worksheet / notes | Used in the game as |
|---|---|
| DAA Exp 4 — Dijkstra (matrix, O(V²)) | Game uses heap versions (tile graph and state graph). The matrix version is kept as `dijkstra_matrix()` in `tests/reference_algorithms.py`, with the **indentation bug fixed** (the break / visited / relaxation lines were inside the min-search loop, and the `new_distance` check was not under `graph[current][v] > 0`). A test compares both versions on every pair of tiles of the test grids and the mission maps. |
| DAA Exp 6 — 0/1 Knapsack Branch & Bound | Game uses DP (Cargo Lock judge). My `knapsack_bb()` is copied unchanged (only formatting) into the tests; DP, B&B and brute force must agree on 30 Cargo puzzles and 200 random cases. |
| DAA Exp 3 — Kruskal's Union-Find | My `find()` (path compression) and `union()` (by rank) prove every walkable tile of each mission is in one connected group. |
| DAA Exp 1 — timing with `perf_counter()` | Optional `tools/benchmark_routes.py`: heap vs matrix Dijkstra on growing random grids; a Matplotlib line graph only if Matplotlib is installed, otherwise a table. At about 1000 tiles: heap 2.9 ms, matrix 86.5 ms, same costs. |
| Python worksheets 1–5, slides 1.x | Classes with `__init__`, dictionary keyed by ID with `in` checks (missions), `.strip()` + default + range checks (player name), tuples for positions, sets for watched tiles, default arguments, docstrings, inheritance + overriding (`BaseScreen`, `BaseRepository`). |
| Tkinter slides 3.1–3.5 | `Tk()`, `geometry()`, `title()`, `mainloop()`, `Canvas` shapes, `grid`/`pack`, `Menu`, `bind()`. The `keyboard` / `pynput` modules from slide 3.4 are **not** used — Tkinter's own `bind()` is the right tool inside a window. |
| PL/SQL Programs 2–6 | 2 explicit cursor → `HP_PRINT_RECENT_RUNS`; 3 function with CASE → `HP_RANK_TITLE`; 4 SELECT INTO / NO_DATA_FOUND → `HP_SAVE_RUN`; 5 user-defined exceptions → validation in `HP_SAVE_RUN`; 6 sequence + audit trigger → `HP_AUDIT_SEQ` + `HP_TRG_RUN_AUDIT`. |

## 11. Testing

```bash
python -m unittest discover -s tests -v
```

Last result: **125 tests, OK** — game engine 26, pathfinding 18, missions 13, SQLite
repository 13, drones 11, state planner 9, puzzles 9, loadout optimizer 9, Oracle repository
(offline, fake connection) 7, scoring 6, validation 4.

`tests/manual_oracle_check.py` is the real Oracle check (run by hand; it rolls back its data).

## 12. Manual test checklist (repeat before the demo)

| # | Check | ✓ |
|---|---|---|
| 1 | `python app.py` opens the menu; the window title is "Heist Planner Game \| Mission Strategy Simulator" | ☐ |
| 2 | A bad name like `a<b>` shows an inline message; an empty name becomes "Agent" | ☐ |
| 3 | Mission Select: three cards; clicking a card shows its briefing; Back works | ☐ |
| 4 | Start Mission opens the map directly (no preparation screen) | ☐ |
| 5 | Vault: drones move one tile per turn; red tiles show their vision; amber outlines show the next turn | ☐ |
| 6 | Vault: Plan Route shows "25 steps (4 waits), effort 25" and amber wait badges | ☐ |
| 7 | Move Next Step (Space) takes one turn; Auto Travel (A) animates; Stop (Esc) pauses; Wait (W) spends a turn | ☐ |
| 8 | Stepping into a red tile ends the mission ("Spotted by ...") and History shows "Caught" | ☐ |
| 9 | Collect Objective is only enabled on the objective; reaching extraction without it does not finish | ☐ |
| 10 | Vault with the planner's route finishes with 880 (Phantom); History shows it exactly once | ☐ |
| 11 | Lab: the locked door refuses you until you step on the keycard; Plan Route first goes to the terminal | ☐ |
| 12 | Lab: Hack Terminal opens the Power Relay; a wrong path costs +5 effort; the right one switches the laser off | ☐ |
| 13 | Penthouse: the Cargo Lock accepts only the richest load within the lift limit | ☐ |
| 14 | Pro mode: Plan Route / Auto Travel / preview are off; debrief shows "Pro mode bonus (+25%)"; History shows "Pro" | ☐ |
| 15 | Restart Mission resets moves, effort, drones, keycard and lasers | ☐ |
| 16 | Return to Menu after moving asks "Abandon mission?"; Yes saves one ABANDONED row | ☐ |
| 17 | Play Again on the debrief starts the same mission straight away | ☐ |
| 18 | About Project shows the database mode; (Oracle) "Oracle PL/SQL connected" | ☐ |

## 13. Limitations and future work

- Oracle mode was tested live on Oracle AI Database 26ai Free only (Section 6). The 19c
  compatibility of `setup_oracle.sql` comes from avoiding 23ai-only syntax; it was not run on
  a real 19c server (FreeSQL.com / college server).
- Three fixed maps; drones follow fixed patrols (no chasing AI), no map editor, no sound.
- The database keeps two legacy columns (`kit_summary`, `alert_triggered`) from the first
  version so old records stay readable.
- On this laptop's 1280×720 (scaled) screen the window is sized to the screen (about 1180×630)
  instead of the planned 1180×760; all screens were checked at 1000×620.
- Possible future work: more missions loaded from JSON, a replay of the last route, an
  Oracle view for leaderboards.
