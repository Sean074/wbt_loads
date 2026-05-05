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
│  src/loads.py       — loads summation to LRA/grid  │
│  src/aeroelastic.py — aeroelastic corrections      │
│  src/lra.py         — loads reference axis + grid  │
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
│  data/conditions/ — condition list files           │
│  data/outputs/    — generated results              │
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
│   ├── aero_db.py           # Computation — aero DB import and interpolation
│   ├── mass_model.py        # Computation — distributed mass (NASTRAN CONM2)
│   ├── trim.py              # Computation — trim solver
│   ├── maneuver.py          # Computation — maneuver time history
│   ├── gust.py              # Computation — discrete & continuous gust loads
│   ├── loads.py             # Computation — loads summation to LRA/grid points
│   ├── aeroelastic.py       # Computation — aeroelastic corrections + jig shape
│   ├── lra.py               # Data model — loads reference axis and grid
│   ├── unit_convert.py      # Support — conversion constants only
│   └── config.py            # Support — config file loader
│
├── config/
│   └── defaults.json        # Tunable solver/display parameters
│
├── data/
│   ├── aero/                # Aerodynamic strip load database files
│   ├── mass/                # NASTRAN CONM2 mass model files
│   ├── lra/                 # Loads reference axis definition files
│   ├── conditions/          # Condition list files (maneuvers, flight conditions)
│   └── outputs/             # Generated runtime artifacts (not committed)
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

### `src/loads.py` — Loads summation

Sums aerodynamic strip loads and inertia loads to the LRA and grid reporting
points. Produces the final distributed load arrays for output.

**Allowed to import:** `aero_db`, `mass_model`, `lra`, `unit_convert`

**Must not contain:** display logic, trim or maneuver logic.

---

### `src/aeroelastic.py` — Aeroelastic corrections

Applies aeroelastic corrections using the elastic model (influence coefficients /
stiffness matrix). Computes aeroelastic effectiveness and determines the jig shape
from the cruise condition.

**Allowed to import:** `aero_db`, `loads`, `lra`, `numpy`, `scipy`

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
| `src/menu.py` | computation modules, `ui`, `config` |
| `src/ui.py` | `rich`, `prompt_toolkit`, `config` |
| `src/aero_db.py` | `numpy`, `scipy`, `pandas`, `unit_convert`, `config` |
| `src/mass_model.py` | `numpy`, `pandas` |
| `src/lra.py` | `numpy` |
| `src/trim.py` | `aero_db`, `mass_model`, `lra`, `numpy`, `scipy`, `unit_convert`, `config` |
| `src/maneuver.py` | `aero_db`, `mass_model`, `lra`, `trim`, `numpy`, `scipy`, `unit_convert` |
| `src/gust.py` | `aero_db`, `mass_model`, `lra`, `numpy`, `scipy`, `unit_convert`, `config` |
| `src/loads.py` | `aero_db`, `mass_model`, `lra`, `unit_convert` |
| `src/aeroelastic.py` | `aero_db`, `loads`, `lra`, `numpy`, `scipy` |
| `src/unit_convert.py` | nothing |
| `src/config.py` | stdlib only (`json`, `pathlib`) |

No computation module may import from the presentation layer (`ui.py`, `menu.py`,
`main.py`).

---

## Data flow

```
User selects menu item
        │
        ▼
menu.py handler
  ├── ui.py       ← prompts user for inputs / file selection
  ├── trim.py     ← solve balanced flight state
  ├── loads.py    ← sum aero + inertia loads to LRA/grid
  └── ui.py       ← render result tables / panels
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

## Adding new features

**New load case or maneuver type:**
Add to `maneuver.py` if time-history based, or to `loads.py` for static cases.
Add a condition type identifier to the condition list format. Add a menu handler
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

## What does not belong in the source tree

- Generated output files (`data/outputs/`) — runtime artifacts, not committed.
- Raw aero/mass data files added for a specific project — place in `instance/`.
- Exploratory notebooks and scratch scripts — place in `tools/`.
- The `example_docs/` directory is reference material from another project and
  is not part of this application.
