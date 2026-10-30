"""Drawing the mission map on a Tkinter Canvas.

Only Canvas primitives are used (rectangles, lines, ovals, polygons, text).
The same draw_tile() helper draws the big map, the legend swatches, the
mission-card thumbnails and the main-menu preview, so they always match.
"""

import tkinter as tk

from core import missions as m
from ui import styles

# Drawing state flags for draw_tile()
SEALED = "sealed"
COLLECTED = "collected"
WEAK_POINT = "weak_point"
TAKEN = "taken"            # keycard already picked up
UNLOCKED = "unlocked"      # door opened with the keycard
SOLVED = "solved"          # terminal hacked
OFF = "off"                # laser switched off


def draw_tile(canvas, x0, y0, size, char, flags=(), detail=True):
    """Draw one tile with its top-left corner at (x0, y0).

    detail=False draws a simple version for small thumbnails.
    """
    x1, y1 = x0 + size, y0 + size
    cx, cy = x0 + size / 2, y0 + size / 2

    if char == m.WALL:
        canvas.create_rectangle(x0, y0, x1, y1, fill=styles.TILE_WALL,
                                outline=styles.TILE_WALL_EDGE)
        return

    # Every walkable tile gets a floor first.
    canvas.create_rectangle(x0, y0, x1, y1, fill=styles.TILE_FLOOR,
                            outline=styles.TILE_FLOOR_EDGE)
    pad = size * 0.18

    if char == m.STATIC_FIELD:
        canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill=styles.TILE_STATIC,
                                outline="")
        if detail:
            # A small amber zig-zag: the "static" sign.
            points = []
            steps = 4
            for i in range(steps + 1):
                px = x0 + pad + i * (size - 2 * pad) / steps
                py = cy - size * 0.12 if i % 2 == 0 else cy + size * 0.12
                points.extend([px, py])
            canvas.create_line(*points, fill=styles.TILE_STATIC_MARK,
                               width=max(1, size // 18))

    elif char == m.GATE:
        if SEALED in flags:
            canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1,
                                    fill=styles.TILE_GATE_SEALED, outline=styles.RED,
                                    width=2)
            if detail:
                canvas.create_line(x0 + pad, y0 + pad, x1 - pad, y1 - pad,
                                   fill=styles.RED, width=max(2, size // 12))
                canvas.create_line(x0 + pad, y1 - pad, x1 - pad, y0 + pad,
                                   fill=styles.RED, width=max(2, size // 12))
        else:
            canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1,
                                    fill=styles.TILE_GATE_OPEN, outline="")
            if detail:
                # Two vertical bars = an open gate frame.
                for fx in (x0 + pad, x1 - pad):
                    canvas.create_line(fx, y0 + pad, fx, y1 - pad, fill=styles.ACCENT_DARK,
                                       width=max(2, size // 12))
        if WEAK_POINT in flags and SEALED not in flags:
            canvas.create_rectangle(x0 + 2, y0 + 2, x1 - 2, y1 - 2, outline=styles.AMBER,
                                    width=2, dash=(4, 2))

    elif char == m.START:
        canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill=styles.TILE_START,
                                outline="")
        if detail:
            canvas.create_text(cx, cy, text="S", fill=styles.TEXT_DIM,
                               font=styles.font(max(7, int(size * 0.3)), "bold"))

    elif char == m.EXTRACTION:
        canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill=styles.TILE_EXTRACTION,
                                outline=styles.GREEN, width=1 if not detail else 2)
        if detail:
            canvas.create_polygon(cx, y0 + pad, x1 - pad, y1 - pad, x0 + pad, y1 - pad,
                                  fill="", outline=styles.GREEN, width=2)

    elif char == m.KEYCARD:
        if TAKEN not in flags:
            w = size * 0.5
            h = size * 0.34
            canvas.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2,
                                    fill=styles.KEYCARD, outline="")
            if detail:
                canvas.create_rectangle(cx - w / 2, cy - h / 6, cx + w / 2, cy,
                                        fill=styles.TEXT_DARK, outline="")

    elif char == m.DOOR:
        if UNLOCKED in flags:
            canvas.create_rectangle(x0 + 2, y0 + 2, x1 - 2, y1 - 2, outline=styles.DOOR_FRAME,
                                    dash=(3, 3))
        else:
            canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill=styles.TILE_DOOR,
                                    outline=styles.DOOR_FRAME, width=2)
            if detail:
                # A small padlock: shackle (arc) + body (rectangle).
                r = size * 0.13
                canvas.create_arc(cx - r, cy - r * 2.2, cx + r, cy, start=0, extent=180,
                                  style="arc", outline=styles.DOOR_FRAME, width=2)
                canvas.create_rectangle(cx - r * 1.4, cy - r * 0.9, cx + r * 1.4, cy + r * 1.5,
                                        fill=styles.DOOR_FRAME, outline="")

    elif char == m.TERMINAL:
        canvas.create_rectangle(x0 + pad, y0 + pad, x1 - pad, y1 - pad * 1.4,
                                fill=styles.TERMINAL_BODY, outline=styles.BORDER)
        screen = styles.GREEN if SOLVED in flags else styles.TERMINAL_SCREEN
        inset = size * 0.26
        canvas.create_rectangle(x0 + inset, y0 + inset, x1 - inset, y1 - inset * 1.5,
                                fill=screen, outline="")
        if detail:
            canvas.create_line(cx - size * 0.15, y1 - pad, cx + size * 0.15, y1 - pad,
                               fill=styles.BORDER, width=2)

    elif char == m.LASER:
        if OFF in flags:
            canvas.create_line(x0 + 2, cy, x1 - 2, cy, fill=styles.TEXT_DIM, dash=(2, 4))
        else:
            for k in (-0.22, 0, 0.22):
                canvas.create_line(x0 + 1, cy + size * k, x1 - 1, cy + size * k,
                                   fill=styles.LASER_BEAM, width=max(1, size // 20))
            if detail:
                for ex in (x0 + 2, x1 - 4):
                    canvas.create_rectangle(ex, y0 + pad, ex + 2, y1 - pad,
                                            fill=styles.LASER_BEAM, outline="")

    elif char == m.OBJECTIVE:
        canvas.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill=styles.TILE_OBJECTIVE,
                                outline="")
        diamond = (cx, y0 + pad, x1 - pad, cy, cx, y1 - pad, x0 + pad, cy)
        if COLLECTED in flags:
            canvas.create_polygon(*diamond, fill="", outline=styles.TEXT_DIM, width=1,
                                  dash=(3, 2))
            if detail:
                canvas.create_text(cx, cy, text="✓", fill=styles.GREEN,
                                   font=styles.font(max(7, int(size * 0.32)), "bold"))
        else:
            canvas.create_polygon(*diamond, fill=styles.AMBER, outline="")


def draw_mini_map(canvas, grid, tile, x0=0, y0=0, flags_for=None, drones=()):
    """Draw a whole map at a small tile size (thumbnails, menu preview)."""
    for r, line in enumerate(grid):
        for c, ch in enumerate(line):
            flags = flags_for((r, c)) if flags_for else ()
            draw_tile(canvas, x0 + c * tile, y0 + r * tile, tile, ch, flags,
                      detail=tile >= 14)
    for drone in drones:             # small red dots at each drone's starting tile
        row, col = drone.position(0)
        x, y = x0 + col * tile + tile / 2, y0 + row * tile + tile / 2
        canvas.create_oval(x - tile * 0.35, y - tile * 0.35, x + tile * 0.35, y + tile * 0.35,
                           fill=styles.DRONE_BODY, outline="")


def draw_drone(canvas, x, y, size, facing, frozen=False):
    """A drone: a diamond body with an 'eye' pointing where it will move next."""
    body = styles.DRONE_FROZEN if frozen else styles.DRONE_BODY
    r = size * 0.34
    canvas.create_polygon(x, y - r, x + r, y, x, y + r, x - r, y, fill=body,
                          outline=styles.DRONE_RING, width=2)
    d_row, d_col = facing
    tip_x, tip_y = x + d_col * r * 1.3, y + d_row * r * 1.3
    base = r * 0.45
    # The base of the eye triangle is perpendicular to the facing direction.
    canvas.create_polygon(tip_x, tip_y,
                          x + d_row * base, y - d_col * base,
                          x - d_row * base, y + d_col * base,
                          fill=styles.TEXT, outline="")


class MapView(tk.Canvas):
    """The big map on the gameplay screen. Redraws everything cheaply."""

    def __init__(self, parent):
        super().__init__(parent, bg=styles.BG, highlightthickness=0, bd=0)
        self.run = None
        self.bind("<Configure>", lambda e: self.redraw())

    def show_run(self, run) -> None:
        self.run = run
        self.redraw()

    def tile_size(self) -> int:
        """Biggest whole-pixel tile that lets the full map fit the canvas."""
        mission = self.run.mission
        width = max(self.winfo_width(), 100)
        height = max(self.winfo_height(), 100)
        size = min((width - 20) // mission.cols, (height - 20) // mission.rows)
        return max(12, min(size, 64))

    def tile_flags(self, pos) -> tuple:
        run = self.run
        flags = []
        if pos in run.sealed_tiles:
            flags.append(SEALED)
        if pos == run.mission.objective and run.objective_collected:
            flags.append(COLLECTED)
        if pos == run.mission.gate and run.weak_point_visible:
            flags.append(WEAK_POINT)
        if run.has_key:
            flags.extend([TAKEN, UNLOCKED])
        if run.terminal_solved:
            flags.extend([SOLVED, OFF])
        return tuple(flags)

    def redraw(self) -> None:
        self.delete("all")
        if self.run is None:
            return
        run = self.run
        mission = run.mission
        size = self.tile_size()
        # Centre the map inside the canvas.
        ox = (max(self.winfo_width(), 100) - size * mission.cols) // 2
        oy = (max(self.winfo_height(), 100) - size * mission.rows) // 2

        for r, line in enumerate(mission.grid):
            for c, ch in enumerate(line):
                draw_tile(self, ox + c * size, oy + r * size, size, ch,
                          self.tile_flags((r, c)))

        def centre(pos):
            return ox + pos[1] * size + size / 2, oy + pos[0] * size + size / 2

        # Drone vision: stippled red tiles (the floor pattern still shows through).
        if mission.drones:
            for row, col in run.watched_now():
                self.create_rectangle(ox + col * size, oy + row * size,
                                      ox + (col + 1) * size, oy + (row + 1) * size,
                                      fill=styles.VISION, stipple="gray25", outline="")
            # Pocket Scanner: amber outlines where the drones will look next turn.
            for row, col in run.watched_next_turn():
                self.create_rectangle(ox + col * size + 3, oy + row * size + 3,
                                      ox + (col + 1) * size - 3, oy + (row + 1) * size - 3,
                                      outline=styles.VISION_NEXT, dash=(3, 3))

        # Route overlay: a line through tile centres plus small dots, so the
        # map underneath stays visible.
        if run.has_valid_route():
            points = []
            for pos in run.route.path:
                points.extend(centre(pos))
            self.create_line(*points, fill=styles.ROUTE, width=max(2, size // 10),
                             capstyle="round", joinstyle="round", dash=(6, 4))
            dot = max(2, size // 12)
            for pos in run.route.path[1:]:
                x, y = centre(pos)
                self.create_oval(x - dot, y - dot, x + dot, y + dot, fill=styles.ROUTE,
                                 outline="")
            # Waits: a small amber badge with the number of turns to wait there.
            waits_at = {}
            for a, b in zip(run.route.path, run.route.path[1:]):
                if a == b:
                    waits_at[a] = waits_at.get(a, 0) + 1
            badge = max(7, size // 5)
            for (row, col), count in waits_at.items():
                bx = ox + (col + 1) * size - badge - 1
                by = oy + row * size + badge + 1
                self.create_oval(bx - badge, by - badge, bx + badge, by + badge,
                                 fill=styles.AMBER, outline="")
                self.create_text(bx, by, text=str(count), fill=styles.TEXT_DARK,
                                 font=styles.font(max(7, badge), "bold"))
            # Target ring at the end of the route.
            x, y = centre(run.route.path[-1])
            ring = size * 0.42
            self.create_oval(x - ring, y - ring, x + ring, y + ring, outline=styles.ROUTE,
                             width=2)

        # Sealed-gate warning mark above the gate.
        for pos in run.sealed_tiles:
            x, y = centre(pos)
            self.create_text(x, y - size * 0.62, text="SEALED", fill=styles.RED,
                             font=styles.font(max(7, size // 5), "bold"))

        # Drones, then the character on top of everything.
        frozen = run.freeze_left > 0
        for drone, pos in run.drone_positions():
            x, y = centre(pos)
            draw_drone(self, x, y, size, drone.facing(run.clock), frozen)

        # The character is drawn LAST so nothing can hide it.
        x, y = centre(run.position)
        if run.is_caught():
            ring = size * 0.48
            self.create_oval(x - ring, y - ring, x + ring, y + ring, outline=styles.RED, width=3)
        outer = size * 0.36
        inner = size * 0.24
        self.create_oval(x - outer, y - outer, x + outer, y + outer,
                         fill=styles.CHARACTER_RING, outline=styles.CHARACTER, width=2)
        self.create_oval(x - inner, y - inner, x + inner, y + inner,
                         fill=styles.CHARACTER, outline="")


LEGEND_ITEMS = (
    (m.FLOOR, (), "Floor"),
    (m.WALL, (), "Wall"),
    (m.STATIC_FIELD, (), "Static field"),
    (m.GATE, (), "Relay gate"),
    (m.GATE, (SEALED,), "Sealed gate"),
    (m.OBJECTIVE, (), "Objective"),
    (m.EXTRACTION, (), "Extraction"),
)


HARD_LEGEND_ITEMS = (
    (m.KEYCARD, (), "Keycard"),
    (m.DOOR, (), "Locked door"),
    (m.TERMINAL, (), "Terminal"),
    (m.LASER, (), "Laser"),
)
ALWAYS_SHOWN = (m.FLOOR, m.WALL, m.OBJECTIVE, m.EXTRACTION)


class Legend(tk.Canvas):
    """A row (or rows) of small swatches that explain the map styles."""

    def __init__(self, parent, bg=styles.BG):
        super().__init__(parent, height=30, bg=bg, highlightthickness=0, bd=0)
        self.mission = None
        self.bind("<Configure>", lambda e: self.redraw())

    def show_for(self, mission) -> None:
        """Only explain the tile types that appear on this mission's map."""
        self.mission = mission
        self.redraw()

    def items(self) -> list:
        mission = self.mission
        items = []
        for char, flags, label in LEGEND_ITEMS + HARD_LEGEND_ITEMS:
            on_map = mission is None or any(char in line for line in mission.grid)
            if char in ALWAYS_SHOWN or on_map:
                items.append((char, flags, label))
        if mission is not None and mission.drones:
            items.append(("drone", (), "Drone"))
            items.append(("vision", (), "Drone vision"))
        items.append(("route", (), "Planned route"))
        items.append(("you", (), "You"))
        return items

    def redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 200)
        items = self.items()
        x, y, swatch = 6, 6, 18
        item_width = 112
        per_row = max(1, (width - 6) // item_width)
        rows = (len(items) + per_row - 1) // per_row
        needed = rows * 26 + 6
        if int(self.cget("height")) != needed:
            self.configure(height=needed)
        for i, (char, flags, label) in enumerate(items):
            col = i % per_row
            row = i // per_row
            x = 6 + col * item_width
            y = 4 + row * 26
            if char == "route":
                self.create_line(x, y + swatch / 2, x + swatch, y + swatch / 2,
                                 fill=styles.ROUTE, width=3, dash=(4, 2))
            elif char == "drone":
                draw_drone(self, x + swatch / 2, y + swatch / 2, swatch, (0, 1))
            elif char == "vision":
                self.create_rectangle(x, y, x + swatch, y + swatch, fill=styles.TILE_FLOOR,
                                      outline=styles.TILE_FLOOR_EDGE)
                self.create_rectangle(x, y, x + swatch, y + swatch, fill=styles.VISION,
                                      stipple="gray25", outline="")
            elif char == "you":
                self.create_oval(x + 2, y + 2, x + swatch - 2, y + swatch - 2,
                                 fill=styles.CHARACTER, outline=styles.CHARACTER_RING, width=2)
            else:
                draw_tile(self, x, y, swatch, char, flags, detail=True)
            self.create_text(x + swatch + 6, y + swatch / 2, text=label, anchor="w",
                             fill=styles.TEXT_DIM, font=styles.font(9))
