# Viva Questions — Heist Planner Game

Short, beginner-friendly answers. File names point to where the answer lives in the code.

---

## A. Tkinter and the event loop

**1. What does `mainloop()` do?**
It starts Tkinter's event loop: it waits for events (clicks, key presses, timers, window
resizes) and calls the matching callback. The program stays inside `mainloop()` until the
window is closed (`app.py`).

**2. How do you start the game?**
From a terminal in the project folder: `python app.py`. `app.py` only sets up logging,
reads the configuration, creates the database repository, builds the main window and calls
`mainloop()`. All file paths are built from `Path(__file__)`, so
`python D:\DAA\heist_planner_game\app.py` from another folder works too.

**3. Why is there only one window, and how do screens change?**
Every screen is a `ttk.Frame` placed in the same grid cell of one container. Showing a
screen means calling `tkraise()` on it (`ui/main_window.py`, `show()`). No new top-level
windows are opened; only `messagebox` dialogs pop up. Even the terminal puzzle is a screen.

**4. Why `after()` instead of `time.sleep()` for Auto Travel?**
`sleep()` blocks the event loop, so the window would freeze and not even redraw.
`after(220, callback)` asks Tkinter to call the function later and returns immediately,
so the window stays responsive and the character moves one turn every 220 ms
(`ui/gameplay_screen.py`).

**5. How is Auto Travel stopped safely?**
The id returned by `after()` is stored and cancelled with `after_cancel()` in Stop,
Restart, Return to Menu, screen change and window close. Each callback also checks a run
token: Restart increases `run_token`, so a callback from an old run sees a different
token and does nothing.

**6. How are keyboard shortcuts done?**
`root.bind("<KeyPress>", ...)` sends every key to `MainWindow.on_key()`, which forwards it
only to the visible screen (and ignores keys typed in an Entry). The gameplay screen maps
`p`, `space`, `a`, `Escape`, `w`, `c`, `h` and the arrow keys to actions. I did not use the
`keyboard` or `pynput` modules from the slides because they hook the whole operating
system; `bind()` is Tkinter's own tool.

**7. How is the map drawn?**
With `Canvas` primitives only: `create_rectangle` for tiles and drone vision (with a
`stipple` pattern so the floor stays visible), `create_line` for the dashed route and the
laser beams, `create_polygon` for the drones, the objective diamond and the extraction
triangle, `create_oval` for the character and wait badges, `create_text` for labels
(`ui/map_view.py`). The character is drawn last so nothing hides it.

**8. What happens if a callback crashes?**
`root.report_callback_exception` is replaced by a handler that logs the full traceback to
`logs/heist_planner.log` and shows a friendly dialog, so the player never sees a raw
traceback.

## B. Dijkstra and the drones

**9. How is a map a graph?**
Each walkable tile `(row, col)` is a vertex. A step up, right, down or left into a walkable
neighbour is a directed edge. Walls are not vertices. The cost of an edge is the cost of
the tile entered: floor 1, static field 4 (`core/pathfinding.py`).

**10. Why does Dijkstra need non-negative costs?**
Dijkstra assumes that once a vertex is taken out with the smallest distance, no later
path can make it cheaper. A negative edge could make a later path cheaper. All our costs
are positive (1 or 4, and 1 for Wait), so the assumption holds.

**11. Why a heap instead of my O(V²) worksheet version?**
My Exp 4 version scans all vertices to find the closest one each time: O(V) per step,
O(V²) total, plus an O(V²) matrix. A map has at most 4 edges per tile, so most of the
matrix is zeros. With `heapq`, getting the smallest is O(log V), giving O((V + E) log V).
The optional benchmark shows 2.9 ms vs 86.5 ms at about 1000 tiles.

**12. What is a "stale" heap entry and how is the path rebuilt?**
A vertex can be pushed several times; an older, more expensive entry popped later is
skipped (`if d > dist[node]: continue`). Whenever a cheaper way is found,
`previous[vertex]` stores where we came from; after reaching the goal we follow `previous`
back to the start and reverse the list.

**13. How do the patrol drones work?**
Each drone has a fixed patrol made of straight lines (`core/drones.py`). A ping-pong patrol
of n tiles repeats every 2(n − 1) turns, so its position at turn t is `cycle[t mod period]`.
After every player turn (move or Wait) every drone advances one tile. It sees its own tile
and two tiles ahead in the direction it is about to move; walls and locked doors block the
view. Being in a drone's view, or swapping tiles with it, fails the mission.

**14. Why can't the plain tile Dijkstra plan these missions?**
Because whether a tile is safe depends on *when* you are there. The same move is safe at
turn 4 and deadly at turn 5. A vertex that is only a tile cannot express that, so the plain
shortest path walks straight into a drone — a test proves this for every part of every
mission.

**15. What is a "state graph"?**
A graph whose vertices are complete situations, not just places. Here a vertex is
`(row, col, drone_clock, has_key)` (`core/state_planner.py`). Edges are the actions of one
turn: four moves and Wait. A move that would be seen is simply not an edge. Then the
ordinary Dijkstra finds the cheapest safe sequence of moves and waits.

**16. Why is the drone clock stored modulo the LCM of the patrol lengths?**
After LCM(periods) turns every drone is back where it started, so turn 3 and turn 3 + LCM
look exactly the same. Storing `t mod LCM` keeps the graph finite and small (Vault 16,
Lab 24, Penthouse 8 values) — at most 132 × 24 × 2 ≈ 6,300 states.

**17. Is it still Dijkstra? How do you know it is correct?**
Yes: same heap, same stale-entry skip, same `previous` map, positive costs. Tests show its
costs equal Bellman-Ford's on the same graph for every mission, equal the tile Dijkstra
when there are no drones, and every planned path is replayed turn by turn to prove no drone
ever sees it.

**18. Why compare with Bellman-Ford?**
Bellman-Ford relaxes every edge up to V − 1 times, without any priority queue. It is O(V·E),
slow but simple, so it is an independent check: if both algorithms agree on every mission,
the heap version is very unlikely to be wrong.

**19. How does the planner deal with the keycard and the locked door?**
`has_key` is part of the vertex. A door edge only exists when `has_key` is true, and
stepping on the keycard tile sets it. So "fetch the keycard first" is not a special rule:
Dijkstra discovers that the only way through the door goes past the keycard.

**20. What happens when the lasers block every route?**
Lasers are blocked tiles until the terminal is hacked. If no route to the target exists,
the engine plans to the terminal instead and tells the player to hack it.

**21. What bug did you fix in your worksheet Dijkstra?**
In the printed Python version, `if current == -1: break`, `visited[current] = True` and
the relaxation loop were indented inside the loop that searches for the minimum, and
`if new_distance < distance[v]` was not nested under `graph[current][v] > 0`. The fixed copy
is `dijkstra_matrix()` in `tests/reference_algorithms.py`, and a test checks that it gives
exactly the same minimum costs as the heap version for every pair of tiles.

**22. How were the missions checked to be fair?**
Tests check for each mission: drones only patrol walkable tiles, the start is never
watched, every part (to terminal, to objective, home) has a safe route, every part needs
timing, the keycard and the terminal are really required, a route home exists at every
clock value, and my Exp 3 Union-Find shows every walkable tile is connected. The Penthouse
patrols were chosen by an exhaustive search over drone triples.

## C. Terminal puzzles and 0/1 Knapsack

**23. How are the terminal puzzles related to the algorithms?**
Power Relay is a shortest-path problem: its answer is checked with `find_shortest_path`
(Dijkstra). Cargo Lock is a 0/1 Knapsack: its answer is checked with the DP in
`core/loadout_optimizer.py`. The algorithms are the judges, and the player has to match
them by hand.

**24. How is the Cargo Lock a Knapsack problem?**
Crates are items (each taken at most once — "0/1"), mass is the weight, credits are the
value, and the lift limit is the capacity.

**25. Explain the DP table.**
`best[i][c]` is the best result using only the first `i` crates with at most `c` kg. For
each crate: skip it (`best[i−1][c]`) or take it if it fits (`best[i−1][c − mass] +
credits`), and keep the better one. O(n × C) time and space.

**26. How do you know which crates were chosen?**
Traceback: start at `best[n][limit]` and go up row by row. If "take crate i" still produces
the value in the cell, crate i was taken and the capacity drops by its mass.

**27. What is the tie-break rule?**
Most credits first; if equal, the lower total mass; if still equal, the alphabetically
first list of IDs. Cells store `(credits, −mass)` so tuple comparison does the first two
rules. Example in the tests: A + D + E and A + C + E both give 15, but A + D + E weighs 7
instead of 8, so it wins.

**28. DP vs Branch and Bound vs brute force?**
Brute force tries all 2ⁿ subsets. My Exp 6 Branch and Bound explores a tree and prunes
branches whose fractional upper bound cannot beat the best so far — usually fast,
exponential in the worst case. DP is O(n × C). The tests run all three on 30 Cargo puzzles
and 200 random cases and check they agree.

**29. Why can't the player just use a greedy strategy in the puzzles?**
The generator throws away every puzzle where greedy already wins (always step to the
cheaper next cell; always take the best credits-per-kg crate). So the player meets exactly
the situations where greedy fails, which is why DAA uses Dijkstra and DP for these problems.

**30. What happened to the Suggested Kit?**
The first version had an equipment screen where the Knapsack DP recommended gadgets. I
removed that screen, the gadgets and the three introductory missions to keep the game
focused. The same DP still runs in the game — as the judge of the Cargo Lock.

## D. Databases, SQL and PL/SQL

**31. Why SQLite as the default?**
It ships with Python, needs no server and stores everything in one file
(`data/heist_planner.db`), so the game runs with zero installation.

**32. Does SQLite run PL/SQL?**
No. SQLite has no stored procedures. In SQLite mode the same rules (validation,
find-or-create player, rank thresholds) are done in Python. PL/SQL runs only in Oracle mode.

**33. What does `HP_SAVE_RUN` do?**
It validates the inputs, checks the mission exists (`SELECT ... INTO` with
`NO_DATA_FOUND`), finds or creates the player, inserts the run and returns the new ID
through the OUT parameter `p_run_id` (`RETURNING run_id INTO p_run_id`).

**34. What is an OUT parameter and how does Python read it?**
A variable the procedure fills for the caller. In Python I create `cursor.var(int)`, pass
it to `cursor.callproc(...)`, and read it with `.getvalue()`.

**35. Function vs procedure?**
A function returns a value and can be used inside SQL, like `HP_RANK_TITLE(score)` in the
history `SELECT`. A procedure performs actions and returns results through OUT parameters,
like `HP_SAVE_RUN` and `HP_GET_STATS`.

**36. What do the trigger and sequence do?**
`HP_TRG_RUN_AUDIT` fires `AFTER INSERT ... FOR EACH ROW` on `HP_MISSION_RUNS` and copies
`:NEW.run_id`, the player, the score, `USER` and `SYSDATE` into `HP_RUN_AUDIT`, taking the
audit ID from `HP_AUDIT_SEQ.NEXTVAL` — my Program 6 pattern, changed from UPDATE to INSERT.

**37. Why does Python commit instead of the procedure?**
The caller owns the transaction. If the procedure committed, a later failure in the same
operation could leave half-saved data. Python commits only after the call succeeds and
rolls back on any exception.

**38. Why `RAISE_APPLICATION_ERROR` instead of `WHEN OTHERS THEN DBMS_OUTPUT.PUT_LINE`?**
`DBMS_OUTPUT` only prints text on the server; Python would think the save worked.
`RAISE_APPLICATION_ERROR(-20001, ...)` sends a real error that `oracledb` raises as an
exception, which the game logs and turns into a friendly message.

**39. What is Thin mode?**
`python-oracledb` talks to Oracle directly in pure Python (Thin mode), so no Oracle Instant
Client is needed. I never call `oracledb.init_oracle_client()`.

**40. What is SQL injection and how do you prevent it?**
If user text is glued into an SQL string, a name like `x'); DROP TABLE players; --` could
change the command. I always use parameters (`?` in SQLite, `:player` / `:lim` in Oracle),
so text is only ever data. A test saves exactly that name and reads it back unchanged.

**41. How does the save-exactly-once rule work?**
`MissionRun.save_once()` returns immediately if `result_saved` is already True, and sets it
only after a successful save. A run is saved the moment it is completed or caught, and the
debrief has no button that saves again.

**42. Why are there `kit_summary` and `alert_triggered` columns if the game has no kits?**
They come from the first version. I kept them so runs saved by that version still show in
History and Oracle did not need to be rebuilt; new runs store `'None'` and `'N'`. The new
`CAUGHT` result and `PRO_MODE` column were added; old SQLite files are migrated once
(rename table, create new, copy rows, drop old) because SQLite cannot change a CHECK
constraint.

**43. What happens if Oracle is down?**
`database_manager.create_repository()` catches the error, logs the technical details,
opens SQLite instead and returns a status like "Oracle unavailable — using SQLite (Oracle
server could not be reached)". The game shows a notice and stays fully playable.

## E. Design, validation and testing

**44. How is the player name validated?**
`.strip()`, empty → "Agent", at most 30 characters, only letters, digits, spaces, `_`, `-`
and `.`; otherwise an inline message is shown (`core/validation.py`).

**45. Why is the game engine free of Tkinter?**
So every rule can be unit-tested without opening a window, and the UI stays a thin layer
that only calls engine methods and redraws.

**46. Where do you use inheritance and method overriding?**
`BaseScreen(ttk.Frame)` defines `on_show()`, `on_hide()`, `can_leave()`; each screen
overrides what it needs (the gameplay screen overrides `can_leave()` to ask "Abandon
mission?"). `BaseRepository` defines the database methods; `SQLiteRepository` and
`OracleRepository` override them.

**47. What is Pro mode and how is it scored?**
Plan Route, Auto Travel and the next-turn preview are switched off; the player reads the
patrols and moves with the arrow keys and Wait. Pro runs get +25% of the score (only when it
is positive) and are stored with `pro_mode = 'Y'`.

**48. How many tests are there and what do they cover?**
125 `unittest` tests: engine, pathfinding, missions, SQLite, drones, state planner,
puzzles, knapsack, Oracle (offline with a fake connection), scoring and validation. Run with
`python -m unittest discover -s tests -v`.

---

## 5-minute demo script

1. **Start** — open a terminal in `D:\DAA\heist_planner_game` and run `python app.py`. Type
   your name, show the inline validation with `a<b>`, then a proper name. (20 s)
2. **The Vault** — Start Mission → The Vault → Start Mission. Point at the red vision tiles
   and the amber next-turn outlines. Press **P**: "Planned route: 25 steps (4 waits),
   effort 25" with an amber wait badge. Now press **W** twice (the drones move) and **P**
   again: "23 steps (2 waits)" — the planner adapts to where the drones are now, because
   the drone clock is part of its vertex. Explain the state graph (question 15). Press
   **A**, then **C** at the core, **P**, **A** → debrief **880**, rank Phantom. (90 s)
3. **The Lab** — Choose Another Mission → The Lab. **P**: the route goes to the keycard and
   then to the terminal ("Lasers block every way in"). **A**, then **H**: the Power Relay.
   Click a wrong path and Submit (+5 effort lockout), then the lightest path. Back to Map,
   **P**, **A** to the prototype. (90 s)
4. **Pro mode** — Choose Another Mission → The Penthouse, tick Pro mode, Start Mission. Walk
   straight towards the keycard with the arrow keys until a drone spots you. (30 s)
5. **History** — Main Menu → Mission History: success and caught runs with rank, effort and
   mode; toggle "All players". (20 s)
6. **About** — show the algorithm credits and the database mode line. (15 s)
7. **(Optional, Oracle mode)** — in a terminal:
   `sqlplus heist@localhost:1521/FREEPDB1` then `SET SERVEROUTPUT ON`,
   `EXEC HP_PRINT_RECENT_RUNS(5)` and `SELECT * FROM hp_run_audit;` to show the rows the
   game just saved through `HP_SAVE_RUN` and the trigger. (30 s)
