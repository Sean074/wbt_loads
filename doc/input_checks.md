# Input Data Checks

Input data checks are pre-analysis verification steps run before any loads batch
to confirm that the aerodynamic database, mass model, and LRA geometry are
self-consistent and plausible. They do not modify any data or write any output
files; they are purely diagnostic.

**Access paths:**
- `P` from the main menu → Pre-Analysis Checks submenu (Checks 1–6)
- `L` from the main menu → LRA Geometry Viewer (single or combined airplane)

All checks follow the `input → analysis → output` pattern from `doc/ui.md`.
The handler for each check lives in `src/menu.py`; the display functions live
in `src/ui.py`.

---

## Pre-Analysis Checks menu

Accessed via `P` from the main menu. The submenu loops until `0` is entered.

| Key | Check | Handler |
|---|---|---|
| 1 | Aero Data Review | `handle_precheck_aero_review()` |
| 2 | Mass Data Review | `handle_precheck_mass_review()` |
| 3 | VMT for User-Defined State | `handle_precheck_vmt_state()` |
| 4 | Trim Condition Check | `handle_precheck_trim_check()` |
| 5 | Inertia VMT (1g) | `handle_precheck_inertia_vmt()` |
| 6 | Control Derivatives | `handle_precheck_control_derivatives()` |
| 0 | Back to main menu | — |

Menu label strings are defined in `ui.print_precheck_menu()`. Do not duplicate
them elsewhere.

---

## Check 1 — Aero Data Review

**Purpose:** Verify the aerodynamic database before loads analysis. Confirms
strip coefficients are sensible, checks total-airplane CL and CM vs alpha are
physical, and exposes the lateral derivative CYβ from the vtail.

### Input flow — two-stage by design

The two stages are kept separate so that total-airplane sweeps (baseline only,
no control increments) are not contaminated by the increment files used for the
detailed strip display.

**Stage 1 — Total airplane composition (required)**

```
ui.select_total_airplane_files()
```

Lists all `aero_*.csv` files in `data/aero/` (excluding `aero_incr_*`). The
user selects every surface that contributes to the total airplane (wing, htail,
vtail, fuselage). At least one selection is enforced — empty input re-prompts
with an error.

Panel title: `"Total Airplane Components — select ALL contributing surfaces"`.

**Stage 2 — Detail surface for strip table and VMT**

```
ui.select_detail_surface(airplane_paths)
```

Single-select from the Stage 1 list. Skipped automatically when only one
surface was selected. The chosen surface is loaded again with any control
increment files selected in the next step.

**Remaining inputs (in order):**

1. `ui.select_aero_incr_files()` — zero or more `aero_incr_*.csv` files;
   applied only to the detail surface, not to the total-airplane sweep
2. `ui.select_lra_file()` — LRA JSON for the detail surface (needed for VMT)
3. `ui.prompt_float("Angle of attack (deg)", −30, 40)` → `alpha_deg`
4. `ui.prompt_float("Sideslip angle (deg)", −40, 40)` → `beta_deg`
5. Altitude: `ui.ask_unit("altitude", "m", "ft")` + `prompt_float`
6. EAS: `ui.ask_unit("equivalent airspeed", "m/s", "kts")` + `prompt_float`
7. `ui.prompt_float("Wing reference area s_ref (m²)", 1, 2000)` → `s_ref_m2`
8. `ui.prompt_float("Mean aerodynamic chord MAC (m)", 0.1, 50)` → `mac_m`

### Analysis

All Stage 1 surfaces are loaded **baseline-only** (no increment files) for the
total-airplane sweeps. The detail surface is loaded **with increment files** for
the strip table and VMT.

Atmospheric state: `atmos.eas_to_tas()`, `atmos.speed_of_sound()`,
`atmos.dynamic_pressure()`.

**Per-surface detail at nominal state (detail surface):**
- `aero_db.interpolate_strips(db, alpha_rad, beta_rad, mach_nd, deflections_rad)`
- `loads.compute_aero_vmt(...)` → `section_loads`
- `loads.compute_integrated_totals(...)` → `totals`

**Total-airplane alpha sweep (all Stage 1 surfaces, baseline only):**
- Sweep `alpha_deg` over `all_aero_dbs[0]["alpha_deg"]` grid
- For each α: call `loads.compute_integrated_totals()` per surface, sum
  `lift_n` and `m_pitch_nm`
- `CL = total_lift_n / (q_dyn_pa × s_ref_m2)`
- `CM = total_m_nm / (q_dyn_pa × s_ref_m2 × mac_m)`
- Linear regression of CL and CM vs alpha (radians) → CL0, CLα, CM0, CMα

**Total-airplane beta sweep (vtail surfaces only):**
- Sweep `beta_deg` over vtail's `beta_deg` grid at nominal alpha and Mach
- For vtail surfaces: `loads.compute_strip_normal_integral(cn, c_m, y_m, q_dyn_pa)`
  (vtail cn is body-y side force; wing/htail cancel symmetrically at zero beta)
- `CY = fy_total / (q_dyn_pa × s_ref_m2)`
- Linear regression of CY vs beta (radians) → CY0, CYβ
- Beta sweep is omitted when no vtail surface is in Stage 1

Prandtl-Glauert warning if Mach is outside database range.

### Output sequence

1. `[cyan]Total airplane: N surface(s) — <stem names>[/cyan]`
2. `ui.print_aero_strip_table()` — detail surface at (α, β, M)
3. `ui.print_aero_totals()` — detail surface lift, drag, pitching moment
4. `ui.show_vmt_plot()` — detail surface section loads (matplotlib, blocking)
5. `ui.show_cl_cm_alpha_plot()` — total-airplane CL and CM vs α (matplotlib)
6. `ui.show_cy_beta_plot()` — total-airplane CY vs β (matplotlib); omitted
   when no vtail
7. `ui.print_aero_derivative_table()` — CL0, CLα, CM0, CMα; + CY0, CYβ when
   vtail present

---

## Check 2 — Mass Data Review

**Purpose:** Parse the NASTRAN CONM2 mass model, verify total weight and CG
against a known reference value, and confirm the inertia VMT is plausible under
1g vertical loading.

### Inputs

1. `ui.select_mass_file()` — `.bdf` file from `data/mass/`
2. `ui.select_lra_file()` — LRA JSON for the surface to integrate mass onto
3. `Reference total mass (kg) for validation [Enter to skip]: ` — optional
   free-form prompt; invalid number → skipped with a warning

### Analysis

- `mass_model.load_mass_model(mass_path)` → `mass_data`
- `loads.compute_inertia_vmt(mass_data, nz_nd=1.0, stations)` — computes
  section loads from all CONM2 point masses at 1g vertical load factor

### Output sequence

1. `ui.print_mass_summary(mass_data)` — total mass, weight, CG (x/y/z),
   inertia tensor, CONM2 card count; SI and imperial columns
2. If reference mass supplied:
   `[cyan]Mass vs reference: {delta:+.1f} kg ({pct:+.2f}%)[/cyan]`
3. `ui.show_vmt_plot()` — 1g inertia VMT (matplotlib, blocking)

---

## Check 3 — VMT for User-Defined State

**Purpose:** Display the aerodynamic strip coefficients and section loads at
a fully user-specified flight state, including arbitrary control deflections.
Used to validate the aero database against CFD or wind-tunnel strip data at
known conditions.

### Inputs

1. `ui.select_aero_file()` — single baseline `aero_*.csv`
2. `ui.select_aero_incr_files()` — zero or more increment files
3. `ui.select_lra_file()` — LRA JSON for the surface
4. `ui.prompt_float("Angle of attack (deg)", −30, 40)` → `alpha_deg`
5. `ui.prompt_float("Sideslip angle (deg)", −40, 40)` → `beta_deg`
6. Altitude (m or ft)
7. EAS (m/s or kts)
8. `ui.prompt_control_deflections()` — elevator, aileron, rudder, flap,
   spoiler in degrees (Enter = 0.0 for each)

### Analysis

- `aero_db.load_aero_db(baseline_path, incr_paths)`
- Atmospheric state from `atmos` module
- `aero_db.interpolate_strips(db, alpha_rad, beta_rad, mach_nd, deflections_rad)`
  — Prandtl-Glauert warning if Mach is outside database range
- `loads.compute_aero_vmt(...)` → `section_loads`
- `loads.compute_integrated_totals(...)` → `totals`

### Output sequence

1. `ui.print_aero_strip_table()` — strip coefficients at (α, β, M)
2. `ui.print_aero_totals()` — integrated lift, drag, pitching moment
3. `ui.show_vmt_plot()` — aerodynamic section loads (matplotlib, blocking)

---

## Check 4 — Trim Condition Check

**Purpose:** Solve the rigid-body alpha trim for a given flight condition and
display the resulting trim state and aerodynamic VMT. Confirms the aero database
can produce a trimmed solution at the required CL.

### Inputs

Two data source modes (user selects at start):

**Mode 1 — Condition CSV:**

1. `ui.select_condition_csv("A")` — Category A condition CSV
2. `ui.print_condition_table()` displayed for reference
3. `ui.prompt_float("Condition row number (1-based)", 1, N)` — selects the row;
   `h_m`, `v_eas_m_s`, `nz_nd`, `m_ac_kg` read from that row

**Mode 2 — Manual entry:**

1. Altitude (m or ft)
2. EAS (m/s or kts)
3. `ui.prompt_float("Normal load factor (nz)", −3.0, 5.0)` → `nz_nd`
4. `ui.prompt_float("Aircraft mass (kg)", 1, 1e6)` → `m_ac_kg`

**Both modes then continue with:**

5. `ui.prompt_float("Wing reference area s_ref (m²)", 1, 2000)` → `s_ref_m2`
6. `ui.prompt_float("Mean aerodynamic chord MAC (m)", 0.1, 50)` → `mac_m`
7. `ui.select_aero_file()` — single baseline (no increments for trim check)
8. `ui.select_lra_file()` — LRA JSON

### Analysis

- Atmospheric state from `atmos` module
- `cl_required = (m_ac_kg × G_M_S2 × nz_nd) / (q_dyn_pa × s_ref_m2)`
- `loads.solve_rigid_alpha_trim(aero_db_data, mach_nd, cl_required, s_ref_m2)`
  — bisection solver; non-convergence prints `[yellow]` warning and continues
- `aero_db.interpolate_strips(db, trim_alpha_rad, 0.0, mach_nd)` — beta = 0
  for trim check
- `loads.compute_aero_vmt(...)` → `section_loads`
- `loads.compute_integrated_totals(...)` → `totals`

`solve_rigid_alpha_trim` is the pre-analysis simplified solver (bisection on CL
only; does not balance pitching moment). Use `trim.solve_trim` for formal loads
cases.

### Output sequence

1. `ui.print_trim_balance()` — trim alpha, achieved CL, unbalanced Cm,
   convergence status; condition ID in the panel title
2. `ui.print_aero_totals()` — lift, drag, pitching moment at trim
3. `ui.show_vmt_plot()` — aerodynamic section loads at trim (matplotlib)

---

## Check 5 — Inertia VMT (1g)

**Purpose:** Apply a 1g vertical inertia load to the mass model and display the
resulting inertia section loads. A focused version of Check 2 that skips the
mass validation step.

### Inputs

1. `ui.select_mass_file()` — `.bdf` file from `data/mass/`
2. `ui.select_lra_file()` — LRA JSON

### Analysis

- `mass_model.load_mass_model(mass_path)` → `mass_data`
- `loads.compute_inertia_vmt(mass_data, nz_nd=1.0, stations)` → `section_loads`

### Output sequence

1. `ui.print_mass_summary(mass_data)` — weight, CG, inertia tensor
2. `ui.show_vmt_plot()` — 1g inertia VMT (matplotlib, blocking)

---

## Check 6 — Control Derivatives

**Purpose:** Compute and display control surface effectiveness derivatives
(dCL/dδ and dCM/dδ) by sweeping each control's deflection grid at a nominal
flight state. Used to verify the aerodynamic increment tables before formal
trim computation.

### Inputs

1. `ui.select_aero_file()` — single baseline `aero_*.csv`
2. `ui.select_aero_incr_files()` — one or more `aero_incr_*.csv` (required;
   re-prompts with a warning if none selected and returns)
3. `ui.prompt_float("Angle of attack (deg)", −30, 40)` → `alpha_deg`
4. `ui.prompt_float("Sideslip angle (deg)", −40, 40)` → `beta_deg`
5. Altitude (m or ft)
6. EAS (m/s or kts)
7. `s_ref_m2` and `mac_m`

### Analysis

For each increment file:
- `aero_db.load_aero_db(baseline_path, [ipath])` → `db` (baseline + one control)
- Read `incr["defl_min_deg"]` and `incr["defl_max_deg"]` from `db["incr_data"][0]`
- Generate `n_pts = max(11, int(abs(d_max − d_min)) + 1)` deflection points
- For each deflection: `aero_db.interpolate_strips(db, ..., deflections_rad={ctrl_tag: d_rad})`
  → `loads.compute_integrated_totals()` → CL and CM at that deflection
- `np.polyfit(defl_rad_arr, cl_vals, 1)` → slope = dCL/dδ per rad;
  `slope × DEG_RAD` → per deg

### Output sequence

1. `ui.print_control_derivatives_table(ctrl_derivs)` — one row per control;
   columns: Control / dCL/dδ /rad / dCL/dδ /deg / dCM/dδ /rad / dCM/dδ /deg

If no increment files load successfully, a `[yellow]` warning is printed instead.

---

## LRA Geometry Viewer

Accessed via `L` from the main menu. Offers two sub-choices:

```
[cyan]LRA view:[/cyan]  1 = Single surface   2 = Total airplane
```

### Single-surface viewer

1. `ui.select_lra_file()` — one `lra_*.json`
2. `lra.load_lra(lra_path)` → `data`
3. `ui.print_lra_table(data["surface"], data["stations"])` — station table
4. `ui.show_lra_3d(surface, stations)` — Plotly Scatter3d in browser

`show_lra_3d` displays:
- LRA spine: cyan line + markers at all station positions
- Unit normals: gold line segments scaled to 8% of the spine bounding-box diagonal
- Station labels: white text; every other label when > 14 stations

### Combined airplane viewer

1. Scans `data/lra/lra_*.json` automatically — no file selection prompt
2. Loads all files; skips with `[yellow]` warning on error
3. `ui.show_lra_3d_airplane(surfaces)` — all LRA spines overlaid in one figure

`show_lra_3d_airplane` displays:
- One spine colour and normal colour per surface (fixed 6-entry palette)
- Legend entry per surface (surface name from LRA dict `"surface"` key)
- Station labels per surface, thinned when > 10 stations per surface
- `aspectmode="data"` enforces equal spatial scale

**Chart display rules (both viewers):**
- `fig.show()` (Plotly); opens the default browser automatically
- TUI prints `[cyan]Opening LRA 3D viewer in browser — close tab when done[/cyan]`
  (single) or `[cyan]Opening combined LRA viewer in browser — close tab when done[/cyan]`
  (combined) before `fig.show()`
- Missing `plotly` → `[red]Error: plotly unavailable: ...[/red]` and return
- `scene.aspectmode="data"` — always set; do not override

---

## UI function reference

Functions used exclusively by the input checks. Signatures and locations:

### Input / selection helpers (`src/ui.py`)

| Function | Purpose |
|---|---|
| `select_total_airplane_files() -> list[Path]` | Multi-select baseline aero files; ≥1 required; re-prompts on empty |
| `select_detail_surface(paths: list) -> Path` | Single-select from already-chosen list; auto-returns `paths[0]` if len == 1 |
| `select_aero_file() -> Path \| None` | Single-select one baseline aero file |
| `select_aero_incr_files() -> list[Path]` | Multi-select increment files; returns `[]` if none chosen |
| `select_lra_file() -> Path \| None` | Single-select one LRA JSON |
| `select_mass_file() -> Path \| None` | Single-select one mass BDF |
| `prompt_control_deflections() -> dict` | Prompts elevator/aileron/rudder/flap/spoiler in deg; Enter = 0.0 |

### Output helpers (`src/ui.py`)

| Function | Purpose |
|---|---|
| `print_aero_strip_table(aero_db, cn, cm, cc, alpha_deg, beta_deg, mach_nd)` | Per-strip coefficient table at queried state |
| `print_aero_totals(totals: dict)` | Integrated lift, drag, pitching moment; SI and imperial |
| `print_aero_derivative_table(derivatives: dict)` | CL0, CLα, CM0, CMα; + CY0, CYβ when present |
| `print_control_derivatives_table(ctrl_derivs: list)` | dCL/dδ and dCM/dδ per control |
| `print_mass_summary(mass_data: dict)` | Total mass, weight, CG, inertia tensor |
| `print_trim_balance(alpha_deg, delta_e_deg, cl_trim_nd, cm_trim_nd, residuals)` | Rigid trim result panel |
| `show_vmt_plot(y_m, station_ids, section_loads, title, surface)` | Matplotlib VMT: Vz, Mx, My vs spanwise station |
| `show_cl_cm_alpha_plot(alpha_deg, cl_nd, cm_nd, nominal_alpha_deg, title)` | Matplotlib CL and CM vs α sweep |
| `show_cy_beta_plot(beta_deg, cy_nd, nominal_beta_deg, title)` | Matplotlib CY vs β sweep |
| `show_lra_3d(surface, stations)` | Plotly single-surface LRA viewer |
| `show_lra_3d_airplane(surfaces: list)` | Plotly combined multi-surface LRA viewer |
| `print_condition_table(conditions_df)` | Condition CSV summary table |
