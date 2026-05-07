import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import prompt as pt_prompt

from src import menu, ui

_MENU_ITEMS = [
    ("A", "Static Flight Loads (SFL)"),
    ("B", "Dynamic Flight Loads (DFL)"),
    ("C", "Static Ground Loads (SGL)"),
    ("D", "Dynamic Ground Loads (DGL)"),
    ("E", "Flap / High-Lift Loads (FLAPS)"),
    ("F", "[dim]Control Surface Loads (CONTROLS) — Phase 2 — deferred[/dim]"),
    ("P", "Pre-analysis Checks"),
    ("L", "View LRA"),
    ("T", "Atmosphere check"),
    ("S", "Show config"),
    ("I", "About / data summary"),
    ("Q", "Quit"),
]

_HANDLERS = {
    "A": menu.handle_sfl,
    "B": menu.handle_dfl,
    "C": menu.handle_sgl,
    "D": menu.handle_dgl,
    "E": menu.handle_flaps,
    "F": menu.handle_controls_deferred,
    "P": menu.handle_precheck_menu,
    "L": menu.handle_view_lra,
    "T": menu.handle_atmos_check,
    "S": menu.handle_show_config,
    "I": menu.handle_about,
}


def _render_menu() -> None:
    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("Item")
    for key, label in _MENU_ITEMS:
        tbl.add_row(key, label)
    ui.console.print(Panel(tbl, title="[bold]WBT Loads[/bold]", border_style="cyan"))


def main() -> None:
    while True:
        ui.console.print()
        _render_menu()
        raw = pt_prompt("Select option: ").strip().upper()
        if raw == "Q":
            ui.console.print("[cyan]Goodbye.[/cyan]")
            break
        handler = _HANDLERS.get(raw)
        if handler:
            handler()
        else:
            ui.console.print("[red]Invalid selection.[/red]")


if __name__ == "__main__":
    main()
