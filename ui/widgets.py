"""Small reusable widget: the "Label:  value" info row of the gameplay sidebar."""

from tkinter import ttk


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
