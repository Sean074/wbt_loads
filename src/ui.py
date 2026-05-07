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
    "E": "Flap / High-Lift Loads (FLAPS) — Phase 2 — deferred",
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
        if key in ("E", "F"):
            tbl.add_row(key, f"[dim]{label}[/dim]")
        else:
            tbl.add_row(key, label)

    console.print(Panel(tbl, title="[bold]Analysis Categories[/bold]", border_style="cyan"))

    valid = set("ABCD")
    while True:
        raw = pt_prompt("Select category: ").strip().upper()
        if raw in ("E", "F"):
            console.print(f"[dim]Category {raw} is deferred to Phase 2.[/dim]")
            continue
        if raw in valid:
            return raw
        console.print("[red]Invalid selection. Enter A, B, C, or D.[/red]")


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
    d = data_root / "aero"
    if not d.exists():
        print_error(f"Directory not found: {d}")
        return None
    files = sorted(f for f in d.glob("aero_*.csv") if not f.name.startswith("aero_incr_"))
    if not files:
        print_warning(f"No baseline aero_*.csv files found in {d}")
        return None
    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("File")
    for i, f in enumerate(files, 1):
        tbl.add_row(str(i), f.name)
    console.print(Panel(tbl, title="[bold]Aero Database Files[/bold]", border_style="cyan"))
    from prompt_toolkit.completion import WordCompleter
    completer = WordCompleter([f.name for f in files], sentence=True)
    while True:
        raw = pt_prompt("Select file: ", completer=completer).strip()
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


# ---------------------------------------------------------------------------
# Pre-analysis checks — display and prompts
# ---------------------------------------------------------------------------

def print_precheck_menu() -> None:
    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("Check")
    tbl.add_row("1", "Aero Data Review — strip table + VMT at selected state")
    tbl.add_row("2", "Mass Data Review — weight, CG, inertia + 1g VMT")
    tbl.add_row("3", "VMT for User-Defined State — validate aero model vs. CFD")
    tbl.add_row("4", "Trim Condition Check — rigid alpha trim, Cm residual")
    tbl.add_row("5", "Inertia VMT (1g) — apply 1g load, plot inertia distribution")
    tbl.add_row("0", "Back to main menu")
    console.print(Panel(tbl, title="[bold]Pre-Analysis Checks[/bold]", border_style="cyan"))


def select_aero_incr_files() -> list:
    """
    Multi-file selector for aerodynamic increment CSVs (aero_incr_*.csv).

    The user enters comma-separated indices or an empty line to select none.
    Returns a list of Path objects (possibly empty).
    """
    from pathlib import Path
    data_root = Path(APP_CONFIG["data_root"])
    d = data_root / "aero"
    if not d.exists():
        return []
    files = sorted(d.glob("aero_incr_*.csv"))
    if not files:
        console.print("[dim]No increment files found in data/aero/[/dim]")
        return []
    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column("Key", style="cyan")
    tbl.add_column("File")
    for i, f in enumerate(files, 1):
        tbl.add_row(str(i), f.name)
    console.print(Panel(tbl, title="[bold]Increment Files (optional)[/bold]", border_style="cyan"))
    raw = pt_prompt("Select increment files (comma-separated indices, Enter for none): ").strip()
    if not raw:
        return []
    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(files):
                selected.append(files[idx])
            else:
                print_warning(f"Index {part} out of range — skipped")
        else:
            match = [f for f in files if f.name == part]
            if match:
                selected.append(match[0])
            else:
                print_warning(f"File not found: {part} — skipped")
    return selected


def prompt_control_deflections() -> dict:
    """
    Prompt for control surface deflections in degrees.

    Returns a dict: {control_tag: deflection_deg} for each surface.
    User may press Enter (empty) to accept 0.0 for any surface.
    """
    console.print("[cyan]Enter control deflections (deg). Press Enter to use 0.0.[/cyan]")
    controls = [
        ("elevator",  "Elevator  delta_e_deg"),
        ("aileron",   "Aileron   delta_a_deg"),
        ("rudder",    "Rudder    delta_r_deg"),
        ("flap",      "Flap      delta_f_deg"),
        ("spoiler",   "Spoiler   delta_sp_deg"),
    ]
    result = {}
    for tag, label in controls:
        raw = pt_prompt(f"  {label}: ").strip()
        if not raw:
            result[tag] = 0.0
        else:
            try:
                result[tag] = float(raw)
            except ValueError:
                print_warning(f"Invalid value '{raw}' for {tag} — using 0.0")
                result[tag] = 0.0
    return result


def print_aero_strip_table(
    aero_db: dict,
    cn_sec_nd,
    cm_sec_nd,
    cc_sec_nd,
    alpha_deg: float,
    beta_deg: float,
    mach_nd: float,
) -> None:
    """Display a table of spanwise strip coefficients at the queried state."""
    tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl.add_column("y_m",      style="cyan", justify="right")
    tbl.add_column("c_m",      justify="right")
    tbl.add_column("cn_sec",   justify="right")
    tbl.add_column("cm_sec",   justify="right")
    tbl.add_column("cc_sec",   justify="right")
    y_vals = aero_db["y_m"]
    c_vals = aero_db["c_m"]
    for k in range(len(y_vals)):
        tbl.add_row(
            f"{y_vals[k]:.3f}",
            f"{c_vals[k]:.3f}",
            f"{cn_sec_nd[k]:.4f}",
            f"{cm_sec_nd[k]:.4f}",
            f"{cc_sec_nd[k]:.4f}",
        )
    title = (
        f"[bold]Strip Coefficients — α={alpha_deg:.1f}°  "
        f"β={beta_deg:.1f}°  M={mach_nd:.3f}[/bold]"
    )
    console.print(Panel(tbl, title=title, border_style="cyan"))


def print_aero_totals(totals: dict) -> None:
    """Display integrated lift, drag, and pitching moment."""
    from .unit_convert import N_LBF, NM_FTLBF
    tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl.add_column("Quantity",  style="cyan", justify="right")
    tbl.add_column("SI",        justify="right")
    tbl.add_column("Imperial",  justify="right")
    tbl.add_row("Lift",            f"{totals['lift_n']:.1f} N",
                f"{totals['lift_n'] * N_LBF:.1f} lbf")
    tbl.add_row("Drag",            f"{totals['drag_n']:.1f} N",
                f"{totals['drag_n'] * N_LBF:.1f} lbf")
    tbl.add_row("Pitching moment", f"{totals['m_pitch_nm']:.1f} N·m",
                f"{totals['m_pitch_nm'] * NM_FTLBF:.1f} ft·lbf")
    console.print(Panel(tbl, title="[bold]Integrated Totals[/bold]", border_style="cyan"))


def print_mass_summary(mass_model: dict) -> None:
    """Display total mass, weight, CG, and inertia tensor."""
    from .unit_convert import N_LBF, M_FT
    tbl1 = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl1.add_column("Quantity", style="cyan", justify="right")
    tbl1.add_column("SI",       justify="right")
    tbl1.add_column("Imperial", justify="right")
    tbl1.add_row("Total mass",   f"{mass_model['m_total_kg']:.2f} kg",   "")
    tbl1.add_row("Total weight", f"{mass_model['w_total_n']:.1f} N",
                 f"{mass_model['w_total_n'] * N_LBF:.1f} lbf")
    tbl1.add_row("CG x",         f"{mass_model['x_cg_m']:.3f} m",
                 f"{mass_model['x_cg_m'] * M_FT:.3f} ft")
    tbl1.add_row("CG y",         f"{mass_model['y_cg_m']:.3f} m",
                 f"{mass_model['y_cg_m'] * M_FT:.3f} ft")
    tbl1.add_row("CG z",         f"{mass_model['z_cg_m']:.3f} m",
                 f"{mass_model['z_cg_m'] * M_FT:.3f} ft")
    tbl1.add_row("CONM2 cards",  str(mass_model["n_masses"]), "")
    console.print(Panel(tbl1, title="[bold]Mass Summary[/bold]", border_style="cyan"))

    tbl2 = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl2.add_column("",    style="cyan", justify="right")
    tbl2.add_column("Ixx", justify="right")
    tbl2.add_column("Iyy", justify="right")
    tbl2.add_column("Izz", justify="right")
    tbl2.add_column("Ixy", justify="right")
    tbl2.add_column("Ixz", justify="right")
    tbl2.add_column("Iyz", justify="right")
    tbl2.add_row(
        "kg·m²",
        f"{mass_model['i_xx_kg_m2']:.1f}",
        f"{mass_model['i_yy_kg_m2']:.1f}",
        f"{mass_model['i_zz_kg_m2']:.1f}",
        f"{mass_model['i_xy_kg_m2']:.1f}",
        f"{mass_model['i_xz_kg_m2']:.1f}",
        f"{mass_model['i_yz_kg_m2']:.1f}",
    )
    console.print(Panel(tbl2, title="[bold]Inertia Tensor (about CG)[/bold]", border_style="cyan"))


def print_trim_balance(
    alpha_deg: float,
    delta_e_deg: float,
    cl_trim_nd: float,
    cm_trim_nd: float,
    residuals: dict,
) -> None:
    """Display rigid-trim result: trim alpha, achieved CL, and unbalanced Cm."""
    tbl = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    tbl.add_column("Quantity", style="cyan", justify="right")
    tbl.add_column("Value",    justify="right")
    tbl.add_row("Trim alpha (deg)",        f"{alpha_deg:.3f}")
    tbl.add_row("Elevator (deg)",          f"{delta_e_deg:.3f}")
    tbl.add_row("CL achieved",             f"{cl_trim_nd:.4f}")
    tbl.add_row("Cm (unbalanced)",         f"{cm_trim_nd:.4f}")
    for key, val in residuals.items():
        tbl.add_row(key.replace("_", " "), f"{val:.2e}")
    converged = residuals.get("cl_residual", 1.0) < 1e-3
    status = "[green]Converged[/green]" if converged else "[yellow]Not converged[/yellow]"
    console.print(Panel(tbl, title=f"[bold]Rigid Trim Result — {status}[/bold]", border_style="cyan"))


def show_vmt_plot(
    y_m,
    station_ids: list,
    section_loads,
    title: str,
    surface: str,
) -> None:
    """
    Open a matplotlib figure with three subplots: Vz, Mx, My vs. spanwise station.

    Computes running shear and moment by integrating the per-station load
    concentrations from tip to root (cumulative sum from outboard to inboard).

    Handles headless environments by catching RuntimeError and printing an error.
    """
    import numpy as np
    try:
        import matplotlib
        if _try_display():
            matplotlib.use("TkAgg")
        else:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print_error(f"matplotlib unavailable: {exc}")
        return

    y_m           = np.asarray(y_m, dtype=float)
    section_loads = np.asarray(section_loads, dtype=float)
    N = len(y_m)

    # Sort stations by y (ascending = inboard to outboard)
    sort_idx  = np.argsort(y_m)
    y_sorted  = y_m[sort_idx]
    sl_sorted = section_loads[sort_idx]  # (N, 6)

    vz_st = sl_sorted[:, 0]  # per-station Vz concentrations
    mx_st = sl_sorted[:, 3]  # per-station Mx concentrations
    my_st = sl_sorted[:, 4]  # per-station My concentrations

    # Running shear: V[j] = Σ_{k>=j} Vz[k]  (tip to root)
    vz_run = np.cumsum(vz_st[::-1])[::-1]

    # Running bending moment: M[j] = Σ_{k>=j} (Vz[k]×(y[k]-y[j]) + Mx[k])
    # Efficient O(N): M[j] = (Σ_{k>=j} Vz[k]×y[k]) − y[j]×V[j] + (Σ_{k>=j} Mx[k])
    vzy = vz_st * y_sorted
    s_vzy  = np.cumsum(vzy[::-1])[::-1]
    s_mx   = np.cumsum(mx_st[::-1])[::-1]
    mx_run = s_vzy - y_sorted * vz_run + s_mx

    # Running torsion: T[j] = Σ_{k>=j} My[k]
    my_run = np.cumsum(my_st[::-1])[::-1]

    ids = [station_ids[i] for i in sort_idx]

    try:
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        fig.suptitle(f"{title} — {surface}", fontsize=12)

        axes[0].bar(range(N), vz_run, color="#00bfff", edgecolor="none")
        axes[0].set_ylabel("Vz [N]")
        axes[0].axhline(0, color="white", linewidth=0.5)
        axes[0].grid(True, alpha=0.3)

        axes[1].bar(range(N), mx_run, color="#ff8c00", edgecolor="none")
        axes[1].set_ylabel("Mx [N·m]")
        axes[1].axhline(0, color="white", linewidth=0.5)
        axes[1].grid(True, alpha=0.3)

        axes[2].bar(range(N), my_run, color="#9acd32", edgecolor="none")
        axes[2].set_ylabel("My [N·m]")
        axes[2].axhline(0, color="white", linewidth=0.5)
        axes[2].grid(True, alpha=0.3)

        axes[2].set_xticks(range(N))
        axes[2].set_xticklabels(ids, rotation=30, ha="right", fontsize=8)

        fig.tight_layout()
        console.print("[cyan]Displaying VMT chart — close window to continue[/cyan]")
        plt.show()
    except RuntimeError as exc:
        print_error(f"No display available for chart: {exc}")
    finally:
        plt.close("all")


def _try_display() -> bool:
    """Return True if a graphical display is likely available."""
    import os
    import sys
    return (
        sys.platform == "darwin"
        or bool(os.environ.get("DISPLAY"))
        or bool(os.environ.get("WAYLAND_DISPLAY"))
    )
