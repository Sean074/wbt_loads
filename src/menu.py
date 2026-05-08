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


def handle_flaps_deferred() -> None:
    ui.console.print("[dim]Flap / High-Lift Loads (FLAPS) is deferred to Phase 2.[/dim]")
    ui.press_enter_to_continue()


def handle_view_lra() -> None:
    from prompt_toolkit import prompt as pt_prompt

    ui.console.print("[cyan]LRA view:[/cyan]  1 = Single surface   2 = Total airplane")
    choice = pt_prompt("Select (1/2): ").strip()
    if choice == "2":
        _handle_view_lra_airplane()
        return

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
    ui.show_lra_3d(data["surface"], data["stations"])
    ui.press_enter_to_continue()


def _handle_view_lra_airplane() -> None:
    """Load all LRA JSON files and open combined 3D airplane viewer."""
    from pathlib import Path
    from . import lra

    lra_dir = Path(APP_CONFIG["data_root"]) / "lra"
    if not lra_dir.exists():
        ui.print_error(f"LRA directory not found: {lra_dir}")
        ui.press_enter_to_continue()
        return

    lra_files = sorted(lra_dir.glob("lra_*.json"))
    if not lra_files:
        ui.print_warning("No LRA files found in data/lra/")
        ui.press_enter_to_continue()
        return

    surfaces = []
    for lra_path in lra_files:
        try:
            surfaces.append(lra.load_lra(lra_path))
        except (ValueError, KeyError) as exc:
            ui.print_warning(f"Skipping {lra_path.name}: {exc}")

    if not surfaces:
        ui.print_error("No LRA data loaded.")
        ui.press_enter_to_continue()
        return

    names = ", ".join(d["surface"] for d in surfaces)
    ui.console.print(f"[cyan]{len(surfaces)} surface(s): {names}[/cyan]")
    ui.show_lra_3d_airplane(surfaces)
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


# ---------------------------------------------------------------------------
# Pre-analysis validation checks
# ---------------------------------------------------------------------------

def handle_precheck_menu() -> None:
    from prompt_toolkit import prompt as pt_prompt

    dispatch = {
        "1": handle_precheck_aero_review,
        "2": handle_precheck_mass_review,
        "3": handle_precheck_vmt_state,
        "4": handle_precheck_trim_check,
        "5": handle_precheck_inertia_vmt,
        "6": handle_precheck_control_derivatives,
    }
    while True:
        ui.console.print()
        ui.print_precheck_menu()
        raw = pt_prompt("Select check: ").strip()
        if raw == "0":
            return
        fn = dispatch.get(raw)
        if fn:
            fn()
        else:
            ui.console.print("[red]Enter 1-6 or 0 to go back.[/red]")


def handle_precheck_aero_review() -> None:
    """Check 1: Total airplane CL/CM vs alpha and derivatives; per-surface strip table and VMT."""
    import numpy as np
    from . import aero_db, lra, atmos, loads
    from .unit_convert import DEG_RAD, FT_M, KTS_M_S

    # --- INPUT ---
    # Step 1: all surfaces that compose the total airplane (required, ≥1)
    airplane_paths = ui.select_total_airplane_files()
    if not airplane_paths:
        return

    # Step 2: one of those surfaces for detailed strip table / VMT display
    baseline_path = ui.select_detail_surface(airplane_paths)

    incr_paths = ui.select_aero_incr_files()

    lra_path = ui.select_lra_file()
    if lra_path is None:
        return

    alpha_deg = ui.prompt_float("Angle of attack (deg)", -30.0, 40.0)
    beta_deg  = ui.prompt_float("Sideslip angle (deg)", -40.0, 40.0)

    unit_h = ui.ask_unit("altitude", "m", "ft")
    raw_h  = ui.prompt_float(f"Pressure altitude ({unit_h})", 0.0, atmos.H_MAX_M
                              if unit_h == "m" else atmos.H_MAX_M / FT_M)
    h_m = raw_h * FT_M if unit_h == "ft" else raw_h

    unit_v = ui.ask_unit("equivalent airspeed", "m/s", "kts")
    raw_v  = ui.prompt_float(f"Equivalent airspeed ({unit_v})", 0.0,
                              600.0 if unit_v == "m/s" else 600.0 / KTS_M_S)
    v_eas_m_s = raw_v * KTS_M_S if unit_v == "kts" else raw_v

    s_ref_m2 = ui.prompt_float("Wing reference area s_ref (m²)", 1.0, 2000.0)
    mac_m    = ui.prompt_float("Mean aerodynamic chord MAC (m)", 0.1, 50.0)

    # --- ANALYSIS ---
    # Load all airplane surfaces (baseline only — no increments — for total airplane sweep)
    all_aero_dbs = []
    for p in airplane_paths:
        try:
            all_aero_dbs.append(aero_db.load_aero_db(p))
        except (FileNotFoundError, ValueError) as exc:
            ui.print_error(str(exc))
            ui.press_enter_to_continue()
            return

    # Load detail surface with control increments for strip table / VMT
    try:
        aero_db_data = aero_db.load_aero_db(baseline_path, incr_paths)
    except (FileNotFoundError, ValueError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    try:
        lra_data = lra.load_lra(lra_path)
    except (ValueError, KeyError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    stations = lra_data["stations"]
    v_tas_m_s = atmos.eas_to_tas(v_eas_m_s, h_m)
    a_m_s     = atmos.speed_of_sound(h_m)
    mach_nd   = v_tas_m_s / a_m_s
    q_dyn_pa  = atmos.dynamic_pressure(v_tas_m_s, h_m)
    alpha_rad = alpha_deg * DEG_RAD
    beta_rad  = beta_deg  * DEG_RAD

    # Per-surface detail: strip coefficients and section loads at nominal state
    cn, cm, cc, pg_applied = aero_db.interpolate_strips(
        aero_db_data, alpha_rad, beta_rad, mach_nd
    )
    if pg_applied:
        ui.print_warning(
            f"Mach {mach_nd:.3f} outside database range "
            f"[{aero_db_data['mach_min_nd']:.2f} – {aero_db_data['mach_max_nd']:.2f}]. "
            f"Prandtl-Glauert extrapolation applied."
        )

    section_loads = loads.compute_aero_vmt(
        cn, cm, cc, aero_db_data["c_m"], aero_db_data["y_m"], q_dyn_pa, stations
    )
    totals = loads.compute_integrated_totals(
        cn, cm, cc, aero_db_data["c_m"], aero_db_data["y_m"], q_dyn_pa, alpha_rad
    )

    # Total airplane: sweep alpha across primary surface grid at nominal beta and mach
    alpha_grid_deg = all_aero_dbs[0]["alpha_deg"]
    cl_sweep = np.empty(len(alpha_grid_deg))
    cm_sweep = np.empty(len(alpha_grid_deg))

    for j, a_deg in enumerate(alpha_grid_deg):
        a_rad = a_deg * DEG_RAD
        total_lift_n = 0.0
        total_m_nm   = 0.0
        for db in all_aero_dbs:
            cn_j, cm_j, cc_j, _ = aero_db.interpolate_strips(db, a_rad, beta_rad, mach_nd)
            t = loads.compute_integrated_totals(
                cn_j, cm_j, cc_j, db["c_m"], db["y_m"], q_dyn_pa, a_rad
            )
            total_lift_n += t["lift_n"]
            total_m_nm   += t["m_pitch_nm"]
        cl_sweep[j] = total_lift_n / (q_dyn_pa * s_ref_m2)
        cm_sweep[j] = total_m_nm   / (q_dyn_pa * s_ref_m2 * mac_m)

    # Linear regression over full alpha range for airplane derivatives
    alpha_rad_arr = alpha_grid_deg * DEG_RAD
    cl_slope, cl_intercept = np.polyfit(alpha_rad_arr, cl_sweep, 1)
    cm_slope, cm_intercept = np.polyfit(alpha_rad_arr, cm_sweep, 1)
    n_surfaces = len(all_aero_dbs)
    derivatives = {
        "cl0_nd":           cl_intercept,
        "cl_alpha_per_rad": cl_slope,
        "cl_alpha_per_deg": cl_slope * DEG_RAD,
        "cm0_nd":           cm_intercept,
        "cm_alpha_per_rad": cm_slope,
        "cm_alpha_per_deg": cm_slope * DEG_RAD,
    }

    # Cy vs beta sweep — vtail is the primary contributor; wing/htail cancel symmetrically
    vtail_dbs = [db for db in all_aero_dbs if db["surface"] == "vtail"]
    if vtail_dbs:
        beta_grid_deg = vtail_dbs[0]["beta_deg"]
        cy_sweep = np.empty(len(beta_grid_deg))
        for j, b_deg in enumerate(beta_grid_deg):
            b_rad   = b_deg * DEG_RAD
            fy_n = 0.0
            for db in all_aero_dbs:
                if db["surface"] == "vtail":
                    cn_j, _, _, _ = aero_db.interpolate_strips(db, alpha_rad, b_rad, mach_nd)
                    fy_n += loads.compute_strip_normal_integral(
                        cn_j, db["c_m"], db["y_m"], q_dyn_pa
                    )
            cy_sweep[j] = fy_n / (q_dyn_pa * s_ref_m2)
        beta_rad_arr = beta_grid_deg * DEG_RAD
        cy_slope, cy_intercept = np.polyfit(beta_rad_arr, cy_sweep, 1)
        derivatives.update({
            "cy0_nd":          cy_intercept,
            "cy_beta_per_rad": cy_slope,
            "cy_beta_per_deg": cy_slope * DEG_RAD,
        })
    else:
        cy_sweep      = None
        beta_grid_deg = None

    # --- OUTPUT ---
    surface_names = ", ".join(p.stem for p in airplane_paths)
    ui.console.print(
        f"[cyan]Total airplane: {n_surfaces} surface(s) — {surface_names}[/cyan]"
    )
    ui.print_aero_strip_table(aero_db_data, cn, cm, cc, alpha_deg, beta_deg, mach_nd)
    ui.print_aero_totals(totals)
    y_stations  = np.array([s["position_m"][1] for s in stations])
    station_ids = [s["station_id"] for s in stations]
    ui.show_vmt_plot(y_stations, station_ids, section_loads,
                     title=f"Aero Review — {baseline_path.stem}", surface=lra_data["surface"])
    config_tag = all_aero_dbs[0]["config_tag"]
    ui.show_cl_cm_alpha_plot(
        alpha_grid_deg, cl_sweep, cm_sweep,
        nominal_alpha_deg=alpha_deg,
        title=f"Total Airplane CL / CM vs α — {n_surfaces} surfaces ({config_tag})",
    )
    if cy_sweep is not None:
        ui.show_cy_beta_plot(
            beta_grid_deg, cy_sweep,
            nominal_beta_deg=beta_deg,
            title=f"Total Airplane CY vs β — {n_surfaces} surfaces ({config_tag})",
        )
    ui.print_aero_derivative_table(derivatives)
    ui.press_enter_to_continue()


def handle_precheck_mass_review() -> None:
    """Check 2: Load mass model, display CG/inertia, plot 1g inertia VMT."""
    from . import mass_model, lra, loads
    from prompt_toolkit import prompt as pt_prompt
    import numpy as np

    # --- INPUT ---
    mass_path = ui.select_mass_file()
    if mass_path is None:
        return

    lra_path = ui.select_lra_file()
    if lra_path is None:
        return

    raw_ref = pt_prompt("Reference total mass (kg) for validation [Enter to skip]: ").strip()
    ref_mass_kg = None
    if raw_ref:
        try:
            ref_mass_kg = float(raw_ref)
        except ValueError:
            ui.print_warning("Invalid reference mass — skipped.")

    # --- ANALYSIS ---
    try:
        mass_data = mass_model.load_mass_model(mass_path)
    except (FileNotFoundError, ValueError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    try:
        lra_data = lra.load_lra(lra_path)
    except (ValueError, KeyError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    stations = lra_data["stations"]
    section_loads = loads.compute_inertia_vmt(mass_data, nz_nd=1.0, stations=stations)

    # --- OUTPUT ---
    ui.print_mass_summary(mass_data)
    if ref_mass_kg is not None:
        delta_kg = mass_data["m_total_kg"] - ref_mass_kg
        pct = 100.0 * delta_kg / ref_mass_kg
        ui.console.print(
            f"[cyan]Mass vs reference: {delta_kg:+.1f} kg ({pct:+.2f}%)[/cyan]"
        )

    y_stations  = np.array([s["position_m"][1] for s in stations])
    station_ids = [s["station_id"] for s in stations]
    ui.show_vmt_plot(y_stations, station_ids, section_loads,
                     title="Mass Review — 1g Inertia VMT", surface=lra_data["surface"])
    ui.press_enter_to_continue()


def handle_precheck_vmt_state() -> None:
    """Check 3: VMT at user-defined alpha/beta/controls to validate aero model vs. CFD."""
    from . import aero_db, lra, atmos, loads
    from .unit_convert import DEG_RAD, FT_M, KTS_M_S
    import numpy as np

    # --- INPUT ---
    baseline_path = ui.select_aero_file()
    if baseline_path is None:
        return

    incr_paths = ui.select_aero_incr_files()

    lra_path = ui.select_lra_file()
    if lra_path is None:
        return

    alpha_deg = ui.prompt_float("Angle of attack (deg)", -30.0, 40.0)
    beta_deg  = ui.prompt_float("Sideslip angle (deg)", -40.0, 40.0)

    unit_h = ui.ask_unit("altitude", "m", "ft")
    raw_h  = ui.prompt_float(f"Pressure altitude ({unit_h})", 0.0,
                              atmos.H_MAX_M if unit_h == "m" else atmos.H_MAX_M / FT_M)
    h_m = raw_h * FT_M if unit_h == "ft" else raw_h

    unit_v = ui.ask_unit("equivalent airspeed", "m/s", "kts")
    raw_v  = ui.prompt_float(f"Equivalent airspeed ({unit_v})", 0.0,
                              600.0 if unit_v == "m/s" else 600.0 / KTS_M_S)
    v_eas_m_s = raw_v * KTS_M_S if unit_v == "kts" else raw_v

    ctrl_deg = ui.prompt_control_deflections()

    # --- ANALYSIS ---
    try:
        aero_db_data = aero_db.load_aero_db(baseline_path, incr_paths)
    except (FileNotFoundError, ValueError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    try:
        lra_data = lra.load_lra(lra_path)
    except (ValueError, KeyError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    stations = lra_data["stations"]
    v_tas_m_s = atmos.eas_to_tas(v_eas_m_s, h_m)
    a_m_s     = atmos.speed_of_sound(h_m)
    mach_nd   = v_tas_m_s / a_m_s
    q_dyn_pa  = atmos.dynamic_pressure(v_tas_m_s, h_m)
    alpha_rad = alpha_deg * DEG_RAD
    beta_rad  = beta_deg  * DEG_RAD
    deflections_rad = {tag: deg * DEG_RAD for tag, deg in ctrl_deg.items()}

    cn, cm, cc, pg_applied = aero_db.interpolate_strips(
        aero_db_data, alpha_rad, beta_rad, mach_nd, deflections_rad
    )
    if pg_applied:
        ui.print_warning(
            f"Mach {mach_nd:.3f} outside database range "
            f"[{aero_db_data['mach_min_nd']:.2f} – {aero_db_data['mach_max_nd']:.2f}]. "
            f"Prandtl-Glauert extrapolation applied."
        )

    section_loads = loads.compute_aero_vmt(
        cn, cm, cc, aero_db_data["c_m"], aero_db_data["y_m"], q_dyn_pa, stations
    )
    totals = loads.compute_integrated_totals(
        cn, cm, cc, aero_db_data["c_m"], aero_db_data["y_m"], q_dyn_pa, alpha_rad
    )

    # --- OUTPUT ---
    ui.print_aero_strip_table(aero_db_data, cn, cm, cc, alpha_deg, beta_deg, mach_nd)
    ui.print_aero_totals(totals)
    y_stations  = np.array([s["position_m"][1] for s in stations])
    station_ids = [s["station_id"] for s in stations]
    ui.show_vmt_plot(y_stations, station_ids, section_loads,
                     title="VMT — User-Defined State", surface=lra_data["surface"])
    ui.press_enter_to_continue()


def handle_precheck_trim_check() -> None:
    """Check 4: Rigid alpha trim to match CL_required; display trim state and VMT."""
    from . import aero_db, lra, atmos, loads, condition
    from .unit_convert import FT_M, KTS_M_S
    from prompt_toolkit import prompt as pt_prompt
    import numpy as np

    # --- INPUT ---
    ui.console.print("[cyan]Trim data source:[/cyan]  1 = Condition CSV   2 = Manual entry")
    src = pt_prompt("Select (1/2): ").strip()

    if src == "1":
        csv_path = ui.select_condition_csv("A")
        if csv_path is None:
            return
        try:
            conditions_df = condition.load_conditions(csv_path, "A")
        except (FileNotFoundError, ValueError) as exc:
            ui.print_error(str(exc))
            ui.press_enter_to_continue()
            return
        ui.print_condition_table(conditions_df)
        row_idx = int(ui.prompt_float(
            "Condition row number (1-based)", 1.0, float(len(conditions_df))
        )) - 1
        row       = conditions_df.iloc[row_idx]
        h_m       = float(row["h_m"])
        v_eas_m_s = float(row["v_eas_m_s"])
        nz_nd     = float(row["nz_nd"])
        m_ac_kg   = float(row["m_ac_kg"])
        cond_id   = str(row["condition_id"])
    else:
        unit_h = ui.ask_unit("altitude", "m", "ft")
        raw_h  = ui.prompt_float(f"Pressure altitude ({unit_h})", 0.0,
                                  atmos.H_MAX_M if unit_h == "m" else atmos.H_MAX_M / FT_M)
        h_m = raw_h * FT_M if unit_h == "ft" else raw_h

        unit_v = ui.ask_unit("equivalent airspeed", "m/s", "kts")
        raw_v  = ui.prompt_float(f"Equivalent airspeed ({unit_v})", 0.0,
                                  600.0 if unit_v == "m/s" else 600.0 / KTS_M_S)
        v_eas_m_s = raw_v * KTS_M_S if unit_v == "kts" else raw_v

        nz_nd   = ui.prompt_float("Normal load factor (nz)", -3.0, 5.0)
        m_ac_kg = ui.prompt_float("Aircraft mass (kg)", 1.0, 1e6)
        cond_id = "MANUAL"

    s_ref_m2 = ui.prompt_float("Wing reference area s_ref (m²)", 1.0, 2000.0)
    mac_m    = ui.prompt_float("Mean aerodynamic chord MAC (m)", 0.1, 50.0)

    baseline_path = ui.select_aero_file()
    if baseline_path is None:
        return

    lra_path = ui.select_lra_file()
    if lra_path is None:
        return

    # --- ANALYSIS ---
    try:
        aero_db_data = aero_db.load_aero_db(baseline_path)
    except (FileNotFoundError, ValueError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    try:
        lra_data = lra.load_lra(lra_path)
    except (ValueError, KeyError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    stations  = lra_data["stations"]
    v_tas_m_s = atmos.eas_to_tas(v_eas_m_s, h_m)
    a_m_s     = atmos.speed_of_sound(h_m)
    mach_nd   = v_tas_m_s / a_m_s
    q_dyn_pa  = atmos.dynamic_pressure(v_tas_m_s, h_m)

    from .atmos import G_M_S2
    w_n           = m_ac_kg * G_M_S2
    cl_required   = (w_n * nz_nd) / (q_dyn_pa * s_ref_m2)

    trim_result = loads.solve_rigid_alpha_trim(
        aero_db_data, mach_nd, cl_required, s_ref_m2
    )

    if not trim_result["converged"]:
        ui.print_warning(
            f"Trim did not converge for condition {cond_id}. "
            f"CL required={cl_required:.4f}, achieved={trim_result['cl_trim_nd']:.4f}."
        )

    cn, cm, cc, pg_applied = aero_db.interpolate_strips(
        aero_db_data, trim_result["alpha_rad"], 0.0, mach_nd
    )
    if pg_applied:
        ui.print_warning(
            f"Mach {mach_nd:.3f} outside database range; Prandtl-Glauert applied."
        )

    section_loads = loads.compute_aero_vmt(
        cn, cm, cc, aero_db_data["c_m"], aero_db_data["y_m"], q_dyn_pa, stations
    )
    totals = loads.compute_integrated_totals(
        cn, cm, cc, aero_db_data["c_m"], aero_db_data["y_m"],
        q_dyn_pa, trim_result["alpha_rad"]
    )

    # --- OUTPUT ---
    ui.print_trim_balance(
        alpha_deg   = trim_result["alpha_deg"],
        delta_e_deg = 0.0,
        cl_trim_nd  = trim_result["cl_trim_nd"],
        cm_trim_nd  = trim_result["cm_trim_nd"],
        residuals   = {"cl_residual": trim_result["residual_cl"]},
    )
    ui.print_aero_totals(totals)
    y_stations  = np.array([s["position_m"][1] for s in stations])
    station_ids = [s["station_id"] for s in stations]
    ui.show_vmt_plot(y_stations, station_ids, section_loads,
                     title=f"Trim VMT — {cond_id}", surface=lra_data["surface"])
    ui.press_enter_to_continue()


def handle_precheck_control_derivatives() -> None:
    """Check 6: Sweep control deflection at nominal state; display dCL/dδ and dCM/dδ."""
    import numpy as np
    from . import aero_db, atmos, loads
    from .unit_convert import DEG_RAD, FT_M, KTS_M_S

    # --- INPUT ---
    baseline_path = ui.select_aero_file()
    if baseline_path is None:
        return

    incr_paths = ui.select_aero_incr_files()
    if not incr_paths:
        ui.print_warning("No increment files selected — nothing to compute.")
        ui.press_enter_to_continue()
        return

    alpha_deg = ui.prompt_float("Angle of attack (deg)", -30.0, 40.0)
    beta_deg  = ui.prompt_float("Sideslip angle (deg)", -40.0, 40.0)

    unit_h = ui.ask_unit("altitude", "m", "ft")
    raw_h  = ui.prompt_float(f"Pressure altitude ({unit_h})", 0.0,
                              atmos.H_MAX_M if unit_h == "m" else atmos.H_MAX_M / FT_M)
    h_m = raw_h * FT_M if unit_h == "ft" else raw_h

    unit_v = ui.ask_unit("equivalent airspeed", "m/s", "kts")
    raw_v  = ui.prompt_float(f"Equivalent airspeed ({unit_v})", 0.0,
                              600.0 if unit_v == "m/s" else 600.0 / KTS_M_S)
    v_eas_m_s = raw_v * KTS_M_S if unit_v == "kts" else raw_v

    s_ref_m2 = ui.prompt_float("Wing reference area s_ref (m²)", 1.0, 2000.0)
    mac_m    = ui.prompt_float("Mean aerodynamic chord MAC (m)", 0.1, 50.0)

    # --- ANALYSIS ---
    v_tas_m_s = atmos.eas_to_tas(v_eas_m_s, h_m)
    a_m_s     = atmos.speed_of_sound(h_m)
    mach_nd   = v_tas_m_s / a_m_s
    q_dyn_pa  = atmos.dynamic_pressure(v_tas_m_s, h_m)
    alpha_rad = alpha_deg * DEG_RAD
    beta_rad  = beta_deg  * DEG_RAD

    ctrl_derivs = []
    for ipath in incr_paths:
        try:
            db = aero_db.load_aero_db(baseline_path, [ipath])
        except (FileNotFoundError, ValueError) as exc:
            ui.print_warning(f"Skipping {ipath.name}: {exc}")
            continue

        incr     = db["incr_data"][0]
        ctrl_tag = incr["control_tag"]
        d_min    = incr["defl_min_deg"]
        d_max    = incr["defl_max_deg"]
        n_pts    = max(11, int(abs(d_max - d_min)) + 1)
        defl_grid_deg = np.linspace(d_min, d_max, n_pts)

        cl_vals = np.empty(n_pts)
        cm_vals = np.empty(n_pts)
        for j, d_deg in enumerate(defl_grid_deg):
            d_rad = d_deg * DEG_RAD
            cn_j, cm_j, cc_j, _ = aero_db.interpolate_strips(
                db, alpha_rad, beta_rad, mach_nd,
                deflections_rad={ctrl_tag: d_rad},
            )
            t = loads.compute_integrated_totals(
                cn_j, cm_j, cc_j, db["c_m"], db["y_m"], q_dyn_pa, alpha_rad
            )
            cl_vals[j] = t["lift_n"]       / (q_dyn_pa * s_ref_m2)
            cm_vals[j] = t["m_pitch_nm"]   / (q_dyn_pa * s_ref_m2 * mac_m)

        defl_rad_arr = defl_grid_deg * DEG_RAD
        cl_slope, _ = np.polyfit(defl_rad_arr, cl_vals, 1)
        cm_slope, _ = np.polyfit(defl_rad_arr, cm_vals, 1)
        ctrl_derivs.append({
            "control_tag":        ctrl_tag,
            "dcl_ddelta_per_rad": cl_slope,
            "dcl_ddelta_per_deg": cl_slope * DEG_RAD,
            "dcm_ddelta_per_rad": cm_slope,
            "dcm_ddelta_per_deg": cm_slope * DEG_RAD,
        })

    # --- OUTPUT ---
    if not ctrl_derivs:
        ui.print_warning("No control derivatives computed.")
    else:
        ui.print_control_derivatives_table(ctrl_derivs)
    ui.press_enter_to_continue()


def handle_precheck_inertia_vmt() -> None:
    """Check 5: Apply 1g vertical load to mass model and plot inertia VMT."""
    from . import mass_model, lra, loads
    import numpy as np

    # --- INPUT ---
    mass_path = ui.select_mass_file()
    if mass_path is None:
        return

    lra_path = ui.select_lra_file()
    if lra_path is None:
        return

    # --- ANALYSIS ---
    try:
        mass_data = mass_model.load_mass_model(mass_path)
    except (FileNotFoundError, ValueError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    try:
        lra_data = lra.load_lra(lra_path)
    except (ValueError, KeyError) as exc:
        ui.print_error(str(exc))
        ui.press_enter_to_continue()
        return

    stations = lra_data["stations"]
    section_loads = loads.compute_inertia_vmt(mass_data, nz_nd=1.0, stations=stations)

    # --- OUTPUT ---
    ui.print_mass_summary(mass_data)
    y_stations  = np.array([s["position_m"][1] for s in stations])
    station_ids = [s["station_id"] for s in stations]
    ui.show_vmt_plot(y_stations, station_ids, section_loads,
                     title="Inertia VMT — 1g", surface=lra_data["surface"])
    ui.press_enter_to_continue()
