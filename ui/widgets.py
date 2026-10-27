"""Small reusable widgets: scrollable frame, capacity bar, info rows and badges."""

import tkinter as tk
from tkinter import ttk

from ui import styles


class ScrollableFrame(ttk.Frame):
    """A frame with a vertical scrollbar. Put children inside self.inner."""

    def __init__(self, parent, inner_style: str = "TFrame", bg: str = styles.BG):
        super().__init__(parent, style=inner_style)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, style=inner_style)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.inner.bind("<Configure>", self.on_inner_resize)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        # Mouse wheel only while the pointer is over this area.
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self.on_wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def on_inner_resize(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_resize(self, event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def on_wheel(self, event) -> None:
        # Only scroll when the content is taller than the visible area.
        if self.inner.winfo_reqheight() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-event.delta / 120), "units")


class CapacityBar(tk.Canvas):
    """Horizontal bar such as "Energy used: 5 / 8"."""

    def __init__(self, parent, capacity: int, bg: str = styles.PANEL, height: int = 22):
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self.capacity = capacity
        self.used = 0
        self.bind("<Configure>", lambda e: self.redraw())

    def set_used(self, used: int) -> None:
        self.used = used
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 50)
        height = int(self.cget("height"))
        segment = (width - 2) / self.capacity
        for i in range(self.capacity):
            x0 = 1 + i * segment
            filled = i < self.used
            colour = styles.ACCENT if filled else styles.PANEL_ALT
            if filled and self.used == self.capacity:
                colour = styles.AMBER          # full: show it in amber
            self.create_rectangle(x0 + 1, 2, x0 + segment - 2, height - 2,
                                  fill=colour, outline=styles.BORDER)


def usefulness_level(value: int) -> tuple:
    """Turn a usefulness number into (bars, word) for the player: 1-3 bars."""
    if value >= 7:
        return 3, "High"
    if value >= 4:
        return 2, "Medium"
    return 1, "Low"


def draw_level_bars(canvas: tk.Canvas, bars: int, x: int = 2, y: int = 4,
                    colour: str = styles.ACCENT) -> None:
    """Three small rising bars, `bars` of them lit (a signal-strength icon)."""
    for i in range(3):
        height = 6 + i * 5
        fill = colour if i < bars else styles.BORDER
        canvas.create_rectangle(x + i * 8, y + 16 - height, x + i * 8 + 5, y + 16,
                                fill=fill, outline="")


class InfoRow:
    """A "Label:  value" line inside a panel, with a changeable value style."""

    def __init__(self, parent, row: int, label: str, wraplength: int = 200):
        ttk.Label(parent, text=label, style="PanelDim.TLabel").grid(
            row=row, column=0, sticky="nw", padx=(0, 10), pady=2)
        self.value = ttk.Label(parent, text="-", style="PanelValue.TLabel",
                               wraplength=wraplength, justify="left")
        self.value.grid(row=row, column=1, sticky="nw", pady=2)

    def set(self, text: str, style: str = "PanelValue.TLabel") -> None:
        self.value.configure(text=text, style=style)
