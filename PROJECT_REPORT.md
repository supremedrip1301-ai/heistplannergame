# Project Report — Heist Planner Game: Mission Strategy Simulator

**Student:** Anshul Kaushik · MCA (AI & ML), Chandigarh University
**Subjects connected:** Design and Analysis of Algorithms, Python Programming, Database (PL/SQL)
**Date:** 27 October 2026

---

## 1. Aim

To design and build a desktop strategy-puzzle game in Python Tkinter in which two
classic algorithms — **Dijkstra's shortest path** and **0/1 Knapsack (dynamic
programming)** — run inside the gameplay and change what happens, with results stored
in SQLite and, optionally, in Oracle Database through PL/SQL stored procedures.

## 2. Problem statement

Algorithm exercises are usually shown as console programs that print a distance array
or a maximum profit. The problem here is to use the same algorithms *naturally*: the
player should experience route guidance, equipment recommendations and a changing map,
without seeing textbook terms on the screen, while the code, tests and documents still
explain exactly which algorithm runs and why it is correct.

## 3. Objectives

1. Build a complete, playable Tkinter game with three missions, a Canvas map, visible
   step-by-step and animated movement, objective collection and extraction.
2. Implement Dijkstra with a binary heap on a grid graph and use it for every route,
   including rerouting after a gate is sealed.
3. Implement 0/1 Knapsack with a DP table and traceback for the Suggested Kit, with a
   documented tie-break rule.
4. Keep the game logic independent from the UI and from the database.
5. Save results exactly once in SQLite; provide a genuine Oracle PL/SQL backend with an
   automatic fallback to SQLite.
6. Verify everything with automated `unittest` tests, including cross-checks against my
   own DAA worksheet programs.
7. (Upgrade, 30 Oct 2026) Make the game a real challenge for experienced players: patrol
   drones, keycards and locked doors, lasers and hacking terminals, Pro mode and three new
   missions - while keeping every route and every puzzle answer computed by the same
   algorithms.

## 4. Scope

**In scope:** single player, six fixed maps (12 columns, up to 11 rows), six gadgets,
capacity 8, one deterministic alert event, deterministic patrol drones, keycards, doors,
lasers, two terminal puzzle types, Pro mode, scoring and ranks, history and statistics,
SQLite (default) and Oracle (optional) storage.
**Out of scope (by design):** chasing / learning enemy AI, multiplayer, accounts, sound,
images, internet, third-party game engines.

## 5. Features

- Main menu with validated operative name, How to Play and About pages.
- Mission cards with drawn thumbnails and a briefing.
- Equipment preparation: energy bar, usefulness bars, readiness %, Suggested Kit,
  over-capacity refusal.
- Gameplay: Plan Route, Move Next Step, Auto Travel (`after()`), Stop, Collect Objective,
  Trigger Alert (Relay), Restart, Return to Menu; keyboard shortcuts P / Space / A / Esc /
  C and arrow keys.
- Relay alert: seals the gate, invalidates the route, re-plans from the current tile.
- Hard missions (Vault, Lab, Penthouse): patrol drones with vision, Wait [W], keycards,
  locked doors, lasers, hacking terminals [H] with Power Relay and Cargo Lock puzzles,
  Signal Decoy freeze [D], Scanner preview, Shield second chance, Lens hint, Repair retry.
- Pro mode: no route guidance, +25% score; caught runs are recorded as CAUGHT.
- Debrief with score breakdown and rank; save-exactly-once; abandoned runs recorded.
- Mission history with statistics (player / all players).

## 6. Technology stack

Python 3.11+ standard library only for the game: `tkinter`, `tkinter.ttk`, `Canvas`,
`heapq`, `dataclasses`, `sqlite3`, `json`, `logging`, `pathlib`, `unittest`.
Optional: Oracle AI Database 26ai Free (compatible with 19c), PL/SQL, `python-oracledb`
in Thin mode.

## 7. Architecture

```
                   ┌─────────────────────── ui (Tkinter) ───────────────────────┐
                   │ MainWindow ── screens: Menu, Select, Preparation, Gameplay, │
                   │      Terminal, Debrief, History, HowTo, About (BaseScreen)  │
                   └───────┬──────────────────────────────────────┬──────────────┘
                           │ calls                                │ save / load
                           ▼                                      ▼
      ┌──────────── core (no Tkinter) ────────────┐   ┌──── database ─────────────┐
      │ game_engine.MissionRun (state machine)    │   │ BaseRepository            │
      │   ├── pathfinding  (Dijkstra, heapq)      │   │   ├── SQLiteRepository    │──► data/heist_planner.db
      │   ├── state_planner (Dijkstra on states)  │   │                           │
      │   ├── drones / puzzles                    │   │                           │
      │   ├── scoring      (score, ranks)         │   │   └── OracleRepository    │──► HP_SAVE_RUN, HP_GET_STATS,
      │   └── missions / gadgets (data)           │   │ database_manager (fallback)│    HP_RANK_TITLE (PL/SQL)
      │ loadout_optimizer (0/1 Knapsack DP)       │   └───────────────────────────┘
      └───────────────────────────────────────────┘
```

UI → engine → algorithms, and UI → repository → SQLite / Oracle. The engine never
imports Tkinter and scoring never imports the optimiser, so each part can be tested alone.

## 8. Program logic (algorithm design)

### 8.1 Dijkstra (route guidance)

- Vertices: walkable tiles `(row, col)`. Edges: up/right/down/left steps into walkable,
  unsealed neighbours. Edge cost = cost of the **entered** tile (floor 1, static field 4,
  or 2 with Mobility Boots).
- `heapq` stores `(cost, row, col)`; stale entries are skipped; the search stops when the
  goal is popped; the path is rebuilt from the `previous` dictionary.
- Unreachable or invalid goal → `RouteResult([], None, False)`, never an exception.
- **Time:** O((V + E) log V) with E ≤ 4V. **Space:** O(V).
- Worksheet version (Exp 4): adjacency matrix + linear scan, O(V²) time and O(V²) space.

### 8.2 0/1 Knapsack DP (Suggested Kit)

- Weight = energy cost, value = mission usefulness, capacity = 8.
- `best[i][c]` holds the pair `(usefulness, −energy)`; recurrence
  `best[i][c] = max(best[i−1][c], best[i−1][c−w] + (v, −w))`; traceback recovers the kit.
- Tie-break: highest usefulness → lower energy → alphabetically first ID tuple.
- **Time and space:** O(n × C) = 6 × 9 cells. Brute force: O(2ⁿ) = 64 subsets.
  Branch & Bound (Exp 6): exponential worst case, prunes with a fractional upper bound.

### 8.3 Dijkstra on a state graph (hard missions)

- Vertex = `(row, col, drone_clock, has_key, freeze_left)`. Drones are periodic, so the
  clock is stored modulo the LCM of all patrol lengths (Vault 16, Lab 24, Penthouse 8).
- Edges = one turn: four moves (cost of the entered tile) or Wait (cost 1); edges that end
  in a drone's view, walk through a drone, or enter a locked door without the keycard or
  an active laser are removed.
- Same heap Dijkstra; at most 132 × 24 × 2 × 4 ≈ 25,000 states, a few milliseconds.
- Checked against the tile Dijkstra (old missions, identical costs) and Bellman-Ford
  (new missions, identical costs); every planned path is replayed to prove it is unseen.

### 8.4 Terminal puzzles

- Power Relay: the minimum path load in a 6 × 6 grid, computed with `find_shortest_path`;
  cross-checked by a brute-force DFS over all simple paths.
- Cargo Lock: the maximum credits within a mass limit, computed with the Knapsack DP;
  cross-checked by brute force over all subsets.
- Puzzles where a greedy choice already gives the best answer are rejected by the generator.

### 8.5 State machine

`PLANNING → IN_PROGRESS → OBJECTIVE_SECURED → COMPLETED`, plus `ABANDONED`, `NO_ROUTE` and
`CAUGHT`. Every move goes through `MissionRun.step()`, which refuses walls, sealed gates,
jumps and diagonal moves. Restart increases a run token so an old animation callback can
never move the character of a new run.

### 8.6 Scoring

`500 + 200 + 100 + round(150 × chosen ÷ best) + high-risk bonus − 5 × effort − 50 (alert
without decoy)`, then +25% in Pro mode, clamped at 0. High-risk bonus: Vault 150, Lab 350,
Penthouse 250. Ranks: Phantom ≥ 800, Specialist ≥ 650, Operative ≥ 450, else Rookie.

## 9. Database design

**Tables** (SQLite names / Oracle names): `players` / `HP_PLAYERS`, `missions` /
`HP_MISSIONS`, `mission_runs` / `HP_MISSION_RUNS`, and in Oracle also `HP_RUN_AUDIT`.

**Keys and relationships:** `player_id` and `run_id` are surrogate keys (SQLite
AUTOINCREMENT, Oracle `GENERATED BY DEFAULT AS IDENTITY`). `mission_runs.player_id` →
`players`, `mission_runs.mission_id` → `missions` (one-to-many each). `player_name` is
UNIQUE. CHECK constraints: result ∈ {SUCCESS, ABANDONED, CAUGHT}, score ≥ 0,
alert ∈ {Y, N}, pro_mode ∈ {Y, N}. Old SQLite save files are migrated once (table rebuilt,
every row copied) because SQLite cannot alter a CHECK constraint.

**PL/SQL objects:** procedure `HP_SAVE_RUN` (validation with named exceptions and
`RAISE_APPLICATION_ERROR`, `SELECT ... INTO` + `NO_DATA_FOUND`, find-or-create player,
`RETURNING ... INTO` OUT parameter, **no COMMIT**); procedure `HP_GET_STATS` (4 OUT
parameters, `NVL` so no NULLs); function `HP_RANK_TITLE` (CASE); procedure
`HP_PRINT_RECENT_RUNS` (explicit cursor); sequence `HP_AUDIT_SEQ` + trigger
`HP_TRG_RUN_AUDIT` (AFTER INSERT FOR EACH ROW using `:NEW`).

Python commits after a successful procedure call and rolls back on any error, so the
transaction has one clear owner.

## 10. Procedure (how it was built)

1. Phase 1 — configuration, `.env` loader, logging, heap Dijkstra, mission data, my
   worksheet reference algorithms, pathfinding and mission tests.
2. Phase 2 — scoring, the `MissionRun` engine and its tests, styles, the main window and
   all screens, map drawing, Auto Travel with `after()`, alert rerouting, debrief.
3. Phase 3 — DP optimiser with brute-force and Branch & Bound cross-checks, preparation
   screen, gadget effects.
4. Phase 4 — SQLite repository, backend manager with fallback, save-once, history screen.
5. Phase 5 — Oracle scripts (user, schema, procedures, manual test), Oracle repository,
   offline tests, manual check script.
6. Phase 6 — layout checks at 1180×630 and 1000×620, batch files, scripted live
   walkthroughs of the real window.
7. Phase 7 — README, this report, viva questions, and the optional benchmark
   `tools/benchmark_routes.py` (heap 2.9 ms vs matrix 86.5 ms at about 1000 tiles, same costs).
8. Phase 8 (upgrade) — drones, state-graph planner, puzzles, three new missions (verified
   with the planner; the Penthouse patrols chosen by an exhaustive search over drone
   triples), engine rules, new screens, database changes, live re-tests.

Progress was checkpointed after every task in `PROGRESS.md`, `progress_state.json` and
`SESSION_LOG.md`, with a git commit after each phase.

## 11. Output / testing results

**Automated tests** (`python -m unittest discover -s tests -v`, last run 30 Oct 2026):
**157 tests, 0 failures, 0 errors.**

| Test file | Tests | What it proves |
|---|---|---|
| test_pathfinding | 17 | cheaper-longer route chosen, walls never crossed, start = goal, no route, invalid input, sealed tile, all Section 8 numbers, heap = my matrix Dijkstra on every pair of tiles |
| test_missions | 18 | rectangular maps, one S/O/E, one gate (Relay), border walls, Union-Find connectivity, gadget data; hard missions: drones on walkable tiles, safe start, every leg solvable and needs timing, keycard + terminal required, home route at every clock, expected kits |
| test_loadout_optimizer | 13 | expected kits, Archive tie-break (7 over 8 energy), capacity rules, edge cases, DP = brute force = Branch & Bound (3 missions + 200 random cases) |
| test_scoring | 10 | Gallery = 810, clamp at 0, decoy cancels penalty, rank thresholds, high-risk + Pro bonus, old breakdown unchanged |
| test_game_engine | 25 | distant collect refused, walls/gate refused, early exit not a win, full missions, alert reroute 19, restart reset, save once, abandoned record |
| test_hard_missions | 19 | planner completes all three hard missions unseen, Wait, caught, Shield, Decoy freeze, Scanner preview, doors/lasers refuse, keycard, lockout, Repair, Lens, restart, Pro mode |
| test_drones | 12 | patrol cycles, facing, vision blocked by walls/doors, detection incl. swap and freeze |
| test_state_planner | 10 | = tile Dijkstra on old maps, = Bellman-Ford with drones / keycards / freeze, waits, no-route |
| test_puzzles | 9 | Power Relay = brute-force DFS, Cargo = brute force, greedy always beaten, bad answers rejected |
| test_sqlite_repository | 13 | fresh DB zeros, save → history → stats, filters, restart persistence, invalid rows rejected, injection text stored safely, engine save path saves once, fallback, CAUGHT + pro_mode, old save file upgraded |
| test_oracle_repository | 7 | (offline, fake connection) callproc arguments, commit / rollback, stats, friendly errors, SYS/SYSTEM refused |
| test_validation | 4 | player-name rules |

**Verified game numbers:** Archive 14 / 8; Gallery 17 (13 with boots, direct 21) / 15;
Relay 13 / 11 → 19 after the alert. Kits: Archive 15 @ 7, Gallery 15 @ 8, Relay 14 @ 8.

**Live runs of the real window** (scripted, on this laptop): Gallery with Suggested Kit
finished with score **810** (24 moves, effort 28), saved once and shown in history as
"Phantom"; Relay with Scanner + Shield finished with **697** after the alert reroute;
Archive with an empty kit **690**; an abandoned Relay run was saved once as ABANDONED;
25 of 25 interface checks passed (name validation, shortcuts, Stop, Restart, early alert,
history toggle).

**Hard missions, live window (30 Oct 2026):** Vault **880** (effort 44), Lab **830**
(effort 94, keycard, Power Relay with the Repair Module absorbing one wrong answer),
Penthouse **825** (effort 75, Cargo Lock); a Pro-mode Vault run walking the plain shortest
path was spotted by the "Shaft guard" and saved once as CAUGHT; all checks also passed at
1000 × 620, and the original 25-check walkthrough still passes.

**Oracle re-verified live on 30 Oct 2026** after adding CAUGHT / PRO_MODE and the three
missions: 15 objects VALID, `oracle_manual_test.sql` including a CAUGHT Pro run on the
Vault, `manual_oracle_check.py` ALL CHECKS PASSED (the three earlier game rows were backed
up and restored).

**Oracle (live, 27 Oct 2026, Oracle AI Database 26ai Free 23.26.3, FREEPDB1, Thin mode):**
`setup_oracle.sql` ran three times without errors and all 15 objects are VALID;
`oracle_manual_test.sql` gave the expected saves, statistics (2 / 1 / 810 / 810), ORA-20001
and ORA-20002 rejections, rank titles, audit rows and cursor report;
`tests/manual_oracle_check.py` printed ALL CHECKS PASSED; and the real game in Oracle mode
saved Gallery (810) and Relay (790) through `HP_SAVE_RUN` and read them back in History.

## 12. Limitations

- Oracle tested live on 26ai Free only; 19c compatibility is by design, not run on a 19c server.
- Fixed maps; drones follow fixed patrols (no chasing AI); no sound.

## 13. Future improvements

Missions loaded from JSON files, a map editor, a replay of the chosen route, an Oracle
leaderboard view.

## 14. What I learned

- How a tile map becomes a graph, and why Dijkstra needs non-negative costs.
- Why a heap beats a linear scan on sparse graphs, and how to rebuild the path.
- How a DP table plus traceback answers "which items", not just "how much", and how to
  make ties deterministic.
- Event-driven GUI programming: `after()` instead of `sleep()`, cancelling callbacks,
  keeping state in one engine object.
- Clean separation of UI, logic and storage through inheritance (`BaseScreen`,
  `BaseRepository`).
- Writing PL/SQL that reports errors to the caller instead of hiding them, and letting the
  application own the transaction.
- That "where am I" can mean more than a position: adding time, keys and gadget state to
  the vertex turns a hard timing puzzle into an ordinary shortest-path problem.
- Why greedy fails for shortest paths and knapsack - shown by puzzles built so that the
  greedy answer is always wrong.

## 15. Conclusion

The project delivers a complete, playable Tkinter game in which Dijkstra and 0/1
Knapsack really drive the gameplay: boots chosen by the Knapsack change the Dijkstra
route (Gallery 17 → 13), and the Relay alert forces a visible reroute (11 → 19). The hard
missions extend the same Dijkstra to a state graph that plans around patrol drones,
keycards and decoys, and the terminal puzzles are judged by Dijkstra and the Knapsack DP.
The game runs with zero installs in SQLite mode, has a genuine PL/SQL backend for Oracle,
and is backed by 157 passing tests that cross-check my own worksheet algorithms and
Bellman-Ford.
