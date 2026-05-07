import json
from pathlib import Path

from . import ui
from .config import APP_CONFIG


def handle_show_config() -> None:
    ui.print_config(APP_CONFIG)
    ui.press_enter_to_continue()


def handle_about() -> None:
    summary_path = Path(APP_CONFIG["data_root"]) / "data_summary.json"
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
    else:
        summary = {"note": "data_summary.json not found"}
    ui.print_data_summary(summary)
    ui.press_enter_to_continue()


def handle_sfl() -> None:
    from . import condition

    # --- INPUT ---
    csv_path = ui.select_condition_csv("A")
    if csv_path is None:
        return

    try:
        conditions_df = condition.load_conditions(csv_path, "A")
    except (FileNotFoundError, ValueError) as e:
        ui.print_error(str(e))
        ui.press_enter_to_continue()
        return

    ui.print_condition_table(conditions_df)

    # --- ANALYSIS (stub) ---
    # Computation not yet implemented.

    # --- OUTPUT ---
    ui.press_enter_to_continue()


def handle_dfl() -> None:
    ui.console.print("[cyan]Dynamic Flight Loads (DFL) — not yet implemented.[/cyan]")
    ui.press_enter_to_continue()


def handle_sgl() -> None:
    ui.console.print("[cyan]Static Ground Loads (SGL) — not yet implemented.[/cyan]")
    ui.press_enter_to_continue()


def handle_dgl() -> None:
    ui.console.print("[cyan]Dynamic Ground Loads (DGL) — not yet implemented.[/cyan]")
    ui.press_enter_to_continue()


def handle_flaps() -> None:
    ui.console.print("[cyan]Flap / High-Lift Loads (FLAPS) — not yet implemented.[/cyan]")
    ui.press_enter_to_continue()


def handle_view_lra() -> None:
    from . import lra

    # --- INPUT ---
    lra_path = ui.select_lra_file()
    if lra_path is None:
        return

    try:
        data = lra.load_lra(lra_path)
    except (ValueError, KeyError) as e:
        ui.print_error(str(e))
        ui.press_enter_to_continue()
        return

    # --- OUTPUT ---
    ui.print_lra_table(data["surface"], data["stations"])
    ui.press_enter_to_continue()


def handle_atmos_check() -> None:
    from . import atmos
    from .unit_convert import FT_M, KTS_M_S

    # --- INPUT ---
    unit_h = ui.ask_unit("altitude", "m", "ft")
    raw_h = ui.prompt_float(f"Pressure altitude ({unit_h})", 0, 52000)
    h_m = raw_h * FT_M if unit_h == "ft" else raw_h
    if h_m > atmos.H_MAX_M:
        ui.print_error(f"Altitude {h_m:.0f} m exceeds maximum {atmos.H_MAX_M:.0f} m")
        ui.press_enter_to_continue()
        return

    unit_v = ui.ask_unit("equivalent airspeed", "m/s", "kts")
    raw_v = ui.prompt_float(f"Equivalent airspeed ({unit_v})", 0, 600)
    v_eas_m_s = raw_v * KTS_M_S if unit_v == "kts" else raw_v

    # --- ANALYSIS ---
    v_tas_m_s = atmos.eas_to_tas(v_eas_m_s, h_m)
    a_m_s = atmos.speed_of_sound(h_m)
    state = {
        "rho_kg_m3": atmos.density(h_m),
        "p_pa":      atmos.pressure(h_m),
        "t_k":       atmos.temperature(h_m),
        "a_m_s":     a_m_s,
        "v_tas_m_s": v_tas_m_s,
        "mach_nd":   v_tas_m_s / a_m_s,
        "q_dyn_pa":  atmos.dynamic_pressure(v_tas_m_s, h_m),
    }

    # --- OUTPUT ---
    ui.print_atmos_table(h_m, v_eas_m_s, state)
    ui.press_enter_to_continue()


def handle_controls_deferred() -> None:
    ui.console.print("[dim]Control Surface Loads (CONTROLS) is deferred to Phase 2.[/dim]")
    ui.press_enter_to_continue()
