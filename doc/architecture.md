# Architecture

This document defines the structure and design principles of the WBT Loads codebase.
It is the authoritative reference for where code belongs, how modules interact,
and why the structure is organised the way it is.

---

## Design principles

1. **Strict layering** — each layer depends only on layers below it; no upward
   dependencies.
2. **Single responsibility** — each module has one job; mixing concerns
   (e.g. computation inside display code) is a defect.
3. **Input → Analysis → Output** — the workflow pattern in every handler; stages
   are never skipped or interleaved.
4. **No global mutable state** — modules communicate through function arguments
   and return values, not shared globals.

---

## Layer diagram

```
┌────────────────────────────────────────────────────┐
│  Entry point                                       │
│  main.py                                           │
└──────────────────────┬─────────────────────────────┘
                       │ calls
┌──────────────────────▼─────────────────────────────┐
│  Presentation layer                                │
│  src/ui.py       — display, prompts                │
│  src/menu.py     — handler functions               │
└──────────────────────┬─────────────────────────────┘
                       │ calls
┌──────────────────────▼─────────────────────────────┐
│  Computation layer                                 │
│  src/aero_db.py     — aero database import + interp│
│  src/mass_model.py  — distributed mass (CONM2)     │
│  src/trim.py        — trim solver                  │
│  src/maneuver.py    — maneuver time history        │
│  src/gust.py        — discrete & continuous gust loads │
│  src/ground.py      — static & dynamic ground loads│
│  src/loads.py       — loads summation to LRA/grid  │
│  src/aero_trim.py   — coupled aeroelastic trim loop │
│  src/aeroelastic.py — aeroelastic corrections      │
│  src/beam.py        — sbeam BDF + modal ROM        │
│  src/lra.py         — loads reference axis + grid  │
│  src/atmos.py       — US Std Atmosphere 1976       │
└──────────────────────┬─────────────────────────────┘
                       │ uses
┌──────────────────────▼─────────────────────────────┐
│  Support layer                                     │
│  src/unit_convert.py — conversion constants        │
│  src/config.py       — settings loader             │
└──────────────────────┬─────────────────────────────┘
                       │ reads / writes
┌──────────────────────▼─────────────────────────────┐
│  Data files                                        │
│  config/defaults.json                              │
│  data/aero/       — aerodynamic database files     │
│  data/mass/       — NASTRAN CONM2 mass files       │
│  data/lra/        — loads reference axis files     │
│  data/conditions/                                  │
│    ├── static_flight/  — Category A CSVs           │
│    ├── dynamic_flight/ — Category B CSVs           │
│    ├── static_ground/  — Category C CSVs           │
│    ├── dynamic_ground/ — Category D CSVs           │
│    ├── flap/           — Category E (Phase 2)       │
│    └── control_surface/— Category F (Phase 2)      │
│  data/outputs/    — generated results              │
│    ├── <ac_id>_<cycle_id>_<case_id>.dat            │
│    │     NASTRAN FORCE/MOMENT per load case (all   │
│    │     surfaces in one file; load cycle ID is    │
│    │     user-defined at write time)               │
│    ├── <ac_id>_<cycle_id>_<component>_VMT.csv      │
│    │     VMT section load tables per surface       │
│    └── analysis_summary_<date>.out                 │
│          input file manifest — paths, mod dates    │
└────────────────────────────────────────────────────┘
```

---

## Directory structure

```
wbt_loads/
│
├── main.py                  # Entry point — startup, workflow menu loop
│
├── src/                     # All application source modules
│   ├── menu.py              # Presentation — menu handler functions
│   ├── ui.py                # Presentation — display and prompt helpers
│   ├── condition.py         # Data model — condition CSV parser (all analysis types)
│   ├── aero_db.py           # Computation — aero DB import and interpolation
│   ├── mass_model.py        # Computation — distributed mass (NASTRAN CONM2)
│   ├── trim.py              # Computation — trim solver
│   ├── maneuver.py          # Computation — maneuver time history
│   ├── gust.py              # Computation — discrete & continuous gust loads
│   ├── ground.py            # Computation — static & dynamic ground loads
│   ├── loads.py             # Computation — loads summation to LRA/grid points
│   ├── aero_trim.py         # Computation — coupled aeroelastic trim iteration
│   ├── aeroelastic.py       # Computation — aeroelastic corrections + jig shape
│   ├── beam.py              # Computation — sbeam BDF parser + modal ROM
│   ├── lra.py               # Data model — loads reference axis and grid
│   ├── atmos.py             # Computation — US Standard Atmosphere 1976
│   ├── nastran_out.py       # Output — NASTRAN FORCE/MOMENT card writer
│   ├── unit_convert.py      # Support — conversion constants only
│   └── config.py            # Support — config file loader
│
├── config/
│   └── defaults.json        # Tunable solver/display parameters
│
├── data/
│   ├── aero/                # Aerodynamic strip load database files
│   ├── mass/                # NASTRAN CONM2 mass model files
│   ├── gear/                # Landing gear design data (stroke, efficiency)
│   ├── lra/                 # Loads reference axis definition files
│   ├── conditions/          # Condition list files — six analysis type subdirectories
│   │   ├── static_flight/   #   Category A — static flight loads (LOAD_CASE output)
│   │   ├── dynamic_flight/  #   Category B — dynamic flight loads / gust
│   │   ├── static_ground/   #   Category C — static ground handling
│   │   ├── dynamic_ground/  #   Category D — landing and dynamic ground
│   │   ├── flap/            #   Category E — flap / high-lift loads (Phase 2; empty)
│   │   └── control_surface/ #   Category F — control surface loads (Phase 2; empty)
│   ├── outputs/             # Generated runtime artifacts (not committed)
│   └── data_summary.json    # Provenance: data source, analyst, analysis intent
│
│ The data/ root path is user-configurable via "data_root" in config/defaults.json.
│ The default is data/ relative to the project root. All subdirectory names are
│ fixed; only the root path changes.
│
├── doc/                     # Authoritative coding standards
│   ├── architecture.md      # This file
│   ├── analysis_code.md     # Variable naming and analysis method conventions
│   ├── loads_aero_db.md     # Aerodynamic database file format and interpolation method
│   └── ui.md                # TUI code standards
│
├── tools/                   # Standalone scripts; not imported by the app
│
├── WBT_Loads.md             # Project specification
├── CLAUDE.md                # Claude Code guidance
└── README.md                # Project overview
```

---

## Module responsibilities

### `main.py` — Entry point

Owns the application lifecycle: file selection on startup, the top-level workflow
menu loop, and clean shutdown. It is the only place that renders the top-level
menu panel.

**Allowed to import:** `src/menu`, `src/ui`, `src/config`

**Must not contain:** computation logic, display formatting, or file I/O beyond
what is required to start the app.

---

### `src/menu.py` — Menu handlers

One handler function per workflow step. Each handler follows the strict
**input → analysis → output** pattern defined in `doc/ui.md`:

1. Collect all inputs (via `ui` helpers or file selection).
2. Call the computation engine.
3. Display results via `ui` helpers.
4. Call `ui.press_enter_to_continue()`.

**Allowed to import:** all computation modules, `ui`, `config`

**Must not contain:** raw `print()`/`input()` calls, physics calculations.

---

### `src/ui.py` — Display and prompts

All terminal I/O lives here. Exposes a single shared `Console` instance used by
both `ui.py` and `menu.py`. See `doc/ui.md` for full conventions.

**Allowed to import:** `rich`, `prompt_toolkit`, `config`

**Must not contain:** computation logic.

---

### `src/condition.py` — Condition CSV parser

Parses condition list CSVs for any of the six analysis type categories (A–F).
Validates that the required columns for the selected analysis type are present,
converts all `_deg` control-deflection columns to `_rad` via `DEG_RAD`, and
returns a structured DataFrame (one row per condition).

The `analysis_type` argument selects which set of required columns is validated:
`"A"` through `"F"` correspond to the categories in `decision.md §9`.

**Allowed to import:** `pandas`, `unit_convert`, `config`

**Must not contain:** display logic, computation logic, or file I/O beyond CSV
reading via `pandas.read_csv`.

---

### `src/aero_db.py` — Aerodynamic database

Loads aerodynamic strip data (Cn, Cm, Cc) and control surface / rate increments
from file. Interpolates for a given flight state (α, β, p, q, r, δ). Returns
strip load arrays over the spanwise grid.

Strip data covers: wing, vertical stabiliser, horizontal stabiliser, fuselage.
Control surface deflections are treated as increments on the main surface. Rate
corrections (pitch, roll, yaw) are also increments.

File format, column schema, and interpolation method are specified in
`doc/loads_aero_db.md`.

**Allowed to import:** `numpy`, `scipy`, `pandas`, `unit_convert`, `config`

**Must not contain:** display logic, trim or maneuver logic.

---

### `src/mass_model.py` — Distributed mass model

Parses NASTRAN CONM2 format mass files (CID=0, global frame). Returns distributed
point masses with position vectors.

**Allowed to import:** `numpy`, `pandas`

**Must not contain:** display logic.

---

### `src/lra.py` — Loads reference axis

Defines the Loads Reference Axis as a piecewise-linear 3-D spine of oriented
reference points. Each surface (wing, HT, VT, fuselage) has an independent LRA
loaded from its own JSON file. The spine may be kinked (e.g. winglets); station
ordering is defined by the user in the JSON file, not enforced by a single
monotone spatial axis. Provides helpers to assign strip positions to the nearest
LRA station via minimum 3-D distance to the spine, and to integrate strip loads
to discrete section cuts.

The inertia and aerodynamic loads are both summed to the LRA reporting points.

**Allowed to import:** `json`, `pathlib`, `numpy`

**Must not contain:** display logic or aerodynamic data.

---

### `src/atmos.py` — US Standard Atmosphere 1976 (Decision 30)

Computes altitude-dependent atmospheric properties per US Standard Atmosphere
1976: density (`rho_kg_m3`), pressure (`p_static_pa`), temperature (`t_k`),
and speed of sound (`a_m_s`) from geopotential altitude `h_m`. Also provides
EAS↔TAS conversion and dynamic pressure helpers.

**Self-contained by design (Decision 30):** no other WBT_LOADS module is
imported. The module can be imported and called independently of the rest of
the program — users may use it in standalone tools or scripts with no other
WBT_LOADS dependencies.

Public functions (all inputs and outputs SI; no configuration parameters):

```python
def temperature(h_m: float) -> float          # → t_k (K)
def pressure(h_m: float) -> float             # → p_static_pa (Pa)
def density(h_m: float) -> float              # → rho_kg_m3 (kg/m³)
def speed_of_sound(h_m: float) -> float       # → a_m_s (m/s)
def eas_to_tas(v_eas_m_s: float, h_m: float) -> float     # → v_tas_m_s (m/s)
def dynamic_pressure(v_tas_m_s: float, h_m: float) -> float  # → q_dyn_pa (Pa)
```

US Std Atm 1976 constants are module-level literals; no `unit_convert` import
needed. Range: sea level (0 m) to ~15 545 m (~51 000 ft) — subsonic envelope.

**Allowed to import:** `math`, `numpy` — nothing else.

**Used by:** `trim.py`, `maneuver.py`, `gust.py`

---

### `src/trim.py` — Trim solver

Solves for the balanced flight state (α, elevator δe, thrust) for a given
condition (altitude, speed, load factor, CG). Uses a root-finding solver
(scipy) with convergence tolerance drawn from `APP_CONFIG`.

**Allowed to import:** `aero_db`, `mass_model`, `lra`, `numpy`, `scipy`,
`unit_convert`, `config`

**Must not contain:** display logic.

---

### `src/maneuver.py` — Maneuver time history

Time history integration for dynamic maneuvers (pull-up, push-over, rolling
pull-out, yaw). Produces loads as a function of time using scipy ODE integration.

**Allowed to import:** `aero_db`, `mass_model`, `lra`, `trim`, `numpy`, `scipy`,
`unit_convert`

**Must not contain:** display logic.

---

### `src/gust.py` — Gust loads

Implements two Phase 1 gust load paths:

1. **Static equivalent discrete gust (pre-Amendment 25-86):** computes
   `k_gust_nd`, `mu_g_nd`, and `delta_nz_nd` from the pre-1996 FAR design gust
   velocities. Returns `delta_nz_nd` as an increment on the trim load factor for
   consumption by `loads.py`. Condition routing: `maneuver_type` in
   `{discrete_gust_vertical, discrete_gust_lateral}`.

2. **2-DOF rigid-body continuous turbulence:** assembles the 2-DOF plunge-pitch
   system matrices from aircraft mass properties and strip-theory derivatives,
   computes complex FRFs `h_nz_nd(jω)` and `h_my_nm(jω)`, evaluates the Von
   Kármán PSD `phi_u_m2_s(ω)`, integrates numerically to produce RMS loads
   `sigma_nz_nd` and `sigma_my_nm`, and returns design limit loads
   (`k_sigma_nd × σ`). Condition routing: `maneuver_type == continuous_turbulence`.

Phase 2 deferred paths (1-cosine TDG, DLM-based PSD FRFs) will be added here.

**Allowed to import:** `aero_db`, `mass_model`, `lra`, `numpy`, `scipy`,
`unit_convert`, `config`

**Must not contain:** display logic, trim or maneuver logic.

---

### `src/ground.py` — Ground loads

Computes quasi-static ground loads for Categories C (Static Ground Loads) and
D (Dynamic Ground Loads). No aerodynamic loads; no time integration. All methods
are quasi-static in Phase 1. Provides three public functions:

- `compute_static_ground_loads` — Category C ground handling cases
  (braked roll, ground turn, nose-wheel yaw, towing, pivoting, jacking).
  Applies `nx_nd`, `ny_nd` inertia reactions and any applied external forces
  (brake torque, tow load, centrifugal) at their attachment points.

- `compute_landing_loads` — Category D.1 landing sub-cases (level, tail-down,
  one-gear, lateral drift, rebound). Uses the FAR 25.473 quasi-static reserve
  energy formula to compute the peak gear reaction from `v_sink_m_s`,
  `d_stroke_m`, and `eta_gear_nd`.

- `compute_taxi_braking_loads` — Category D.2 taxi/braking sub-cases (taxi bump,
  rough runway, abrupt braking). Reads `nz_bump_nd` or `nx_nd` directly from
  the condition row.

All three functions return a state dict with keys `applied_forces_n`,
`attach_positions_m`, `nz_nd`, `nx_nd`, `ny_nd`, and `condition_id`. The caller
(`menu.py`) passes this dict to `loads.compute_ground_loads()` for LRA summation.

**Allowed to import:** `mass_model`, `lra`, `numpy`, `unit_convert`, `config`

**Must not import:** `aero_db`, `trim`, `maneuver`, `gust`, `loads`, `aeroelastic`,
`beam` — the no-import of `aero_db` and `trim` enforces that ground cases carry
no aerodynamic contribution.

---

### `src/beam.py` — Beam model and modal ROM

Interfaces with the `sbeam` library (installed editable from
`/Users/seanomeara/Documents/99-Tests/sbeam`) to provide the structural
flexibility model needed by `aeroelastic.py`. Owns all beam-model I/O and
structural dynamics computation.

Three-step API:

1. **Parse** — `sbeam.parser.bdf_reader.parse_bdf(path)` reads the BDF file
   into a `BulkData` object. Imperial BDFs are converted to SI at ingestion
   via `unit_convert.py` before any assembler is called.

2. **Assemble** — `sbeam.assembly.stiffness.assemble_global_stiffness(bulk)` → K
   and `sbeam.assembly.mass_matrix.assemble_global_mass(bulk)` → M.

3. **Modal solve** — `sbeam.solver.sol103.solve(bulk, case_control)` →
   `Sol103Result` with `mode_shapes` Φ, `eigenvalues` ω², `frequencies_hz`.
   Forms the modal-reduced system: K_modal = diag(ω²), M_modal = I,
   D_modal = diag(2ζᵢωᵢ).

Exposes `get_K()`, `get_M()`, and `get_flexibility()` for use by
`aeroelastic.py`. The modal truncated flexibility matrix is
F_flex = Φ Λ⁻¹ Φᵀ where Λ = diag(ω²).

**Allowed to import:** `sbeam`, `numpy`, `scipy`, `unit_convert`, `config`

**Must not contain:** display logic.

---

### `src/loads.py` — Loads summation

Sums aerodynamic strip loads and inertia loads to the LRA and grid reporting
points. Produces the final distributed load arrays for output.

**Allowed to import:** `aero_db`, `mass_model`, `lra`, `unit_convert`

**Must not contain:** display logic, trim or maneuver logic, envelope accumulation.

---

### `src/nastran_out.py` — NASTRAN FORCE/MOMENT card writer

Formats the per-condition section loads from `loads.py` as NASTRAN bulk data
FORCE and MOMENT cards and writes them to `data/outputs/`. One FORCE card and
one MOMENT card are written per LRA station per condition. The NASTRAN load set
ID (SID) equals the condition sequence number in the condition list.

**Allowed to import:** `lra`, `unit_convert`, stdlib (`pathlib`, `io`)

**Must not contain:** computation logic, display logic, envelope selection.

---

### `src/aero_trim.py` — Coupled aeroelastic trim (Decision 13)

Owns the flexible-body trim iteration: the convergence loop that alternates
between the trim solver and the aeroelastic deflection correction until both
have converged simultaneously. This module exists so that neither `trim.py` nor
`aeroelastic.py` needs to import the other; the coupling is handled here.

Typical call sequence (internal):
1. `trim.solve_trim(...)` → rigid trim state
2. `aeroelastic.apply_corrections(rigid_state, ...)` → deflected shape + corrected loads
3. Repeat 1–2 until section load change < `APP_CONFIG["flex_tol"]`

`menu.py` calls `aero_trim.solve(...)` instead of calling `trim` and
`aeroelastic` directly for flight load conditions where elastic corrections are
active.

**Allowed to import:** `trim`, `aeroelastic`, `aero_db`, `lra`, `numpy`, `scipy`,
`unit_convert`, `config`

**Must not contain:** display logic, ground load logic.

---

### `src/aeroelastic.py` — Aeroelastic corrections

Applies aeroelastic corrections using the elastic model (influence coefficients /
stiffness matrix). Computes aeroelastic effectiveness and determines the jig shape
from the cruise condition.

**Control reversal (Decision 17):** when `e_flex_nd < 0` for any control surface
at any condition, `aeroelastic.py` raises a `ValueError` with the message
`"Control reversal: <surface> at condition <ID> (e_flex_nd = <value>)"`. The
calling handler in `menu.py` catches this, prints it as a `[red]Error[/red]`,
and returns to the menu without writing an output file. Control reversal is
treated as a hard error; the run is aborted for that condition.

**Allowed to import:** `aero_db`, `loads`, `lra`, `beam`, `numpy`, `scipy`

**Must not contain:** display logic.

---

### `src/unit_convert.py` — Conversion constants

Constants only. Pattern `<FROM>_<TO>` in `ALL_CAPS`. No functions, no imports.
See `doc/analysis_code.md` for the full reference.

**Must not contain:** any logic, imports, or mutable state.

---

### `src/config.py` — Configuration loader

Thin module. `from config import APP_CONFIG` returns the dict parsed from
`config/defaults.json`. Falls back to hardcoded defaults if the file is missing.

**Allowed to import:** stdlib only (`json`, `pathlib`)

**Must not contain:** application logic or direct knowledge of config keys.

---

## Dependency rules (summary)

| Module | May import |
|---|---|
| `main.py` | `src/menu`, `src/ui`, `src/config` |
| `src/menu.py` | computation modules, `condition`, `ui`, `config` |
| `src/ui.py` | `rich`, `prompt_toolkit`, `config` |
| `src/condition.py` | `pandas`, `unit_convert`, `config` |
| `src/aero_db.py` | `numpy`, `scipy`, `pandas`, `unit_convert`, `config` |
| `src/mass_model.py` | `numpy`, `pandas` |
| `src/lra.py` | `numpy` |
| `src/atmos.py` | `math`, `numpy` only — no other WBT_LOADS modules |
| `src/trim.py` | `atmos`, `aero_db`, `mass_model`, `lra`, `numpy`, `scipy`, `unit_convert`, `config` |
| `src/maneuver.py` | `atmos`, `aero_db`, `mass_model`, `lra`, `trim`, `numpy`, `scipy`, `unit_convert` |
| `src/gust.py` | `atmos`, `aero_db`, `mass_model`, `lra`, `numpy`, `scipy`, `unit_convert`, `config` |
| `src/ground.py` | `mass_model`, `lra`, `numpy`, `unit_convert`, `config` |
| `src/loads.py` | `aero_db`, `mass_model`, `lra`, `unit_convert` |
| `src/aero_trim.py` | `trim`, `aeroelastic`, `aero_db`, `lra`, `numpy`, `scipy`, `unit_convert`, `config` |
| `src/aeroelastic.py` | `aero_db`, `loads`, `lra`, `beam`, `numpy`, `scipy` |
| `src/beam.py` | `sbeam`, `numpy`, `scipy`, `unit_convert`, `config` |
| `src/unit_convert.py` | nothing |
| `src/config.py` | stdlib only (`json`, `pathlib`) |
| `src/nastran_out.py` | `lra`, `unit_convert`, stdlib only |
| `src/far_reg.py` | `unit_convert` only — deferred; module does not yet exist |

No computation module may import from the presentation layer (`ui.py`, `menu.py`,
`main.py`).

---

## Data flow

```
User selects "Run analysis" from main menu
        │
        ▼
ui.select_analysis_type()
    — numbered menu; Categories A–F; F labelled "(Phase 2 — deferred)"
        │
        ▼
ui.select_condition_csv(analysis_type)
    — lists CSVs in data/conditions/<type>/ subdirectory
        │
        ▼
condition.load_conditions(csv_path, analysis_type)
    — parses CSV; validates required columns for selected analysis type
        │
        ▼
menu.py handler iterates over all condition rows in the DataFrame:
  ├── (flight loads) trim.py / maneuver.py / gust.py
  │       ← solve flight state for the analysis sub-category
  ├── (ground loads) ground.py
  │       ← compute quasi-static ground reactions (Categories C, D)
  ├── loads.py        ← sum aero + inertia + applied loads to LRA/grid
  ├── nastran_out.py  ← write FORCE/MOMENT cards to data/outputs/
  └── (loop continues for next condition)
        │
        ▼
ui.print_batch_summary(results)
        │
        ▼
ui.press_enter_to_continue()
        │
        ▼
Returns to main menu loop (main.py)
```

For aeroelastic corrections:

```
menu.py handler
  ├── aero_db.py      ← load and interpolate strip data
  ├── loads.py        ← baseline loads summation
  └── aeroelastic.py
        ├── lra.py    ← resolve positions on LRA
        └── scipy     ← apply influence coefficient matrix
```

### Analysis sub-category routing

Each analysis category dispatches to computation modules based on
`maneuver_type`. The full routing table is:

| Sub-category | `maneuver_type` values | Computation path |
|---|---|---|
| A.1 Longitudinal – Balanced | `symmetric_pullup`, `pushover` | `trim` → `loads.compute_flight_loads` |
| A.2 Longitudinal – Maneuver | `checked` | `maneuver` ODE → `loads.compute_flight_loads` |
| A.3 Lateral – Balanced | *(see known limitation)* | `trim` → `loads.compute_flight_loads` |
| A.4 Lateral – Maneuver | `rolling_pullout`, `yaw` | `maneuver` ODE → `loads.compute_flight_loads` |
| B.1 PSD turbulence | `continuous_turbulence` | `gust` (2-DOF FRF) → `loads.compute_flight_loads` |
| B.2 Discrete gust | `discrete_gust_vertical`, `discrete_gust_lateral` | `gust` (static equiv.) → `loads.compute_flight_loads` |
| C SGL | `braked_roll`, `ground_turn`, `nose_wheel_yaw`, `towing`, `pivoting`, `jacking` | `ground.compute_static_ground_loads` → `loads.compute_ground_loads` |
| D.1 Landing | `level_landing`, `tail_down_landing`, `one_gear_landing`, `lateral_drift`, `rebound_landing` | `ground.compute_landing_loads` → `loads.compute_ground_loads` |
| D.2 Taxi/Braking | `taxi_bump`, `rough_runway`, `abrupt_braking` | `ground.compute_taxi_braking_loads` → `loads.compute_ground_loads` |
| E FLAPS | *(all)* | deferred — `_handle_flaps_deferred` shows Phase 2 message |
| F CONTROLS | *(all)* | deferred — `_handle_controls_deferred` shows Phase 2 message |

The `menu.py` top-level handler dict and per-category dispatch dicts are the
single authoritative routing implementation; they must match this table exactly.
The TUI abbreviations (SFL, DFL, SGL, DGL, FLAPS, CONTROLS) are defined in
`CATEGORY_LABELS` in `ui.py` and `CATEGORY_FILE_PREFIX` in `nastran_out.py`.

### Known Phase 1 limitation — A.3 static lateral balanced

`maneuver_type = "yaw"` routes to the maneuver ODE path (A.4 dynamic) in Phase 1.
A true static lateral balanced trim case (A.3 — steady sideslip equilibrium)
requires a new `maneuver_type = "balanced_lateral"` value, deferred to Phase 2.
See `decision.md §11` for the engineering workaround.

---

Downstream (external — not part of this application):

```
data/outputs/<aircraft_id>_<load_cycle_id>_<load_case_id>.dat
        │
        ▼ read by
CRITIC_LOADS (independent tool)
  ├── potato plots    ← multi-component interaction diagrams per load station
  ├── load envelope   ← critical case selection per component per station
  └── design summary  ← critical case ID, condition, and load by station
```

---

## Configuration vs. constants

| Type | Location | Examples |
|---|---|---|
| Physics constants (SI) | computation module level | `G_M_S2`, `RHO_0_KG_M3`, `P_0_PA`, `GAMMA` |
| Tunable parameters | `config/defaults.json` | solver tolerances, display options |
| Conversion factors | `unit_convert.py` | `DEG_RAD`, `KTS_M_S`, `FT_M`, `LBF_N`, `SLUG_KG` |
| Variable naming authority | `doc/aerospace_variables_reference.csv` | `code_variable_name` column |

Never move physics constants to config. Never hardcode conversion factors as bare
literals inside analysis functions.

All physics constants are in SI. If a regulatory equation requires imperial
quantities, use `unit_convert` constants to convert to imperial *within the
equation scope*, then convert the result back to SI immediately.

Variable names for aerodynamic, structural, and flight-state quantities are
defined in `doc/aerospace_variables_reference.csv` (`code_variable_name` column).
For project-specific quantities not in that file, follow the same convention:
all-lowercase, underscore-separated, SI unit suffix. See `doc/analysis_code.md`
for the full reference.

---

## CRITIC_LOADS interface — load envelope (Decision 7)

Decision 7 (`decision.md §7`) establishes that load envelope selection is the
responsibility of CRITIC_LOADS, an independent external post-processing tool.
WBT_LOADS is a **loads supplier only**; it does not compute or report a load
envelope internally.

### What WBT_LOADS produces

For each completed analysis run, `src/nastran_out.py` writes:

**NASTRAN loads file** (one per load case, all surfaces):
`<aircraft_id>_<load_cycle_id>_<load_case_id>.dat`

The `load_cycle_id` is a user-defined label entered in the TUI before the
output is written (e.g. `rev01`, `CycleA`). This provides traceability across
analysis iterations without embedding a date in the filename.

Contents:
- One **FORCE** card per LRA station per surface — components `(vx_n, fy_n, vz_n)`
  in the structural frame (x aft, y starboard, z up).
- One **MOMENT** card per LRA station per surface — components `(mx_nm, my_nm, mz_nm)`
  in the structural frame.
- Load set ID (SID) = condition sequence number in the condition list (1-based).
- Coordinate system ID (CID) = 0 (basic / global frame).
- Grid point IDs correspond to the LRA station index in the surface JSON file.

Both limit and ultimate values are written; ultimate cards are placed in a
separate load case block with SID offset by `10000 × n_conditions`.

**VMT summary CSV** (one per surface):
`<aircraft_id>_<load_cycle_id>_<component>_VMT.csv`

where `<component>` is the surface tag (e.g. `wing`, `htail`, `vtail`).

**Analysis summary** (one per output write session):
`analysis_summary_<YYYYMMDD>.out`

Lists every input file used (path and last-modified timestamp) so results are
traceable to the data revision used, without requiring hash embedding in the
input files themselves (Decision 27, Option B).

### What CRITIC_LOADS does (external — not implemented here)

CRITIC_LOADS reads the NASTRAN card output and applies the stress team's
envelope criteria:

- **Potato plots** — multi-component interaction diagrams in load-space (e.g.
  Vz vs. Mx, My vs. Vz) drawn at each load station as defined by the stress team.
  Cases whose load vector lies on or near the convex hull of the potato are the
  critical envelope candidates.
- **Additional criteria** — spar shear flow, gauge stresses, combined interaction
  checks, or other structural response quantities defined by the stress team.

Load station definitions used by CRITIC_LOADS are independent of the LRA station
definitions in WBT_LOADS. The stress team maps WBT_LOADS LRA grid points to their
own structural load stations when setting up CRITIC_LOADS.

### Module boundary

`src/nastran_out.py` is the only module in this application that writes the
NASTRAN output file (`.dat`), the VMT CSV tables, and the analysis summary
`.out` file. No other module writes to `data/outputs/` except via `nastran_out.py`
(for `.dat` / VMT / summary output) or the TUI chart helpers (for SMT matplotlib
windows). No application module may implement envelope accumulation, potato plot
logic, or critical case selection — those responsibilities belong entirely to
CRITIC_LOADS.

---

## FAR 23 provision (deferred to a future release)

Decision 6 (`decision.md §6`) selects Option C: FAR 23 is **not** implemented
in the initial release. FAR 25 / CS-25 is the sole regulatory basis. The
architecture is provisioned so that a future FAR 23 implementation requires no
structural changes to existing modules.

### Extension point 1 — `cert_basis` field in the condition list

A string column `cert_basis` will be added to the condition list CSV
(`data/conditions/`). Valid values: `"FAR25"` (default; assumed when the column
is absent) and `"FAR23"`. All existing FAR 25 conditions continue to work
unchanged because the column is optional and defaults to `"FAR25"`.

### Extension point 2 — `src/far_reg.py` in the support layer

FAR 23-specific regulatory formulas belong in a new **support-layer** module
`src/far_reg.py`, sitting at the same layer as `src/unit_convert.py` and
`src/config.py`.

Planned contents:
- `nz_maneuver_far23(m_ac_kg, category)` — maneuver load factor limits per
  FAR 23.337 for normal, utility, and acrobatic categories.
- `u_gust_far23_m_s(h_m)` — design gust velocity as a function of altitude
  per FAR 23.341.

**Dependency rule:** `src/far_reg.py` may import `src/unit_convert.py` only.
Computation modules (`maneuver.py`, `gust.py`) may import it. The presentation
layer must not import it directly. The module does not yet exist; when created,
the layer diagram and dependency table in this file must be updated.

### Extension point 3 — routing logic in `maneuver.py` and `gust.py`

When `cert_basis == "FAR23"`, `maneuver.py` and `gust.py` will branch to call
`far_reg.nz_maneuver_far23` and `far_reg.u_gust_far23_m_s` instead of the FAR
25 design values. The branch guard is a simple `if` on `cert_basis` at the top
of each relevant calculation block.

FAR 23 does **not** require continuous turbulence PSD analysis. When
`cert_basis == "FAR23"` and `maneuver_type == "continuous_turbulence"`, the
program must raise a `ValueError` indicating the case is not applicable under
FAR 23.

### What is not provisional

The LRA, aero database, mass model, trim solver, and loads summation modules are
regulation-agnostic by design — no changes to these modules are needed for FAR
23. The load factor `nz_nd` is already a user-supplied field, so an engineer can
analyse a GA aircraft today by supplying FAR 23-compliant values manually. Option
C defers *automated formula enforcement*, not the ability to analyse a GA aircraft.

---

## Program behavior conventions

### Non-convergence (Decision 23)

When the trim solver fails to converge for a condition:

1. Print `[yellow]Warning: trim did not converge for condition <ID>. Skipped.[/yellow]`.
2. Continue to the next condition in the batch.
3. Mark the condition as `SKIP` in the batch summary table.

Non-converged conditions appear in the batch summary with status `SKIP` and are
omitted from the NASTRAN output file. No output is written for a non-converged
condition. The analysis summary `.out` file notes each skipped condition.

### Single aircraft per session (Decision 24)

One aircraft configuration (aero database, mass file, LRA file, elastic model)
is loaded at startup and is fixed for the session. To switch configurations,
restart the program. `menu.py` must not implement a mid-session configuration
reload.

### FAR coverage validation (Decision 28)

WBT_LOADS does not check whether the supplied condition list is complete or
compliant with FAR 25 (e.g. that all required categories are present). Coverage
validation is the responsibility of the LOAD_CASE project and the responsible
engineer. WBT_LOADS validates only the column schema of the input CSV (required
columns present, correct types, SI units).

### Load combination for asymmetric cases (Decision 25)

Rolling pull-out section loads are the **direct algebraic sum** of the symmetric
pull-up component and the antisymmetric roll-rate component at each LRA station
(direct superposition per FAR 25.349). SRSS or partial-envelope combinations are
not used.

---

## Adding new features

**New load case or maneuver type:**
Add to `maneuver.py` if time-history based; to `gust.py` for gust/turbulence
cases; to `ground.py` for ground handling or landing cases; or to `loads.py`
for other static cases.
Add the new `maneuver_type` value to the enumeration in `decision.md §1b` and to
the appropriate per-type CSV schema in `decision.md §9`. Update `condition.py`
to validate the new column if type-specific columns are added. Add a menu handler
in `menu.py`. Add a display function to `ui.py` if the output shape differs from
existing tables.

**New aeroelastic capability:**
Extend `aeroelastic.py`. Follow variable naming conventions in
`doc/analysis_code.md`. Add the menu item and handler in `main.py` and `menu.py`.

**New config parameter:**
Add the key and default value to `config/defaults.json`. Read it in the consuming
module via `APP_CONFIG`. Do not add a new module-level constant for a tunable
parameter.

**New standalone tool or script:**
Place it in `tools/`. It must not be imported by any application module.

---

## tools/plot_vmt.py — Standalone VMT chart script (Decision 29)

`tools/plot_vmt.py` is a command-line script that reads saved VMT CSV files
and renders shear/moment/torque diagrams using `matplotlib`. It runs
independently — no WBT_LOADS application modules are imported; it requires
only `matplotlib`, `pandas`, and `numpy`.

**CLI usage:**
```
python tools/plot_vmt.py --file <path_to_VMT.csv>
                         [--conditions C001 C002 ...]
                         [--surface wing]
                         [--envelope <path_to_envelope.csv>]
```

Supported modes:
- Single case: plots Vz, Mx, My vs. spanwise station for one condition.
- Overlay: multiple `--conditions` arguments overlay all listed cases on the
  same axes.
- Vs envelope: `--envelope` argument overlays the condition against a
  reference envelope CSV.

Inertia and aerodynamic contributions are plotted as separate series on each
plot. The script calls `plt.show()` (blocking) and prints no TUI output.

**TUI integration (Decision 29, Option C):** the same capability is available
interactively from the TUI "Review cases" menu item, which calls
`ui.show_vmt_single`, `ui.show_vmt_compare`, and `ui.show_vmt_vs_envelope`
from `src/ui.py`. The two paths are independent implementations of the same
analysis; `tools/plot_vmt.py` does not import `src/ui.py` or any other
application module.

---

## What does not belong in the source tree

- Generated output files (`data/outputs/`) — runtime artifacts, not committed.
- Raw aero/mass data files added for a specific project — place in `instance/`.
- Exploratory notebooks and scratch scripts — place in `tools/`.
- The `example_docs/` directory is reference material from another project and
  is not part of this application.
