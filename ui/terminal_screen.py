"""Terminal screen: the Power Relay puzzle of the Lab and the Penthouse.

Click touching cells from IN to OUT; the load must be the lowest possible
(the engine checks it with Dijkstra).

Relay Monitor: after every click, Dijkstra runs again from the end of the
player's path to OUT (PowerRelayPuzzle.best_from) and the monitor says
whether the path can still reach the lightest load. Off in Pro mode.
"""

import tkinter as tk
from tkinter import ttk

from ui import styles
from ui.base_screen import BaseScreen

INSTRUCTIONS = ("Route power from IN to OUT through touching cells. Every number is the load "
                "of that cell. Only the lightest possible path stabilises the relay. "
                "Click a cell next to the end of your path to extend it; click the last cell "
                "to take it back.")


class TerminalScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.puzzle = None
        self.path = []                # selected cells, in order
        self.cell_size = 56

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0, minsize=320)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(32, 16, 32, 6))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(header, text="Terminal", style="Title.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w")
        self.instructions = ttk.Label(header, text="", style="Subtitle.TLabel", wraplength=900,
                                      justify="left")
        self.instructions.grid(row=1, column=0, sticky="w")
        header.bind("<Configure>", lambda e: self.instructions.configure(
            wraplength=max(400, e.width - 80)))

        self.canvas = tk.Canvas(self, bg=styles.PANEL, highlightthickness=0, bd=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(32, 12), pady=(6, 20))
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

        side = ttk.Frame(self, style="Panel.TFrame", padding=18)
        side.grid(row=1, column=1, sticky="nsew", padx=(0, 32), pady=(6, 20))
        side.columnconfigure(0, weight=1)
        side.rowconfigure(5, weight=1)
        ttk.Label(side, text="Readout", style="PanelHeading.TLabel").grid(
            row=0, column=0, sticky="w")
        self.readout = ttk.Label(side, text="", style="PanelValue.TLabel",
                                 font=styles.font(14, "bold"), wraplength=270, justify="left")
        self.readout.grid(row=1, column=0, sticky="w", pady=(8, 4))
        # Relay Monitor line (green = on track, red = off track).
        self.monitor = ttk.Label(side, text="", style="PanelDim.TLabel", wraplength=270,
                                 justify="left")
        self.monitor.grid(row=2, column=0, sticky="w", pady=(4, 4))
        self.message = ttk.Label(side, text="", style="PanelDim.TLabel", wraplength=270,
                                 justify="left")
        self.message.grid(row=3, column=0, sticky="w", pady=(8, 4))
        self.lockouts = ttk.Label(side, text="", style="PanelDim.TLabel", wraplength=270)
        self.lockouts.grid(row=4, column=0, sticky="w")

        buttons = ttk.Frame(side, style="Panel.TFrame")
        buttons.grid(row=6, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1, uniform="tb")
        buttons.columnconfigure(1, weight=1, uniform="tb")
        self.submit_button = ttk.Button(buttons, text="Submit", style="Accent.TButton",
                                        command=self.submit)
        self.submit_button.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Button(buttons, text="Clear", command=self.clear).grid(
            row=1, column=0, sticky="ew", padx=(0, 4))
        self.back_button = ttk.Button(buttons, text="Back to Map", command=self.back)
        self.back_button.grid(row=1, column=1, sticky="ew", padx=(4, 0))

    # ------------------------------------------------------------ life cycle
    def on_show(self, **kwargs) -> None:
        run = self.app.run
        if run is None or not run.can_hack():
            self.app.show("gameplay")
            return
        self.puzzle = run.open_terminal()
        self.path = []
        n = self.puzzle.size
        self.title_label.configure(text=f"Terminal — {self.puzzle.title}  ({n} × {n})")
        self.instructions.configure(text=INSTRUCTIONS)
        self.message.configure(text="", style="PanelDim.TLabel")
        self.submit_button.state(["!disabled"])
        self.back_button.configure(style="TButton")
        self.update_readout()
        self.redraw()

    def can_leave(self) -> bool:
        """Leaving to anything but the map counts as leaving the mission."""
        if self.app.next_screen == "gameplay":
            return True
        return self.app.screens["gameplay"].can_leave()

    # ------------------------------------------------------------ drawing
    def layout(self):
        """(cell size, x offset, y offset) that centre the puzzle in the canvas."""
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        n = self.puzzle.size
        size = max(30, min(64, (width - 40) // n, (height - 40) // n))
        return size, (width - size * n) // 2, (height - size * n) // 2

    def redraw(self) -> None:
        self.canvas.delete("all")
        if self.puzzle is None:
            return
        puzzle = self.puzzle
        size, ox, oy = self.layout()
        on_path = {pos: i for i, pos in enumerate(self.path)}
        for row in range(puzzle.size):
            for col in range(puzzle.size):
                x0, y0 = ox + col * size, oy + row * size
                pos = (row, col)
                fill = styles.ACCENT_SOFT if pos in on_path else styles.PANEL_ALT
                if pos == puzzle.start or pos == puzzle.goal:
                    outline, width = styles.ACCENT, 2
                else:
                    outline, width = styles.BORDER, 1
                self.canvas.create_rectangle(x0 + 2, y0 + 2, x0 + size - 2, y0 + size - 2,
                                             fill=fill, outline=outline, width=width)
                colour = styles.TEXT if pos in on_path else styles.TEXT_DIM
                self.canvas.create_text(x0 + size / 2, y0 + size / 2, text=str(puzzle.cell(pos)),
                                        fill=colour, font=styles.font(max(10, size // 3), "bold"))
                if pos == puzzle.start:
                    self.canvas.create_text(x0 + 8, y0 + 10, text="IN", anchor="w",
                                            fill=styles.ACCENT, font=styles.font(8, "bold"))
                if pos == puzzle.goal:
                    self.canvas.create_text(x0 + 8, y0 + 10, text="OUT", anchor="w",
                                            fill=styles.ACCENT, font=styles.font(8, "bold"))
        # The current path as a line through cell centres.
        if len(self.path) >= 2:
            points = []
            for row, col in self.path:
                points.extend([ox + col * size + size / 2, oy + row * size + size / 2])
            self.canvas.create_line(*points, fill=styles.ACCENT, width=3, dash=(6, 3))

    # ------------------------------------------------------------ input
    def on_click(self, event) -> None:
        if self.puzzle is None or self.app.run is None or not self.app.run.can_hack():
            return
        size, ox, oy = self.layout()
        col = (event.x - ox) // size
        row = (event.y - oy) // size
        if 0 <= row < self.puzzle.size and 0 <= col < self.puzzle.size:
            self.click_cell((row, col))
        self.update_readout()
        self.redraw()

    def click_cell(self, pos) -> None:
        """Extend, shorten or start the Power Relay path."""
        if self.path and pos == self.path[-1]:
            self.path.pop()                          # take back the last cell
            return
        if not self.path:
            if pos == self.puzzle.start:
                self.path.append(pos)
            else:
                self.message.configure(text="Start at IN (top-left).", style="PanelWarn.TLabel")
            return
        last = self.path[-1]
        if abs(pos[0] - last[0]) + abs(pos[1] - last[1]) == 1 and pos not in self.path:
            self.path.append(pos)
        else:
            self.message.configure(text="Pick a cell touching the end of your path.",
                                   style="PanelWarn.TLabel")

    def update_readout(self) -> None:
        puzzle = self.puzzle
        text = f"Relay load: {puzzle.load(self.path)}"
        if self.path and self.path[-1] == puzzle.goal:
            text += "  (path complete)"
        self.readout.configure(text=text)
        self.update_monitor()
        run = self.app.run
        if run is not None and run.wrong_answers:
            self.lockouts.configure(text=f"Wrong answers so far: {run.wrong_answers}")
        else:
            self.lockouts.configure(text="A wrong answer costs a lockout (+5 effort).")

    def update_monitor(self) -> None:
        """Ask the puzzle (Dijkstra from the end of the path) how the path is doing."""
        puzzle = self.puzzle
        run = self.app.run
        if run is not None and run.pro_mode:
            self.monitor.configure(text="Relay Monitor offline (Pro mode).",
                                   style="PanelDim.TLabel")
            return
        if not self.path:
            self.monitor.configure(text="Relay Monitor: start at IN (top-left).",
                                   style="PanelDim.TLabel")
            return
        best_here = puzzle.best_from(self.path)
        if best_here is None:
            self.monitor.configure(text="Relay Monitor: DEAD END — OUT cannot be reached from "
                                        "here. Take back some cells.", style="PanelAlert.TLabel")
        elif best_here == puzzle.best and self.path[-1] == puzzle.goal:
            self.monitor.configure(text="Relay Monitor: lightest path found — Submit!",
                                   style="PanelGood.TLabel")
        elif best_here == puzzle.best:
            self.monitor.configure(text="Relay Monitor: ON TRACK — this path can still reach "
                                        "the lightest load.", style="PanelGood.TLabel")
        else:
            self.monitor.configure(text=f"Relay Monitor: OFF TRACK — the best this path can "
                                        f"still reach is {best_here}. Take back some cells.",
                                   style="PanelAlert.TLabel")

    # ------------------------------------------------------------ buttons
    def submit(self) -> None:
        run = self.app.run
        if run is None or not run.can_hack():
            return
        solved, message = run.submit_terminal(list(self.path))
        self.message.configure(text=message, style="PanelGood.TLabel" if solved
                               else "PanelWarn.TLabel")
        self.update_readout()
        if solved:
            self.submit_button.state(["disabled"])
            self.back_button.configure(style="Accent.TButton")
            self.app.terminal_message = message + " Plan your route to the target."

    def clear(self) -> None:
        self.path = []
        self.message.configure(text="", style="PanelDim.TLabel")
        self.update_readout()
        self.redraw()

    def back(self) -> None:
        run = self.app.run
        if run is not None and not run.terminal_solved:
            self.app.terminal_message = "Terminal still locked — the lasers are on."
        self.app.show("gameplay", from_terminal=True)
