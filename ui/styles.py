"""Colours, fonts and the ttk Style for the whole game.

Every colour used anywhere in the UI is defined here once, as a named
constant, so no hex code is repeated across files.
"""

import tkinter.font as tkfont
from tkinter import ttk

# ---------------------------------------------------------------- base palette
BG = "#0B1220"            # window background
PANEL = "#141E2E"         # main panels
PANEL_ALT = "#1C2A3F"     # cards, raised areas
BORDER = "#2A3A52"
HOVER = "#24364F"
TEXT = "#E6EDF3"
TEXT_DIM = "#8B9BB4"
TEXT_DARK = "#0B1220"     # text on bright buttons

ACCENT = "#2EC4B6"        # teal: navigation, selection, route
ACCENT_DARK = "#1F8A80"
ACCENT_SOFT = "#163B44"
AMBER = "#E9A23B"         # warnings, static fields
GREEN = "#3DDC84"         # success, extraction
RED = "#E5484D"           # sealed gate, failure
DISABLED_BG = "#1A2433"
DISABLED_FG = "#56657C"

# ---------------------------------------------------------------- map tiles
TILE_WALL = "#273449"
TILE_WALL_EDGE = "#33445E"
TILE_FLOOR = "#121B2A"
TILE_FLOOR_EDGE = "#1A2638"
TILE_STATIC = "#3A2C12"
TILE_STATIC_MARK = AMBER
TILE_GATE_OPEN = "#1B3340"
TILE_GATE_SEALED = "#4A1C22"
TILE_START = "#16323A"
TILE_EXTRACTION = "#123825"
TILE_OBJECTIVE = "#2A2A12"
ROUTE = ACCENT
CHARACTER = ACCENT
CHARACTER_RING = "#0E4D47"

# ---------------------------------------------------------------- fonts
FONT_FAMILY = "Segoe UI"   # replaced by a safe fallback in apply_style()
MONO_FAMILY = "Consolas"


def font(size: int = 10, weight: str = "normal") -> tuple:
    """Font tuple in the game's single font family."""
    return (FONT_FAMILY, size, weight)


def choose_font_family(root) -> None:
    """Use Segoe UI when Windows has it, otherwise a safe default."""
    global FONT_FAMILY, MONO_FAMILY
    families = set(tkfont.families(root))
    if "Segoe UI" not in families:
        FONT_FAMILY = "Helvetica" if "Helvetica" in families else "TkDefaultFont"
    if "Consolas" not in families:
        MONO_FAMILY = "Courier"


def apply_style(root) -> ttk.Style:
    """Configure the ttk theme ('clam' allows colour changes on Windows)."""
    choose_font_family(root)
    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.font", font(10))
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG, foreground=TEXT, font=font(10),
                    bordercolor=BORDER, focuscolor=ACCENT, troughcolor=PANEL)

    # Frames
    style.configure("TFrame", background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("Card.TFrame", background=PANEL_ALT)
    style.configure("Selected.TFrame", background=ACCENT_SOFT)

    # Labels
    style.configure("TLabel", background=BG, foreground=TEXT, font=font(10))
    style.configure("Title.TLabel", font=font(24, "bold"), foreground=TEXT)
    style.configure("Subtitle.TLabel", font=font(11), foreground=TEXT_DIM)
    style.configure("Heading.TLabel", font=font(14, "bold"), foreground=TEXT)
    style.configure("Dim.TLabel", foreground=TEXT_DIM)
    style.configure("Error.TLabel", foreground=RED)
    style.configure("Panel.TLabel", background=PANEL)
    style.configure("PanelDim.TLabel", background=PANEL, foreground=TEXT_DIM, font=font(9))
    style.configure("PanelHeading.TLabel", background=PANEL, font=font(13, "bold"))
    style.configure("PanelValue.TLabel", background=PANEL, font=font(10, "bold"))
    style.configure("PanelAccent.TLabel", background=PANEL, foreground=ACCENT,
                    font=font(10, "bold"))
    style.configure("PanelWarn.TLabel", background=PANEL, foreground=AMBER,
                    font=font(10, "bold"))
    style.configure("PanelAlert.TLabel", background=PANEL, foreground=RED,
                    font=font(10, "bold"))
    style.configure("PanelGood.TLabel", background=PANEL, foreground=GREEN,
                    font=font(10, "bold"))
    style.configure("Card.TLabel", background=PANEL_ALT)
    style.configure("CardDim.TLabel", background=PANEL_ALT, foreground=TEXT_DIM, font=font(9))
    style.configure("CardHeading.TLabel", background=PANEL_ALT, font=font(12, "bold"))
    style.configure("Selected.TLabel", background=ACCENT_SOFT)
    style.configure("SelectedDim.TLabel", background=ACCENT_SOFT, foreground=TEXT_DIM,
                    font=font(9))
    style.configure("SelectedHeading.TLabel", background=ACCENT_SOFT, font=font(12, "bold"))
    style.configure("Tag.TLabel", background=ACCENT, foreground=TEXT_DARK,
                    font=font(8, "bold"), padding=(6, 1))
    style.configure("Big.TLabel", background=PANEL, font=font(30, "bold"),
                    foreground=ACCENT)

    # Buttons
    style.configure("TButton", background=PANEL_ALT, foreground=TEXT, font=font(10),
                    borderwidth=1, relief="flat", padding=(12, 6), bordercolor=BORDER,
                    lightcolor=PANEL_ALT, darkcolor=PANEL_ALT)
    style.map("TButton",
              background=[("disabled", DISABLED_BG), ("pressed", ACCENT_DARK),
                          ("active", HOVER)],
              foreground=[("disabled", DISABLED_FG)],
              bordercolor=[("focus", ACCENT)])
    style.configure("Accent.TButton", background=ACCENT, foreground=TEXT_DARK,
                    font=font(10, "bold"), bordercolor=ACCENT,
                    lightcolor=ACCENT, darkcolor=ACCENT)
    style.map("Accent.TButton",
              background=[("disabled", DISABLED_BG), ("pressed", ACCENT_DARK),
                          ("active", "#45D6C8")],
              foreground=[("disabled", DISABLED_FG)])
    style.configure("Danger.TButton", foreground=RED)
    style.map("Danger.TButton", foreground=[("disabled", DISABLED_FG)])
    style.configure("Big.TButton", font=font(11, "bold"), padding=(18, 9))
    style.configure("BigAccent.TButton", background=ACCENT, foreground=TEXT_DARK,
                    font=font(11, "bold"), padding=(18, 9), bordercolor=ACCENT,
                    lightcolor=ACCENT, darkcolor=ACCENT)
    style.map("BigAccent.TButton",
              background=[("disabled", DISABLED_BG), ("pressed", ACCENT_DARK),
                          ("active", "#45D6C8")],
              foreground=[("disabled", DISABLED_FG)])

    # Entry, checkbuttons
    style.configure("TEntry", fieldbackground=PANEL_ALT, foreground=TEXT,
                    insertcolor=TEXT, bordercolor=BORDER, padding=6,
                    lightcolor=PANEL_ALT, darkcolor=PANEL_ALT)
    style.map("TEntry", bordercolor=[("focus", ACCENT)])
    for name, bg in (("TCheckbutton", BG), ("Card.TCheckbutton", PANEL_ALT),
                     ("Selected.TCheckbutton", ACCENT_SOFT), ("Panel.TCheckbutton", PANEL)):
        style.configure(name, background=bg, foreground=TEXT, font=font(10),
                        indicatorbackground=PANEL, indicatorforeground=ACCENT,
                        indicatormargin=4, focuscolor=bg)
        style.map(name, background=[("active", bg)],
                  indicatorbackground=[("selected", ACCENT_SOFT), ("active", HOVER)])

    # Scrollbar
    style.configure("Vertical.TScrollbar", background=PANEL_ALT, troughcolor=PANEL,
                    bordercolor=PANEL, arrowcolor=TEXT_DIM, lightcolor=PANEL_ALT,
                    darkcolor=PANEL_ALT)
    style.map("Vertical.TScrollbar", background=[("active", HOVER)])

    # Treeview (mission history)
    style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, rowheight=26, bordercolor=BORDER, font=font(10),
                    lightcolor=PANEL, darkcolor=PANEL)
    style.map("Treeview", background=[("selected", ACCENT_SOFT)],
              foreground=[("selected", TEXT)])
    style.configure("Treeview.Heading", background=PANEL_ALT, foreground=TEXT_DIM,
                    font=font(9, "bold"), relief="flat", bordercolor=BORDER,
                    lightcolor=PANEL_ALT, darkcolor=PANEL_ALT, padding=(6, 4))
    style.map("Treeview.Heading", background=[("active", HOVER)])
    return style
