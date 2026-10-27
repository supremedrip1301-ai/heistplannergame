# Viva Questions — Heist Planner Game

Short, beginner-friendly answers. File names point to where the answer lives in the code.

---

## A. Tkinter and the event loop

**1. What does `mainloop()` do?**
It starts Tkinter's event loop: it waits for events (clicks, key presses, timers, window
resizes) and calls the matching callback. The program stays inside `mainloop()` until the
window is closed (`app.py`).

**2. Why is there only one window, and how do screens change?**
Every screen is a `ttk.Frame` placed in the same grid cell of one container. Showing a
screen means calling `tkraise()` on it (`ui/main_window.py`, `show()`). No new top-level
windows are opened; only `messagebox` dialogs pop up.

**3. Why `after()` instead of `time.sleep()` for Auto Travel?**
`sleep()` blocks the event loop, so the window would freeze and not even redraw.
`after(220, callback)` asks Tkinter to call the function later and returns immediately,
so the window stays responsive and the character moves one tile every 220 ms
(`ui/gameplay_screen.py`).

**4. How is Auto Travel stopped safely?**
The id returned by `after()` is stored and cancelled with `after_cancel()` in Stop,
Restart, Return to Menu, screen change and window close. Each callback also checks a run
token: Restart increases `run_token`, so a callback from an old run sees a different
token and does nothing.

**5. How are keyboard shortcuts done?**
`root.bind("<KeyPress>", ...)` sends every key to `MainWindow.on_key()`, which forwards it
only to the visible screen (and ignores keys typed in an Entry). The gameplay screen maps
`p`, `space`, `a`, `Escape`, `c` and the arrow keys to actions. I did not use the
`keyboard` or `pynput` modules from the slides because they hook the whole operating
system; `bind()` is Tkinter's own tool.

**6. How is the map drawn?**
With `Canvas` primitives only: `create_rectangle` for tiles, `create_line` for the
static-field zig-zag and the dashed route, `create_polygon` for the objective diamond and
the extraction triangle, `create_oval` for the character and route dots, `create_text` for
labels (`ui/map_view.py`). The character is drawn last so nothing hides it.

**7. How does the map fit different window sizes?**
On every `<Configure>` event the tile size is recalculated as the largest whole number
that fits: `min((width − 20) // columns, (height − 20) // rows)`, then the map is centred.

**8. What happens if a callback crashes?**
`root.report_callback_exception` is replaced by a handler that logs the full traceback to
`logs/heist_planner.log` and shows a friendly dialog, so the player never sees a raw
traceback.

## B. Dijkstra and route planning

**9. How is the map a graph?**
Each walkable tile `(row, col)` is a vertex. A step up, right, down or left into a
walkable neighbour is a directed edge. Walls and sealed gates are not vertices.

**10. What is the cost of an edge?**
The cost of the tile being **entered**: floor/start/objective/extraction/open gate = 1,
static field = 4 (2 with Mobility Boots). The start tile itself is never charged.

**11. Why does Dijkstra need non-negative costs?**
Dijkstra assumes that once a vertex is taken out with the smallest distance, no later
path can make it cheaper. A negative edge could make a later path cheaper, breaking that
assumption. All our costs are positive (1, 2 or 4), so the assumption holds.

**12. Why a heap instead of my O(V²) worksheet version?**
My Exp 4 version scans all vertices to find the closest one each time: O(V) per step,
O(V²) total, plus an O(V²) matrix. A map has at most 4 edges per tile, so most of the
matrix is zeros. With `heapq`, getting the smallest is O(log V), giving O((V + E) log V).

**13. What is a "stale" heap entry?**
A tile can be pushed several times with different costs. When an older, more expensive
entry is popped later, `if d > dist[node]: continue` skips it.

**14. How is the path rebuilt?**
Whenever a cheaper way to a tile is found, `previous[tile]` stores the tile we came
from. After reaching the goal, we follow `previous` back to the start and reverse the list.

**15. How are ties broken so the path is always the same?**
The heap stores `(cost, row, col)` tuples, so equal costs are ordered by row then column,
and neighbours are always explored in the order up, right, down, left.

**16. What happens when there is no route?**
`find_shortest_path` returns `RouteResult([], None, False)` — it never raises. The engine
sets status `NO_ROUTE`, the UI shows "No safe route from here" and disables movement,
leaving Restart and Return to Menu.

**17. Explain the Gallery example.**
Straight along row 1 is 9 steps but enters 4 static fields: 2 + 4×4 + 3 = 21. The loop
down column 1, along row 5 and up column 10 is 17 steps of floor = 17, so Dijkstra picks
the longer route. With Mobility Boots the fields cost 2: 2 + 8 + 3 = 13, so the straight
route becomes the best one.

**18. How does rerouting after the alert work?**
The engine adds the gate tile to `sealed_tiles`, discards the current route, and runs
Dijkstra again from the character's current position with the gate blocked. In the Relay,
objective → exit goes from 11 (through the gate) to 19 (around the right side and the bottom).

**19. What bug did you fix in your worksheet Dijkstra?**
In the printed Python version, `if current == -1: break`, `visited[current] = True` and
the relaxation loop were indented inside the loop that searches for the minimum, and
`if new_distance < distance[v]` was not nested under `graph[current][v] > 0`. The fixed
copy is `dijkstra_matrix()` in `tests/reference_algorithms.py`, and a test checks that it
gives exactly the same minimum costs as the heap version for every pair of tiles of every map.

## C. 0/1 Knapsack

**20. How is the Suggested Kit a Knapsack problem?**
Gadgets are items, energy cost is the weight, mission usefulness is the value, 8 energy
units is the capacity, and each gadget can be taken at most once (0/1).

**21. Explain the DP table.**
`best[i][c]` is the best result using only the first `i` gadgets with at most `c`
energy. For each gadget: skip it (`best[i−1][c]`) or take it if it fits
(`best[i−1][c − cost] + usefulness`), and keep the better one.

**22. How do you know which gadgets were chosen?**
Traceback: start at `best[n][8]` and go up row by row. If "take gadget i" still produces
the value in the cell, gadget i was taken and the capacity drops by its cost.

**23. What is the tie-break rule?**
Highest usefulness first; if equal, the lower total energy; if still equal, the
alphabetically first sorted list of IDs. Cells store `(usefulness, −energy)` so tuple
comparison does the first two rules. In the Archive, scanner + repair + lens and
scanner + boots + lens both give 15, but the first uses 7 energy instead of 8, so it wins.

**24. DP vs Branch and Bound vs brute force?**
Brute force tries all 2ⁿ subsets (64 here). My Exp 6 Branch and Bound explores a tree and
prunes branches whose fractional upper bound cannot beat the best so far — usually fast,
exponential in the worst case. DP is O(n × C), here 6 × 9 cells. The tests run all three
and check they agree.

**25. How are the two algorithms connected?**
In the Gallery the Suggested Kit contains Mobility Boots. The boots lower the static-field
cost, which changes Dijkstra's best route from 17 to 13. The Knapsack decision changes the
shortest-path answer.

## D. Databases, SQL and PL/SQL

**26. Why SQLite as the default?**
It ships with Python, needs no server and stores everything in one file
(`data/heist_planner.db`), so the game runs with zero installation.

**27. Does SQLite run PL/SQL?**
No. SQLite has no stored procedures. In SQLite mode the same rules (validation,
find-or-create player, rank thresholds) are done in Python. PL/SQL runs only in Oracle mode.

**28. What does `HP_SAVE_RUN` do?**
It validates the inputs, checks the mission exists (`SELECT ... INTO` with
`NO_DATA_FOUND`), finds or creates the player, inserts the run and returns the new ID
through the OUT parameter `p_run_id` (`RETURNING run_id INTO p_run_id`).

**29. What is an OUT parameter and how does Python read it?**
An OUT parameter is a variable the procedure fills for the caller. In Python I create
`cursor.var(int)`, pass it to `cursor.callproc(...)`, and read it with `.getvalue()`.

**30. Function vs procedure?**
A function returns a value and can be used inside SQL, like `HP_RANK_TITLE(score)` in
the history `SELECT`. A procedure performs actions and returns results through OUT
parameters, like `HP_SAVE_RUN` and `HP_GET_STATS`.

**31. What do the trigger and sequence do?**
`HP_TRG_RUN_AUDIT` fires `AFTER INSERT ... FOR EACH ROW` on `HP_MISSION_RUNS` and copies
`:NEW.run_id`, the player, the score, `USER` and `SYSDATE` into `HP_RUN_AUDIT`, taking the
audit ID from `HP_AUDIT_SEQ.NEXTVAL` — my Program 6 pattern, changed from UPDATE to INSERT.

**32. Why does Python commit instead of the procedure?**
The caller owns the transaction. If the procedure committed, a later failure in the same
operation could leave half-saved data. Python commits only after the call succeeds and
rolls back on any exception.

**33. Why `RAISE_APPLICATION_ERROR` instead of `WHEN OTHERS THEN DBMS_OUTPUT.PUT_LINE`?**
`DBMS_OUTPUT` only prints text on the server; Python would think the save worked.
`RAISE_APPLICATION_ERROR(-20001, ...)` sends a real error that `oracledb` raises as an
exception, which the game logs and turns into a friendly message.

**34. What is Thin mode?**
`python-oracledb` can talk to Oracle directly in pure Python (Thin mode), so no Oracle
Instant Client is needed. I never call `oracledb.init_oracle_client()`.

**35. What is SQL injection and how do you prevent it?**
If user text is glued into an SQL string, a name like `x'); DROP TABLE players; --` could
change the command. I always use parameters (`?` in SQLite, `:player` / `:lim` in Oracle),
so text is only ever data. A test saves exactly that name and reads it back unchanged.

**36. How does the save-exactly-once rule work?**
`MissionRun.save_once()` returns immediately if `result_saved` is already True, and sets
it only after a successful save. The run is saved the moment extraction is reached, and
the debrief has no button that saves again.

**37. What happens if Oracle is down?**
`database_manager.create_repository()` catches the error, logs the technical details,
opens SQLite instead and returns a status like "Oracle unavailable — using SQLite (Oracle
server could not be reached)". The game shows a notice and stays fully playable.

## E. Validation, testing and design

**38. How is the player name validated?**
`.strip()`, empty → "Agent", at most 30 characters, only letters, digits, spaces, `_`,
`-` and `.`; otherwise an inline message is shown (`core/validation.py`).

**39. Why is the game engine free of Tkinter?**
So every rule can be unit-tested without opening a window, and the UI stays a thin layer
that only calls engine methods and redraws.

**40. How did you test that every room is reachable?**
With my Exp 3 Union-Find: every walkable tile starts in its own set, neighbouring
walkable tiles are joined with `union()`, and the test checks that only one root remains.

**41. Where do you use inheritance and method overriding?**
`BaseScreen(ttk.Frame)` defines `on_show()`, `on_hide()`, `can_leave()`; each screen
overrides what it needs (the gameplay screen overrides `can_leave()` to ask "Abandon
mission?"). `BaseRepository` defines the database methods; `SQLiteRepository` and
`OracleRepository` override them.

**42. How many tests are there and what do they cover?**
96 `unittest` tests: pathfinding, missions, optimiser, scoring, engine, SQLite, Oracle
(offline with a fake connection) and validation. Run with
`python -m unittest discover -s tests -v`.

---

## 5-minute demo script

1. **Start** — double-click `run_game.bat`. Type your name, show the inline validation with
   `a<b>`, then a proper name. (20 s)
2. **Gallery without boots** — Start Mission → The Gallery → Start Preparation → Begin
   Mission with an empty kit (confirm). Press **P**: "Planned route: 17 steps, effort 17" —
   the long loop. Point out the 9-step route through the static fields costs 21. (60 s)
3. **Gallery with Suggested Kit** — Return to Menu (no moves yet, so no abandon) → Gallery
   → **Suggested Kit** ticks Scanner + Boots + Repair, energy 8 / 8, readiness 100%. Try
   ticking another gadget to show the refusal. Begin Mission → **P**: "9 steps, effort 13"
   straight through the fields. Press **A**, collect with **C**, **P**, **A** → debrief **810**,
   rank Phantom. (90 s)
4. **Relay alert** — Choose Another Mission → The Relay → Suggested Kit (Decoy + Repair +
   Lens) → Begin. **P**, **A** to the key, **C**: the gate turns red with "SEALED", the event
   says "ALERT — relay gate sealed, route recalculated", the route jumps to effort 19.
   **A** to finish; the debrief shows the alert penalty cancelled by the decoy. (60 s)
5. **History** — Main Menu → Mission History: both runs once each, with rank, effort and
   kit; toggle "All players". (20 s)
6. **About** — show the algorithm credits and the database mode line. (15 s)
7. **(Optional, Oracle mode)** — in a terminal:
   `sqlplus heist@localhost:1521/FREEPDB1` then `SET SERVEROUTPUT ON`,
   `EXEC HP_PRINT_RECENT_RUNS(5)` and `SELECT * FROM hp_run_audit;` to show the rows the
   game just saved through `HP_SAVE_RUN` and the trigger. (Route B container:
   `podman exec -it oracle26ai sqlplus heist@FREEPDB1`.) (30 s)
