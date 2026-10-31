# Heist Planner Game

A stealth strategy game in Python and Tkinter, built as an MCA mini project
(Design and Analysis of Algorithms) at Chandigarh University by
Anshul Kaushik (UID 26MCI10329). The game is driven by **Dijkstra's
shortest-path algorithm** with a binary heap.

## Missions

1. **The Vault** (Hard): three patrol drones guard the vault core.
2. **The Lab** (Expert): four drones, a keycard, a locked door, a laser barrier and a 6 x 6 Power Relay terminal.
3. **The Penthouse** (Master): three drones, static fields, a keycard, a locked door, laser barriers and a 7 x 7 Power Relay terminal.

## Features

- **Real-time drones**: every 0.5 seconds each drone moves one tile along its patrol and looks two tiles ahead.
- **Arrow keys** move the agent at once; **Enter** pauses the game.
- **Plan Route [P]**: Dijkstra on a state graph (tile, drone clock, keycard) finds the cheapest route no drone can see. The route is re-planned whenever it goes out of date.
- **Auto Travel [A]** and **Move Next Step [Space]** follow the planned route.
- **Power Relay hack terminal**: draw the lightest path from IN to OUT. Dijkstra decides the right answer, and the **Relay Monitor** re-runs Dijkstra after every click (ON TRACK / OFF TRACK).
- **Pro mode**: no route guidance, +25% score.
- **Mission History**: every run is saved in SQLite, or in Oracle through PL/SQL procedures.

## Where Dijkstra is used

| File | Function | Role |
|------|----------|------|
| `core/pathfinding.py` | `find_shortest_path()` | Dijkstra with `heapq` on the tile grid |
| `core/state_planner.py` | `plan_state_route()` | Dijkstra on the state graph (drones + keycard) |
| `core/puzzles.py` | `best_from()` | Relay Monitor: Dijkstra from the end of the player's path |

## Run locally

Requires Python 3.10 or newer (Tkinter is included with Python on Windows).

```
git clone https://github.com/supremedrip1301-ai/heistplannergame.git
cd heistplannergame
python app.py
```

By default the game saves to a local SQLite file (`data/heist_planner.db`); nothing else is needed.

## Oracle setup (optional)

Tested on Oracle AI Database 26ai Free (`localhost:1521/FREEPDB1`).

```
pip install oracledb
sqlplus system@localhost:1521/FREEPDB1 @database\create_oracle_user.sql
sqlplus heist@localhost:1521/FREEPDB1 @database\setup_oracle.sql
```

Then create a `.env` file in the project folder (it is git-ignored):

```
DATABASE_BACKEND=oracle
ORACLE_USER=heist
ORACLE_PASSWORD=your_password
ORACLE_DSN=localhost:1521/FREEPDB1
```

The schema has the tables `HP_PLAYERS`, `HP_MISSIONS`, `HP_MISSION_RUNS` and `HP_RUN_AUDIT`, the sequence `HP_AUDIT_SEQ`, the procedures `HP_SAVE_RUN`, `HP_GET_STATS` and `HP_PRINT_RECENT_RUNS`, the function `HP_RANK_TITLE` and the audit trigger `HP_TRG_RUN_AUDIT`. If Oracle cannot be reached, the game falls back to SQLite.

## Project structure

```
app.py          start the game
core/           game engine, missions, drones, Dijkstra, puzzles, scoring
ui/             Tkinter screens and the map canvas
database/       SQLite and Oracle repositories, Oracle SQL scripts
data/           local SQLite database
```
