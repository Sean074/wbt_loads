from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import prompt as pt_prompt

from .config import APP_CONFIG

console = Console()

CATEGORY_LABELS = {
    "A": "Static Flight Loads (SFL)",
    "B": "Dynamic Flight Loads (DFL)",
    "C": "Static Ground Loads (SGL)",
    "D": "Dynamic Ground Loads (DGL)",
    "E": "Flap / High-Lift Loads (FLAPS)",
    "F": "Control Surface Loads (CONTROLS) — Phase 2 — deferred",
}

CATEGORY_SUBDIR = {
    "A": "static_flight",
    "B": "dynamic_flight",
    "C": "static_ground",
    "D": "dynamic_ground",
    "E": "flap",
    "F": "control_surface",
}

CATEGORY_FILE_PREFIX = {
    "A": "SFL",
    "B": "DFL",
    "C": "SGL",
    "D": "DGL",
    "E": "FLAPS",
    "F": "CONTROLS",
}


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------

def press_enter_to_continue() -> None:
    pt_prompt("\nPress Enter to continue...")


# ---------------------------------------------------------------------------
# Error / status messages
# ---------------------------------------------------------------------------

def print_error(msg: str) -> None:
    console.print(f"[red]Error: {msg}[/red]")


def print_warning(msg: str) -> None:
    console.print(f"[yellow]Warning: {msg}[/yellow]")


# ---------------------------------------------------------------------------
# Analysis-type selection
# ---------------------------------------------------------------------------

def select_analysis_type() -> str:
    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("Category")

    for key, label in CATEGORY_LABELS.items():
        if key == "F":
            tbl.add_row(key, f"[dim]{label}[/dim]")
        else:
            tbl.add_row(key, label)

    console.print(Panel(tbl, title="[bold]Analysis Categories[/bold]", border_style="cyan"))

    valid = set("ABCDE")
    while True:
        raw = pt_prompt("Select category: ").strip().upper()
        if raw == "F":
            console.print("[dim]Category F is deferred to Phase 2.[/dim]")
            continue
        if raw in valid:
            return raw
        console.print("[red]Invalid selection. Enter A, B, C, D, or E.[/red]")


def print_config(app_config: dict) -> None:
    tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan", justify="right")
    tbl.add_column("Value", justify="right")
    for k, v in app_config.items():
        tbl.add_row(k, str(v))
    console.print(Panel(tbl, title="[bold]Configuration[/bold]", border_style="cyan"))


def print_data_summary(summary: dict) -> None:
    tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl.add_column("Field", style="cyan", justify="right")
    tbl.add_column("Value", justify="right")
    for k, v in summary.items():
        tbl.add_row(k, str(v) if v else "[dim]—[/dim]")
    console.print(Panel(tbl, title="[bold]Data Summary[/bold]", border_style="cyan"))


def print_lra_table(surface: str, stations: list) -> None:
    tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl.add_column("Station", style="cyan", no_wrap=True)
    tbl.add_column("x_m", justify="right")
    tbl.add_column("y_m", justify="right")
    tbl.add_column("z_m", justify="right")
    tbl.add_column("nx", justify="right")
    tbl.add_column("ny", justify="right")
    tbl.add_column("nz", justify="right")
    for st in stations:
        pos = st["position_m"]
        n   = st["normal_nd"]
        tbl.add_row(
            st["station_id"],
            f"{pos[0]:.3f}", f"{pos[1]:.3f}", f"{pos[2]:.3f}",
            f"{n[0]:.4f}", f"{n[1]:.4f}", f"{n[2]:.4f}",
        )
    console.print(Panel(tbl, title=f"[bold]LRA — {surface}[/bold]", border_style="cyan"))


def print_condition_table(conditions_df) -> None:
    tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    display_cols = [c for c in conditions_df.columns if not c.endswith("_rad")]
    for col in display_cols:
        no_wrap = col in ("condition_id", "description", "maneuver_type")
        tbl.add_column(
            col,
            style="cyan" if col == "condition_id" else "",
            justify="left" if no_wrap else "right",
            no_wrap=no_wrap,
        )
    for _, row in conditions_df.iterrows():
        tbl.add_row(*[str(row[c]) for c in display_cols])
    console.print(Panel(tbl, title="[bold]Conditions[/bold]", border_style="cyan"))


# ---------------------------------------------------------------------------
# File-selection helpers
# ---------------------------------------------------------------------------

def _select_file(directory, pattern: str, panel_title: str):
    from pathlib import Path
    d = Path(directory)
    if not d.exists():
        print_error(f"Directory not found: {d}")
        return None
    files = sorted(d.glob(pattern))
    if not files:
        print_warning(f"No {pattern} files found in {d}")
        return None
    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("File")
    for i, f in enumerate(files, 1):
        tbl.add_row(str(i), f.name)
    console.print(Panel(tbl, title=f"[bold]{panel_title}[/bold]", border_style="cyan"))
    from prompt_toolkit.completion import WordCompleter
    names = [f.name for f in files]
    completer = WordCompleter(names, sentence=True)
    while True:
        raw = pt_prompt(f"Select file: ", completer=completer).strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(files):
                return files[idx]
            print_error(f"Index out of range: {raw}")
            continue
        match = [f for f in files if f.name == raw]
        if match:
            return match[0]
        print_error(f"File not found: {raw}")


def select_lra_file():
    from pathlib import Path
    data_root = Path(APP_CONFIG["data_root"])
    return _select_file(data_root / "lra", "lra_*.json", "LRA Files")


def select_mass_file():
    from pathlib import Path
    data_root = Path(APP_CONFIG["data_root"])
    return _select_file(data_root / "mass", "*.bdf", "Mass Model Files")


def select_aero_file():
    from pathlib import Path
    data_root = Path(APP_CONFIG["data_root"])
    return _select_file(data_root / "aero", "aero_*.csv", "Aero Database Files")


def select_condition_csv(analysis_type: str):
    from pathlib import Path
    subdir = CATEGORY_SUBDIR[analysis_type]
    data_root = Path(APP_CONFIG["data_root"])
    cond_dir = data_root / "conditions" / subdir

    if not cond_dir.exists():
        print_error(f"Condition directory not found: {cond_dir}")
        return None

    csv_files = sorted(cond_dir.glob("*.csv"))
    if not csv_files:
        print_warning(f"No CSV files found in {cond_dir}")
        return None

    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("File")
    for i, f in enumerate(csv_files, 1):
        tbl.add_row(str(i), f.name)

    console.print(Panel(tbl, title="[bold]Condition Files[/bold]", border_style="cyan"))

    from prompt_toolkit.completion import WordCompleter
    names = [f.name for f in csv_files]
    completer = WordCompleter(names, sentence=True)

    while True:
        raw = pt_prompt("Select condition file: ", completer=completer).strip()
        # Accept numeric index or filename
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(csv_files):
                return csv_files[idx]
            print_error(f"Index out of range: {raw}")
            continue
        match = [f for f in csv_files if f.name == raw]
        if match:
            return match[0]
        print_error(f"File not found: {raw}")


# ---------------------------------------------------------------------------
# Manual numeric input
# ---------------------------------------------------------------------------

def prompt_float(label: str, lo: float, hi: float,
                 soft_lo: float = None, soft_hi: float = None) -> float:
    from prompt_toolkit.validation import Validator, ValidationError

    class _RangeValidator(Validator):
        def validate(self, document):
            text = document.text.strip()
            try:
                val = float(text)
            except ValueError:
                raise ValidationError(message="Enter a number", cursor_position=len(text))
            if not (lo <= val <= hi):
                raise ValidationError(
                    message=f"Value must be between {lo} and {hi}",
                    cursor_position=len(text),
                )

    while True:
        raw = pt_prompt(f"{label}: ", validator=_RangeValidator(), validate_while_typing=False)
        val = float(raw.strip())
        if soft_lo is not None and val < soft_lo:
            console.print(f"[yellow]Warning: {val} is below the normal range "
                          f"({soft_lo}–{soft_hi}). Confirm? (y/n): [/yellow]", end="")
            confirm = pt_prompt("").strip().lower()
            if confirm not in ("y", "yes"):
                continue
        elif soft_hi is not None and val > soft_hi:
            console.print(f"[yellow]Warning: {val} is above the normal range "
                          f"({soft_lo}–{soft_hi}). Confirm? (y/n): [/yellow]", end="")
            confirm = pt_prompt("").strip().lower()
            if confirm not in ("y", "yes"):
                continue
        return val


def ask_unit(quantity: str, si_unit: str, alt_unit: str) -> str:
    console.print(f"[cyan]Unit for {quantity}:[/cyan] 1={si_unit}  2={alt_unit}")
    while True:
        raw = pt_prompt("Select unit (1/2): ").strip()
        if raw == "1":
            return si_unit
        if raw == "2":
            return alt_unit
        console.print("[red]Enter 1 or 2.[/red]")


def print_atmos_table(h_m: float, v_eas_m_s: float, state: dict) -> None:
    from .unit_convert import M_FT, M_S_KTS
    tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl.add_column("Quantity", style="cyan", justify="right")
    tbl.add_column("SI", justify="right")
    tbl.add_column("Aviation", justify="right")

    h_ft = h_m * M_FT
    v_kts = v_eas_m_s * M_S_KTS
    tbl.add_row("Altitude", f"{h_m:.1f} m", f"{h_ft:.0f} ft")
    tbl.add_row("EAS", f"{v_eas_m_s:.2f} m/s", f"{v_kts:.1f} kts")
    tbl.add_row("TAS", f"{state['v_tas_m_s']:.2f} m/s",
                f"{state['v_tas_m_s'] * M_S_KTS:.1f} kts")
    tbl.add_row("Density", f"{state['rho_kg_m3']:.4f} kg/m³", "")
    tbl.add_row("Pressure", f"{state['p_pa']:.1f} Pa", "")
    tbl.add_row("Temperature", f"{state['t_k']:.2f} K",
                f"{state['t_k'] - 273.15:.1f} °C")
    tbl.add_row("Speed of sound", f"{state['a_m_s']:.2f} m/s", "")
    tbl.add_row("Mach", f"{state['mach_nd']:.4f}", "")
    tbl.add_row("Dynamic pressure", f"{state['q_dyn_pa']:.1f} Pa", "")
    console.print(Panel(tbl, title="[bold]Atmosphere State[/bold]", border_style="cyan"))
