# Project Report — Heist Planner Game: Mission Strategy Simulator

**Student:** Anshul Kaushik · MCA (AI & ML), Chandigarh University
**Subjects connected:** Design and Analysis of Algorithms, Python Programming, Database (PL/SQL)
**Date:** 30 October 2026

---

## 1. Aim

To design and build a desktop stealth-puzzle game in Python Tkinter in which classic
algorithm runs inside the gameplay and decides what happens: **Dijkstra's shortest path**
(on a tile graph and on a state graph) plans every safe route and judges the Power Relay
puzzle. Results are stored in SQLite and, optionally, in Oracle Database through PL/SQL
stored procedures.

## 2. Problem statement

Algorithm exercises are usually console programs that print a distance array or a maximum
profit. The problem here is to use the same algorithms *naturally*: the player should
experience route guidance around moving guards, locked doors and hacking puzzles, without
seeing textbook terms on the screen, while the code, tests and documents still explain
exactly which algorithm runs and why it is correct.

## 3. Objectives

1. Build a complete, playable Tkinter game with three missions, a Canvas map, visible
   step-by-step and animated movement, objective collection and extraction.
2. Model patrol drones that move every turn, and plan routes that are never seen, by
   running Dijkstra on a state graph (tile, drone clock, keycard).
3. Use Dijkstra as the judge of the terminal puzzle, built so that a greedy answer never
   works.
4. Keep the game logic independent from the UI and from the database.
5. Save results exactly once in SQLite; provide a genuine Oracle PL/SQL backend with an
   automatic fallback to SQLite.
6. Verify everything with automated `unittest` tests, including cross-checks against my
   own DAA worksheet programs and against Bellman-Ford.

## 4. Scope

**In scope:** single player, three fixed maps (12 columns, 11 rows), ten deterministic patrol
drones, keycards, locked doors, laser barriers, a terminal puzzle, Pro mode, scoring
and ranks, history and statistics, SQLite (default) and Oracle (optional) storage.
**Out of scope (by design):** chasing / learning enemy AI, multiplayer, accounts, sound,
images, internet, third-party game engines.

**Scope change (30 Oct 2026):** the first version also had three introductory missions
(Archive, Gallery, Relay), an equipment-preparation screen with a Knapsack-based "Suggested
Kit", and gadgets. On my decision these were removed to keep the game focused on the three
puzzle missions. The three old maps are kept as test grids for the Dijkstra tests. Later
the same day the remaining Knapsack use (a "Cargo Lock" puzzle in the Penthouse) was also
removed, so that **Dijkstra is the only algorithm in the game**; the Penthouse terminal is
now a 7 × 7 Power Relay.

## 5. Features

- Main menu with validated operative name, How to Play and About pages.
- Mission cards with drawn thumbnails, a briefing, a Pro mode switch and Start Mission.
- Gameplay: Plan Route, Move Next Step, Auto Travel (`after()`), Stop, Wait, Collect
  Objective, Hack Terminal, Restart, Return to Menu; keyboard shortcuts P / Space / A / Esc /
  W / C / H and arrow keys.
- Patrol drones with drawn vision cones and an amber preview of the next turn; caught runs
  fail and are recorded as CAUGHT.
- Keycards and locked doors, laser barriers, terminals with the Power Relay puzzle (6 × 6 / 7 × 7).
- Pro mode: no route guidance and no preview, +25% score.
- Debrief with score breakdown and rank; save-exactly-once; abandoned runs recorded.
- Mission history with statistics (player / all players).

## 6. Technology stack

Python 3.11+ standard library only for the game: `tkinter`, `tkinter.ttk`, `Canvas`,
`heapq`, `math`, `dataclasses`, `sqlite3`, `json`, `logging`, `pathlib`, `unittest`.
Optional: Oracle AI Database 26ai Free (compatible with 19c), PL/SQL, `python-oracledb`
in Thin mode.

## 7. Architecture

```
                   ┌─────────────────────── ui (Tkinter) ───────────────────────┐
                   │ MainWindow ── screens: Menu, Select, Gameplay, Terminal,    │
                   │               Debrief, History, HowTo, About (BaseScreen)   │
                   └───────┬──────────────────────────────────────┬──────────────┘
                           │ calls                                │ save / load
                           ▼                                      ▼
      ┌──────────── core (no Tkinter) ────────────┐   ┌──── database ─────────────┐
      │ game_engine.MissionRun (state machine)    │   │ BaseRepository            │
      │   ├── state_planner (Dijkstra on states)  │   │   ├── SQLiteRepository    │──► data/heist_planner.db
      │   │     └── drones (patrols, vision)      │   │   └── OracleRepository    │──► HP_SAVE_RUN, HP_GET_STATS,
      │   ├── puzzles ── pathfinding (Dijkstra)   │   │ database_manager (fallback)│    HP_RANK_TITLE (PL/SQL)
      │   │                                       │   └───────────────────────────┘
      │   ├── scoring  (score, ranks)             │
      │   └── missions (maps, drones, briefings)  │
      └───────────────────────────────────────────┘
```

UI → engine → algorithms, and UI → repository → SQLite / Oracle. The engine never imports
Tkinter and scoring only receives numbers, so each part can be tested alone.

## 8. Program logic (algorithm design)

### 8.1 Dijkstra on a tile grid

- Vertices: walkable tiles `(row, col)`. Edges: up/right/down/left steps into walkable
  neighbours. Edge cost = cost of the **entered** tile (floor 1, static field 4).
- `heapq` stores `(cost, row, col)`; stale entries are skipped; the search stops when the
  goal is popped; the path is rebuilt from the `previous` dictionary.
- Unreachable or invalid goal → `RouteResult([], None, False)`, never an exception.
- **Time:** O((V + E) log V) with E ≤ 4V. **Space:** O(V).
- Worksheet version (Exp 4): adjacency matrix + linear scan, O(V²) time and space.

### 8.2 Dijkstra on a state graph (route guidance)

- Vertex = `(row, col, drone_clock, has_key)`. Drones are periodic, so the clock is stored
  modulo the LCM of all patrol lengths (Vault 16, Lab 24, Penthouse 8).
- Edges = one turn: four moves (cost of the entered tile) or Wait (cost 1); edges that end
  in a drone's view, walk through a drone, or enter a locked door without the keycard or
  an active laser are removed.
- Same heap Dijkstra; at most 132 × 24 × 2 ≈ 6,300 states, a few milliseconds.
- Checked against the tile Dijkstra (no drones: identical costs) and Bellman-Ford (with
  drones: identical costs); every planned path is replayed to prove it is never seen.

### 8.3 Terminal puzzle

- **Power Relay:** the minimum path load in a 6 × 6 (Lab) or 7 × 7 (Penthouse) grid of
  numbers, computed with `find_shortest_path` (each cell is a vertex, its number the cost of
  entering it); cross-checked by a brute-force DFS over all simple paths.
- Grids where a greedy walk (always the cheaper next cell) already gives the minimum are
  rejected by the generator.

### 8.4 State machine

`PLANNING → IN_PROGRESS → OBJECTIVE_SECURED → COMPLETED`, plus `ABANDONED`, `NO_ROUTE` and
`CAUGHT`. Every move and Wait goes through `MissionRun.step()`, which refuses walls, locked
doors, active lasers, jumps and diagonal moves, advances the drone clock and checks for
detection. Restart increases a run token so an old animation callback can never move the
character of a new run.

### 8.5 Scoring

`500 + 200 + 100 + high-risk bonus − 5 × effort`, then +25% in Pro mode, clamped at 0.
High-risk bonus: Vault 300, Lab 500, Penthouse 500. Ranks: Phantom ≥ 800, Specialist ≥ 650,
Operative ≥ 450, else Rookie.

## 9. Database design

**Tables** (SQLite names / Oracle names): `players` / `HP_PLAYERS`, `missions` /
`HP_MISSIONS`, `mission_runs` / `HP_MISSION_RUNS`, and in Oracle also `HP_RUN_AUDIT`.

**Keys and relationships:** `player_id` and `run_id` are surrogate keys (SQLite
AUTOINCREMENT, Oracle `GENERATED BY DEFAULT AS IDENTITY`). `mission_runs.player_id` →
`players`, `mission_runs.mission_id` → `missions` (one-to-many each). `player_name` is
UNIQUE. CHECK constraints: result ∈ {SUCCESS, ABANDONED, CAUGHT}, score ≥ 0,
alert ∈ {Y, N}, pro_mode ∈ {Y, N}. `kit_summary` and `alert_triggered` are legacy columns
from the first version, kept so old records stay readable. Old SQLite save files are
migrated once (table rebuilt, every row copied) because SQLite cannot alter a CHECK
constraint.

**PL/SQL objects:** procedure `HP_SAVE_RUN` (validation with named exceptions and
`RAISE_APPLICATION_ERROR`, `SELECT ... INTO` + `NO_DATA_FOUND`, find-or-create player,
`RETURNING ... INTO` OUT parameter, **no COMMIT**); procedure `HP_GET_STATS` (4 OUT
parameters, `NVL` so no NULLs); function `HP_RANK_TITLE` (CASE); procedure
`HP_PRINT_RECENT_RUNS` (explicit cursor); sequence `HP_AUDIT_SEQ` + trigger
`HP_TRG_RUN_AUDIT` (AFTER INSERT FOR EACH ROW using `:NEW`).

Python commits after a successful procedure call and rolls back on any error, so the
transaction has one clear owner.

## 10. Procedure (how it was built)

1. Phases 1–7 (27 Oct 2026) — configuration, heap Dijkstra, first three missions, my
   worksheet reference algorithms, engine, screens, Knapsack Suggested Kit, SQLite, Oracle
   scripts and repository, layout checks, documentation.
2. Phase 8 (30 Oct 2026) — patrol drones, state-graph planner, terminal puzzles, three
   puzzle missions (verified with the planner; the Penthouse patrols chosen by an exhaustive
   search over drone triples), Pro mode, CAUGHT / PRO_MODE in both databases.
3. Phase 9 (30 Oct 2026) — focus on the three puzzle missions: preparation screen, gadgets
   and the first three missions removed; tests and documents updated; Oracle re-checked live.
4. Phase 10 (30 Oct 2026) — Dijkstra only: the 0/1 Knapsack and the Cargo Lock removed; the
   Penthouse terminal became a 7 × 7 Power Relay.

Progress was checkpointed after every task in `PROGRESS.md`, `progress_state.json` and
`SESSION_LOG.md`, with a git commit after each phase.

## 11. Output / testing results

**Automated tests** (`python -m unittest discover -s tests -v`, last run 30 Oct 2026):
**114 tests, 0 failures, 0 errors.**

| Test file | Tests | What it proves |
|---|---|---|
| test_game_engine | 26 | basic rules on a plain grid (walls, no jumps, collect only on the objective, early exit not a win, save once, abandon, restart); all three missions completed unseen by the planner with exact effort and score; Wait, caught, next-turn preview, doors and lasers refuse, keycard, lockout, restart re-locks; Pro mode |
| test_pathfinding | 18 | cheaper-longer route chosen, walls never crossed, start = goal, no route, invalid input, blocked tile, classic grid numbers, heap = my matrix Dijkstra on every pair of tiles (test grids and mission maps) |
| test_missions | 13 | rectangular maps, one S/O/E, border walls, Union-Find connectivity, keycard/door/terminal/laser; drones on walkable tiles, safe start, every leg solvable and needs timing, keycard + terminal required, home route at every clock |
| test_sqlite_repository | 13 | fresh DB zeros, save → history → stats, filters, restart persistence, invalid rows rejected, injection text stored safely, engine save path saves once, CAUGHT + pro_mode, old save file upgraded, fallback |
| test_drones | 11 | patrol cycles, facing, vision blocked by walls/doors, detection incl. swap |
| test_state_planner | 9 | = tile Dijkstra without drones, = Bellman-Ford with drones and keycards, waits, no-route |
| test_puzzles | 7 | Power Relay: 6 × 6 and 7 × 7 grids, minimum = brute-force DFS, greedy always beaten, bad answers rejected |
| test_oracle_repository | 7 | (offline, fake connection) callproc arguments, commit / rollback, stats, friendly errors, SYS/SYSTEM refused |
| test_scoring | 6 | Vault example 880, clamp at 0, Pro bonus, rank thresholds |
| test_validation | 4 | player-name rules |

**Planner results** (also checked by tests): Vault effort 44 → **880**; Lab effort 94 →
**830**; Penthouse effort 91 → **845** (all Phantom).

**Live runs of the real window** (scripted, on this laptop, 1180 × 630 and 1000 × 620):
Vault 880 with Play Again; Lab 830 through the keycard and the 6 × 6 Power Relay;
Penthouse 845 through the 7 × 7 Power Relay; a
Pro-mode Penthouse run walking the plain path was spotted by the "Atrium guard" and saved
once as CAUGHT; History showed all three runs with the right mode.

**Oracle (live, Oracle AI Database 26ai Free 23.26.3, FREEPDB1, Thin mode):** on 27 Oct
`setup_oracle.sql` ran three times without errors (15 objects VALID) and real games were
saved through `HP_SAVE_RUN`; on 30 Oct `oracle_manual_test.sql` (Vault, Lab, Penthouse incl.
a CAUGHT Pro run) and `tests/manual_oracle_check.py` (ALL CHECKS PASSED) were run again.

## 12. Limitations

- Oracle tested live on 26ai Free only; 19c compatibility is by design, not run on a 19c server.
- Fixed maps; drones follow fixed patrols (no chasing AI); no sound.
- Two legacy database columns remain from the first version.

## 13. Future improvements

Missions loaded from JSON files, a map editor, a replay of the chosen route, an Oracle
leaderboard view.

## 14. What I learned

- How a tile map becomes a graph, and why Dijkstra needs non-negative costs.
- That "where am I" can mean more than a position: adding time and keys to the vertex turns
  a hard timing puzzle into an ordinary shortest-path problem.
- Why a heap beats a linear scan on sparse graphs, and how to rebuild the path.
- Why a greedy walk fails for shortest paths — shown by puzzles built so that the greedy
  answer is always wrong.
- Event-driven GUI programming: `after()` instead of `sleep()`, cancelling callbacks,
  keeping state in one engine object.
- Clean separation of UI, logic and storage through inheritance (`BaseScreen`,
  `BaseRepository`).
- Writing PL/SQL that reports errors to the caller instead of hiding them, and letting the
  application own the transaction.

## 15. Conclusion

The project delivers a complete, playable Tkinter puzzle game in which Dijkstra really
drives the gameplay: on a state graph of (tile, drone clock, keycard) it finds routes that
dodge every patrol drone, waiting exactly when needed. Dijkstra also judges the
terminal puzzle, which is built so that a greedy answer fails. The game runs
with zero installs in SQLite mode, has a genuine PL/SQL backend for Oracle, and is backed
by 114 passing tests that cross-check my own worksheet algorithms and Bellman-Ford.
