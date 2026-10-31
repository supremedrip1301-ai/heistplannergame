"""Colours, fonts and the ttk Style for the whole game.

Every colour used anywhere in the UI is defined here once, as a named
constant, so no hex code is repeated across files.
"""

import tkinter.font as tkfont
from tkinter import ttk

# ---------------------------------------------------------------- base palette (light theme)
BG = "#F3F5F9"            # window background
PANEL = "#FFFFFF"         # main panels
PANEL_ALT = "#EBEFF5"     # cards, raised areas
BORDER = "#C8D1DD"
HOVER = "#DDE4EE"
TEXT = "#1B2433"
TEXT_DIM = "#5A6779"
TEXT_ON_ACCENT = "#FFFFFF"   # text on coloured buttons and badges

ACCENT = "#0E8C80"        # teal: navigation, selection, route
ACCENT_DARK = "#0A6B62"
ACCENT_HOVER = "#12A394"
ACCENT_SOFT = "#D3F0EC"
AMBER = "#B86E00"         # warnings, static fields
GREEN = "#14803C"         # success, extraction
RED = "#D42F35"           # drones, failure
DISABLED_BG = "#E4E8EE"
DISABLED_FG = "#9AA4B2"

# ---------------------------------------------------------------- map tiles
TILE_WALL = "#3C4A5E"
TILE_WALL_EDGE = "#4E5D73"
TILE_FLOOR = "#FAFBFD"
TILE_FLOOR_EDGE = "#DCE2EA"
TILE_STATIC = "#FBE7C2"
TILE_STATIC_MARK = AMBER
TILE_START = "#D3F0EC"
TILE_EXTRACTION = "#D9F5E2"
TILE_OBJECTIVE = "#FBF3C7"
ROUTE = ACCENT
CHARACTER = ACCENT
CHARACTER_RING = "#C9F1EB"
# hard-mission tiles and drones
KEYCARD = "#2563EB"
TILE_DOOR = "#F5E6D3"
DOOR_FRAME = "#A65A12"
TERMINAL_BODY = "#CBD5E1"
TERMINAL_SCREEN = KEYCARD
LASER_BEAM = RED
DRONE_BODY = RED
DRONE_RING = "#7A1418"
VISION = RED                 # drawn with a stipple, so the floor stays visible
VISION_STIPPLE = "gray50"     # dot pattern of the vision tiles (denser on the light floor)
VISION_NEXT = AMBER          # preview: where drones look after the next turn
MASTER = "#7C3AED"           # difficulty label colour for "Master"
EXPERT = "#E0561B"           # difficulty label colour for "Expert"

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
    style.configure("Tag.TLabel", background=ACCENT, foreground=TEXT_ON_ACCENT,
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
    style.configure("Accent.TButton", background=ACCENT, foreground=TEXT_ON_ACCENT,
                    font=font(10, "bold"), bordercolor=ACCENT,
                    lightcolor=ACCENT, darkcolor=ACCENT)
    style.map("Accent.TButton",
              background=[("disabled", DISABLED_BG), ("pressed", ACCENT_DARK),
                          ("active", ACCENT_HOVER)],
              foreground=[("disabled", DISABLED_FG)])
    style.configure("Danger.TButton", foreground=RED)
    style.map("Danger.TButton", foreground=[("disabled", DISABLED_FG)])
    style.configure("Big.TButton", font=font(11, "bold"), padding=(18, 9))
    style.configure("BigAccent.TButton", background=ACCENT, foreground=TEXT_ON_ACCENT,
                    font=font(11, "bold"), padding=(18, 9), bordercolor=ACCENT,
                    lightcolor=ACCENT, darkcolor=ACCENT)
    style.map("BigAccent.TButton",
              background=[("disabled", DISABLED_BG), ("pressed", ACCENT_DARK),
                          ("active", ACCENT_HOVER)],
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
