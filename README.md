# Heist Planner Game — Mission Strategy Simulator

A small top-down tactical puzzle game written in **Python + Tkinter**. You plan a kit
of gadgets, guide an operative through a fictional facility, collect the objective
and reach extraction. Under the hood the game uses **Dijkstra's shortest-path
algorithm** (route guidance) and the **0/1 Knapsack problem solved with dynamic
programming** (Suggested Kit). Results are saved in **SQLite** by default, or in
**Oracle Database through real PL/SQL stored procedures** when Oracle mode is on.

> Everything in the game is fictional: invented places, "static fields", "relay
> gates" and imaginary gadgets. It is an entertainment puzzle, not a guide to any
> real security system.

Project by **Anshul Kaushik** — MCA (AI & ML), Chandigarh University.

---

## 1. Features

- Three missions with fixed, verified maps: **The Archive** (Easy), **The Gallery**
  (Medium), **The Relay** (Hard).
- Map, rooms, walls, special tiles, the route overlay and the character are all drawn
  with `tkinter.Canvas` shapes (no image files).
- **Plan Route** finds the cheapest safe route (Dijkstra); **Move Next Step**,
  **Auto Travel** (animated with `after()`), **Stop**, arrow keys for manual moves.
- **Suggested Kit** picks the most useful gadgets within 8 energy units (0/1 Knapsack DP).
- Gadgets really change the game: Mobility Boots change the best Gallery route,
  the Pocket Scanner reveals the weak gate in the Relay, the Signal Decoy cancels the
  alert penalty.
- **Relay alert**: collecting the signal key seals the relay gate; the route is
  recalculated at once (11 → 19 effort). The alert can also be triggered early.
- Score with breakdown, rank titles, save-exactly-once, abandoned-run records.
- **Mission History** with statistics (current player or all players).
- SQLite by default (zero setup). Optional Oracle mode with tables, identity keys,
  a sequence, an audit trigger, two procedures, a report procedure and a function.
- 96 automated `unittest` tests.

## 2. Screens

| Screen | What it shows |
|---|---|
| Main Menu | Title, story, operative-name field (validated), Start Mission, Mission History, How to Play, About Project, Exit, and a drawn facility preview. |
| How to Play | Rules, effort, alerts, score, keyboard shortcuts. Readable without starting a mission. |
| About Project | Technologies, both algorithm names (credits page for the teacher), active database mode. |
| Mission Select & Briefing | Three cards with drawn thumbnails, difficulty and a hook; the briefing shows goal, special condition, extraction and terrain. |
| Equipment Preparation | Six gadgets with energy cost, usefulness bars (Low / Medium / High), Pack checkboxes, energy bar "Energy used: x / 8", Mission Readiness %, Suggested Kit, Begin Mission. Over-capacity ticks are refused with a friendly message. |
| Gameplay | Map + legend on the left; sidebar with player, objective, position (e.g. "Sector C-4"), planned route ("Planned route: 9 steps, effort 13"), next direction, moves, effort, status, kit and event; buttons with correct enable/disable rules. |
| Mission Debrief | Final score and breakdown, rank, moves, effort, kit, alert, outcome sentence, save status; Play Again / Choose Another Mission / Main Menu. |
| Mission History | Statistics tiles and a scrollable table (Player, Mission, Result, Score, Rank, Moves, Effort, Kit, Date/Time), newest first, last 100 records, "All players" toggle, Refresh, Back. |

Menu bar: **Game** → Main Menu / Mission History / Exit, **Help** → How to Play / About.

## 3. Project structure

```
heist_planner_game\
├── app.py                  start the game (logging, config, repository, window, mainloop)
├── run_game.bat            double-click to play
├── run_tests.bat           double-click to run all tests
├── requirements.txt        nothing needed for SQLite; oracledb optional
├── .env.example            copy to .env for Oracle mode (.env is git-ignored)
├── README.md  PROJECT_REPORT.md  VIVA_QUESTIONS.md
├── PROGRESS.md  progress_state.json  SESSION_LOG.md   (build progress / resume files)
├── core\
│   ├── config.py           paths (pathlib), constants, .env loader, logging setup
│   ├── missions.py         the three maps, briefings, usefulness values, tile costs
│   ├── gadgets.py          gadget catalogue (dictionary keyed by ID)
│   ├── pathfinding.py      Dijkstra with heapq  -> RouteResult
│   ├── loadout_optimizer.py 0/1 Knapsack DP     -> LoadoutResult
│   ├── scoring.py          score constants, calculate_score(), rank_title()
│   ├── game_engine.py      MissionRun state machine (no Tkinter inside)
│   └── validation.py       player-name validation
├── ui\
│   ├── styles.py           every colour + font + ttk Style in one place
│   ├── base_screen.py      BaseScreen(ttk.Frame) with on_show()/on_hide()/can_leave()
│   ├── main_window.py      one window, screen container, menu bar, saving, close/error handlers
│   ├── widgets.py          scrollable frame, capacity bar, usefulness bars, info rows
│   ├── map_view.py         tile drawing, route overlay, character, legend, thumbnails
│   └── menu_screen.py, info_screens.py, mission_select_screen.py, preparation_screen.py,
│       gameplay_screen.py, debrief_screen.py, history_screen.py
├── database\
│   ├── base_repository.py  BaseRepository (interface)
│   ├── sqlite_repository.py, oracle_repository.py   (both inherit BaseRepository)
│   ├── database_manager.py chooses the backend, Oracle -> SQLite fallback
│   ├── create_oracle_user.sql, setup_oracle.sql, oracle_manual_test.sql
├── data\                   heist_planner.db is created here automatically
├── logs\                   heist_planner.log
└── tests\                  unittest files + reference_algorithms.py (my DAA worksheet code)
                            + manual_oracle_check.py (manual, not auto-discovered)
```

`tools\benchmark_routes.py` is an optional extra (never imported by the game): it times the
heap Dijkstra against my matrix version on growing random grids.

## 4. Technology stack

| Part | Technology | Standard library? |
|---|---|---|
| GUI | `tkinter`, `tkinter.ttk` (theme `clam`), `tkinter.Canvas`, `messagebox` | Yes |
| Algorithms | `heapq` (Dijkstra), plain lists (DP table) | Yes |
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

Ya phir `run_game.bat` pe double-click kar do. Kisi `pip install` ki zaroorat nahi hai.

**Save file kahan hai?** Pehli baar chalane pe game khud `data\heist_planner.db` (SQLite
file) bana deta hai. Saare results isi file mein save hote hain aur game band karke
dobara kholne pe bhi rehte hain. Agar history saaf karni ho to game band karke yeh
file delete kar sakte ho — agli baar nayi khaali file ban jaayegi.

**Tests chalane ke liye:**

```bash
python -m unittest discover -s tests -v
```

Ya `run_tests.bat` pe double-click karo. Last run: **96 tests, sab OK**.

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
   Script dobara chalane pe bhi safe hai (purane objects pehle drop hote hain, missions `MERGE` se).
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

**Oracle status of this build — tested live on 27 Oct 2026** against my Oracle AI Database
26ai Free (23.26.3, Route A, `FREEPDB1`, user `heist`, `oracledb` Thin mode):

- `setup_oracle.sql` ran three times in a row without errors; all 15 objects VALID
  (4 tables, 1 sequence, 1 trigger, 3 procedures, 1 function, 5 indexes).
- `oracle_manual_test.sql`: saves, stats (2 / 1 / 810 / 810, unknown player all 0),
  `ORA-20001` and `ORA-20002` rejections, rank titles, audit rows and the cursor report all
  as expected; test rows rolled back.
- `python tests\manual_oracle_check.py`: **ALL CHECKS PASSED** (data rolled back).
- Game in Oracle mode: About showed "Oracle PL/SQL connected"; Gallery (810) and Relay
  (790, alert with decoy) were saved through `HP_SAVE_RUN`, and History read them back from
  Oracle with ranks from `HP_RANK_TITLE`. Those two runs are real game rows and are still
  in the database.

## 7. Controls

| Action | Button | Key |
|---|---|---|
| Plan the cheapest route to the current target | Plan Route | `P` |
| Move one tile along the route | Move Next Step | `Space` |
| Walk the whole route (animated) | Auto Travel | `A` |
| Pause Auto Travel | Stop | `Esc` |
| Pick up the objective (only while standing on it) | Collect Objective | `C` |
| Move one tile by hand (walls and sealed gates refuse) | — | Arrow keys |
| Raise the Relay alert early (Relay only, once) | Trigger Alert | — |
| Start again with the same kit | Restart Mission | — |
| Leave (asks "Abandon mission?" after a move) | Return to Menu | — |

## 8. Algorithm design

### 8.1 Dijkstra — Route Guidance (`core/pathfinding.py`)

- **Graph:** every walkable tile `(row, col)` is a **vertex**. A step up, right, down or
  left (no diagonals) into a walkable neighbour is a directed **edge**. Walls (`#`) and the
  sealed gate are not vertices at all, so no route can cross them.
- **Cost model (entered-tile):** a step costs the cost of the tile you **enter**. Floor,
  start, objective, extraction and open gate = 1; static field `~` = 4, or 2 with Mobility
  Boots. The start tile is never charged. Each step adds 1 move and the tile cost to
  effort. All costs are positive, which is why Dijkstra is correct here.
- **Heap:** `heapq` holds `(cost, row, col)`. The smallest cost is popped first; ties are
  broken by row then column, and neighbours are explored in the fixed order up, right,
  down, left — so the same map always gives the same path.
- **Stale entries:** a tile can be pushed several times; `if d > dist[node]: continue`
  skips the old, more expensive entries. The search **stops early** when the goal is popped.
- **Path reconstruction:** `previous[tile]` remembers where we came from on the cheapest
  route; walking back from the goal and reversing gives the path (start and goal included).
- **No route:** returns `RouteResult([], None, False)` instead of raising; invalid
  positions also give this controlled result (and a log warning).
- **Goal switch:** before collection the target is the objective, afterwards the
  extraction point. **Plan Route** always plans from the current position to the current target.
- **Rerouting:** when the Relay alert seals the gate, the engine adds the gate to
  `sealed_tiles`, throws away the current route, stops Auto Travel and runs Dijkstra
  again from the current position (Relay objective → exit: **11 → 19**).
- **Complexity:** O((V + E) log V); on a tile map E ≤ 4V. My DAA Experiment 4 used an
  adjacency matrix and a linear scan, O(V²).

**Hand-worked example — The Gallery** (start (1,1), objective (1,10)):

```
############
#S..~~~~..O#      direct route along row 1: 9 steps
#.##~~~~##.#        enters 2 floor + 4 static + 3 floor
#.##....##.#        = 2 + 4×4 + 3 = 21 effort
#.########.#
#..........#      long loop: down column 1, along row 5, up column 10
#.########.#        17 steps, all floor = 17 effort  ← cheapest without boots
#E.........#
############      with Mobility Boots: 2 + 4×2 + 3 = 13 in 9 steps ← new best route
```

So the shortest route (9 steps) is **not** the cheapest (17 steps) — until the boots
change the tile costs. Objective → extraction costs 15 (two different 15-cost routes
exist; tests check the cost and the validity of the path, not one exact sequence).

All verified numbers: Archive 14 / 8 · Gallery 17 (13 with boots, direct 21) / 15 ·
Relay 13 / 11, and 19 after the gate is sealed.

### 8.2 0/1 Knapsack DP — Suggested Kit (`core/loadout_optimizer.py`)

- **Mapping:** item = gadget (taken at most once → "0/1"), weight = **energy cost**,
  value = **mission usefulness**, capacity = **8**.
- **Table:** `best[i][c]` = best result using only the first `i` gadgets with at most `c`
  energy. Recurrence: skip gadget `i` → `best[i-1][c]`; take it (if it fits) →
  `best[i-1][c-cost] + usefulness`. Each cell stores the pair `(usefulness, -energy)`,
  compared like tuples.
- **Traceback:** start at `best[n][8]` and walk up the rows: if taking gadget `i` still
  reaches the cell's value, it was taken and the remaining capacity drops by its cost.
- **Tie-break (tested):** (1) highest usefulness, (2) then the **lower energy cost**,
  (3) then the alphabetically first sorted ID tuple. Rule 2 comes from the `-energy` part
  of the pair; rule 3 from placing gadgets in the table in reverse alphabetical order so
  the traceback decides the alphabetically first gadget first and takes it whenever possible.
- **Edge cases:** empty list, capacity 0, gadgets that never fit → empty kit with zeros.
- **Complexity:** O(n × C) = 6 × 9 cells here. Brute force is O(2ⁿ); my Experiment 6
  Branch and Bound is also exponential in the worst case but prunes with a fractional bound.

**Worked example — The Archive** (usefulness: scanner 6, decoy 3, boots 2, repair 2, lens 7,
shield 3; costs 3, 4, 3, 2, 2, 5). Usefulness-only DP table, gadgets in catalogue order:

| i (gadget added) | c=0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| 0 (none) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 scanner (3, 6) | 0 | 0 | 0 | 6 | 6 | 6 | 6 | 6 | 6 |
| 2 decoy (4, 3) | 0 | 0 | 0 | 6 | 6 | 6 | 6 | 9 | 9 |
| 3 boots (3, 2) | 0 | 0 | 0 | 6 | 6 | 6 | 8 | 9 | 9 |
| 4 repair (2, 2) | 0 | 0 | 2 | 6 | 6 | 8 | 8 | 9 | 10 |
| 5 lens (2, 7) | 0 | 0 | 7 | 7 | 9 | 13 | 13 | **15** | **15** |
| 6 shield (5, 3) | 0 | 0 | 7 | 7 | 9 | 13 | 13 | 15 | **15** |

The best usefulness is **15**, and it is already reached with only **7** energy
(`best[6][7] = 15`). Two kits give 15: **scanner + repair + lens (7 energy)** and
**scanner + boots + lens (8 energy)**. The tie-break picks the cheaper one, so the
Suggested Kit for the Archive is scanner + repair + lens, readiness 100%.

Other missions: Gallery → scanner + boots + repair (15 @ 8) — and because the boots are
in it, the best route drops from 17 to 13 (this is the link between the two algorithms).
Relay → decoy + repair + lens (14 @ 8).

### 8.3 Scoring (`core/scoring.py`)

`500 (success) + 200 (objective) + 100 (extraction) + round(150 × chosen ÷ best)
− 5 × effort − 50 (alert without decoy)`, never below 0.
Example: Gallery, Suggested Kit, optimal routes: effort 13 + 15 = 28 →
500 + 200 + 100 + 150 − 140 = **810** (a test checks this; the debrief, the saved
record and the history table show the same number).
Ranks (same thresholds in Python and in `HP_RANK_TITLE`): Phantom ≥ 800, Specialist ≥ 650,
Operative ≥ 450, Rookie below.

## 9. Database design

| SQLite (default) | Oracle | Columns / notes |
|---|---|---|
| `players` | `HP_PLAYERS` | player_id (PK, autoincrement / identity), player_name UNIQUE NOT NULL, created_at |
| `missions` | `HP_MISSIONS` | mission_id PK ('archive' ...), mission_name, difficulty — seeded with `INSERT OR IGNORE` / `MERGE` |
| `mission_runs` | `HP_MISSION_RUNS` | run_id PK, player_id FK, mission_id FK, result CHECK SUCCESS/ABANDONED, score CHECK ≥ 0, moves, route_cost, kit_summary, alert_triggered CHECK Y/N, played_at |
| — | `HP_RUN_AUDIT` + `HP_AUDIT_SEQ` | filled by trigger `HP_TRG_RUN_AUDIT` (AFTER INSERT ... FOR EACH ROW, uses `:NEW`, `USER`, `SYSDATE`) |

Relationships: one player → many runs; one mission → many runs.

Oracle PL/SQL objects (`database/setup_oracle.sql`, works on 26ai and 19c):

- **`HP_SAVE_RUN`** (8 IN + `p_run_id OUT`): validates input (named exceptions →
  `RAISE_APPLICATION_ERROR -20001/-20003/-20004`), checks the mission with
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

Both repositories use only parameterised queries (`?` in SQLite, `:player` / `:lim` binds
in Oracle). Player text is never concatenated into SQL.

## 10. From my college worksheets to this game

| Worksheet / notes | Used in the game as |
|---|---|
| DAA Exp 4 — Dijkstra (matrix, O(V²)) | Game uses a heap version. The matrix version is kept as `dijkstra_matrix()` in `tests/reference_algorithms.py`, with the **indentation bug fixed** (the break / visited / relaxation lines were inside the min-search loop, and the `new_distance` check was not under `graph[current][v] > 0`). A test compares both versions on every pair of tiles of every map. |
| DAA Exp 6 — 0/1 Knapsack Branch & Bound | Game uses DP. My `knapsack_bb()` is copied unchanged (only formatting) into the tests; DP, B&B and brute force must agree for all three missions and 200 random cases. |
| DAA Exp 3 — Kruskal's Union-Find | My `find()` (path compression) and `union()` (by rank) prove every walkable tile of each map is in one connected group. |
| DAA Exp 1 — timing with `perf_counter()` | Optional `tools/benchmark_routes.py`: heap vs matrix Dijkstra on growing random grids; a Matplotlib line graph only if Matplotlib is installed, otherwise a table. On this laptop at about 1000 tiles: heap 2.9 ms, matrix 86.5 ms, same costs. |
| Python worksheets 1–5, slides 1.x | Classes with `__init__`, dictionary keyed by ID with `in` checks (gadgets, missions), `.strip()` + default + range checks (player name), tuples for positions, sets for sealed tiles, default arguments, docstrings, inheritance + overriding (`BaseScreen`, `BaseRepository`). |
| Tkinter slides 3.1–3.5 | `Tk()`, `geometry()`, `title()`, `mainloop()`, `Canvas` shapes, `grid`/`pack`, `Menu`, `bind()`. The `keyboard` / `pynput` modules from slide 3.4 are **not** used — Tkinter's own `bind()` is the right tool inside a window. |
| PL/SQL Programs 2–6 | 2 explicit cursor → `HP_PRINT_RECENT_RUNS`; 3 function with CASE → `HP_RANK_TITLE`; 4 SELECT INTO / NO_DATA_FOUND → `HP_SAVE_RUN`; 5 user-defined exceptions → validation in `HP_SAVE_RUN`; 6 sequence + audit trigger → `HP_AUDIT_SEQ` + `HP_TRG_RUN_AUDIT`. |

## 11. Testing

```bash
python -m unittest discover -s tests -v
```

Last result: **96 tests, OK** — pathfinding 17, missions 12, loadout optimizer 13,
scoring 7, game engine 25, SQLite repository 11, Oracle repository (offline, fake
connection) 7, validation 4.

`tests/manual_oracle_check.py` is the real Oracle check (run by hand; it rolls back its data).

## 12. Manual test checklist (repeat before the demo)

| # | Check | ✓ |
|---|---|---|
| 1 | `python app.py` opens the menu; the window title is "Heist Planner Game \| Mission Strategy Simulator" | ☐ |
| 2 | A bad name like `a<b>` shows an inline message; an empty name becomes "Agent" | ☐ |
| 3 | Mission Select: clicking a card shows its briefing; Back works | ☐ |
| 4 | Preparation (Gallery): Suggested Kit ticks Pocket Scanner + Mobility Boots + Repair Module, energy 8 / 8, readiness 100% | ☐ |
| 5 | Ticking one more gadget is refused ("Not enough energy — 0 units left...") | ☐ |
| 6 | Gallery **without** boots: Plan Route shows "17 steps, effort 17" (the long loop) | ☐ |
| 7 | Gallery **with** boots: Plan Route shows "9 steps, effort 13" (straight through the fields) | ☐ |
| 8 | Move Next Step (Space) moves one tile; Auto Travel (A) animates; Stop (Esc) pauses | ☐ |
| 9 | Collect Objective is only enabled on the objective tile; collecting switches the target to extraction | ☐ |
| 10 | Reaching extraction before collecting does **not** finish the mission | ☐ |
| 11 | Relay: collecting the key shows "ALERT — relay gate sealed", a red X on the gate, and a new route (effort 19) | ☐ |
| 12 | Relay: Trigger Alert before collecting also seals the gate and re-plans | ☐ |
| 13 | Extraction with the objective opens the Debrief; Gallery + Suggested Kit + best routes = 810 | ☐ |
| 14 | History shows the new record exactly once, with the same score and a rank | ☐ |
| 15 | Restart Mission resets moves, effort and reopens the gate | ☐ |
| 16 | Return to Menu after moving asks "Abandon mission?"; Yes saves one ABANDONED row | ☐ |
| 17 | About Project shows the database mode | ☐ |
| 18 | (Oracle) `DATABASE_BACKEND=oracle` + `.env` → About shows "Oracle PL/SQL connected"; wrong password → friendly notice and SQLite fallback | ☐ |

## 13. Limitations and future work

- Oracle mode was tested live on Oracle AI Database 26ai Free only (Section 6). The 19c
  compatibility of `setup_oracle.sql` comes from avoiding 23ai-only syntax; it was not run on
  a real 19c server (FreeSQL.com / college server).
- Three fixed maps; no map editor, no enemy AI, no sound (out of scope by design).
- On this laptop's 1280×720 (scaled) screen the window is sized to the screen (about 1180×630)
  instead of the planned 1180×760; all screens were checked at 1000×620.
- Possible future work: more missions loaded from JSON, a replay of the last route, an
  Oracle view for leaderboards.
