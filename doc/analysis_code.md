# Analysis Code Standards — Variable Naming and Methods

Applies to all computation modules: `atmos.py`, `aero_db.py`, `mass_model.py`,
`lra.py`, `trim.py`, `maneuver.py`, `gust.py`, `ground.py`, `loads.py`,
`aero_trim.py`, `aeroelastic.py`, `beam.py`, and any helper functions called
from them. UI and menu code is excluded.

---

## Core rules

1. **Use the standard symbol where one exists.** Structural and aeronautical
   quantities have established symbols from ICAO, FAR/CS texts, and standard
   references (Lomax, Wright & Cooper). Prefer the symbol over an English
   description.

2. **Append the SI unit as a suffix, separated by `_`.** The suffix makes the unit
   visible at every point of use without reading the function signature.

3. **SI is the internal standard.** All computation module variables use SI.
   Input files in imperial are converted at ingestion; imperial-stated FAR
   empirical equations are evaluated with in-scope converted values and the result
   converted back to SI immediately. See `CLAUDE.md §Unit system` for the full
   policy.

4. **`doc/aerospace_variables_reference.csv` is the authoritative source for
   `code_variable_name`.** When a quantity appears in that file, its
   `code_variable_name` column entry is the required Python identifier. For
   project-specific quantities not in the CSV, follow the same convention:
   all-lowercase, underscore-separated, SI unit suffix.

Combined, the pattern is:

```
<symbol_or_description>_<SI-unit-abbreviation>
```

---

## Unit suffix reference

| Dimension | Suffix | Notes |
|---|---|---|
| Length / span / chord | `_m` | metres — primary |
| Area | `_m2` | square metres |
| Force | `_N` or `_n` | Newtons; constants use `_N`, variables use `_n` |
| Moment / torque | `_nm` | Newton-metres |
| Pressure / stress | `_pa` | Pascals |
| Distributed load | `_n_m` | force per unit span (N/m) |
| Distributed moment | `_nm_m` | moment per unit span (N·m/m) |
| Mass | `_kg` | kilograms |
| Speed | `_m_s` | metres per second |
| Angular rate | `_rad_s` | radians per second |
| Angle (internal) | `_rad` | radians — inside solvers and computation |
| Angle (display) | `_deg` | degrees — at user interface boundaries only |
| Time | `_s` | seconds |
| Dimensionless | `_nd` | coefficients, load factors, ratios |

Knots (`_kts`, `_keas`) are permitted **at the UI boundary only** and must be
converted to `_m_s` before being passed into any computation module.

---

## Unit conversion at ingestion boundaries

Imperial input files are converted to SI in the ingestion module before any
internal variable is assigned:

| Input source | Ingestion module | Conversion applied |
|---|---|---|
| NASTRAN CONM2 (feet / slugs) | `mass_model.py` | positions × `FT_M`, masses × `SLUG_KG` |
| Aero database (feet-based chord/span) | `aero_db.py` | chord/span × `FT_M` |
| FAR gust tables (fps, feet) | `gust.py` | velocities × `FPS_M_S`, distances × `FT_M` |
| Condition list (SI; control deflections in deg) | `condition.py` | `_deg` columns × `DEG_RAD`; no other conversion required |

FAR empirical equations stated in imperial (e.g. gust alleviation factor, gear
reserve energy) use locally-converted imperial intermediates. The result is
converted back to SI before the expression scope ends.

---

## Standard symbol tables

Variable names are drawn from `doc/aerospace_variables_reference.csv`.  The
`code_variable_name` column in that file is the required identifier; the tables
below repeat the relevant subset and add project-specific entries not covered
by the CSV.

### Flight state

| Quantity | Code variable | CSV symbol |
|---|---|---|
| Pressure altitude | `h_m` | *H* |
| True airspeed | `v_tas_m_s` | *V* (TAS) |
| Equivalent airspeed | `v_eas_m_s` | EAS |
| Calibrated airspeed | `v_cas_m_s` | CAS |
| Mach number | `mach_nd` | *M* |
| Dynamic pressure | `q_dyn_pa` | *q* |
| Angle of attack (internal) | `alpha_rad` | *α* |
| Sideslip angle (internal) | `beta_rad` | *β* |
| Roll rate | `p_roll_rad_s` | *p* |
| Pitch rate | `q_pitch_rad_s` | *q* (context-distinct from dynamic pressure) |
| Yaw rate | `r_yaw_rad_s` | *r* |
| Normal load factor | `nz_nd` | *n*_z |

Angles displayed at the UI boundary use `_deg` variants (`alpha_deg`,
`beta_deg`). Convert to `_rad` before passing to any computation module.

### Aerodynamic coefficients — section (strip) data

These are local aerodynamic coefficients defined in the section (body-normal)
axis, distinct from the stability-axis coefficients below.

| Quantity | Code variable | Symbol |
|---|---|---|
| Section normal force coefficient | `cn_sec_nd` | *C*_n (section) |
| Section pitching moment coefficient (c/4) | `cm_sec_nd` | *C*_m (section) |
| Section chord force coefficient | `cc_sec_nd` | *C*_c (section) |

### Aerodynamic coefficients — stability / body axis

| Quantity | Code variable | CSV symbol |
|---|---|---|
| Lift coefficient | `cl_nd` | *C*_L |
| Drag coefficient | `cd_nd` | *C*_D |
| Side force coefficient | `cy_nd` | *C*_Y |
| Rolling moment coefficient | `cl_roll_nd` | *C*_l |
| Yawing moment coefficient (body) | `cn_nd` | *C*_n (body axis) |

### Control surface deflections

Internal representation is radians; degrees are used only at the UI boundary.

| Quantity | Code variable | CSV symbol |
|---|---|---|
| Elevator deflection | `delta_e_rad` | *δ*_e |
| Aileron deflection | `delta_a_rad` | *δ*_a |
| Rudder deflection | `delta_r_rad` | *δ*_r |
| Flap deflection | `delta_f_rad` | *δ*_f |
| Spoiler deflection | `delta_sp_rad` | *δ*_sp |
| Trimmable stabiliser deflection | `delta_stab_rad` | *δ*_stab |

### Structural loads (at LRA / grid point)

All section loads are in the **structural frame** (x aft, y starboard, z up) and follow the
**Lomax §5** sign convention. See `doc/variable_definition.md` for derivations.

| Quantity | Code variable | Symbol | Positive direction |
|---|---|---|---|
| Vertical shear | `vz_n` | *V*_z | +z (upward); positive under lift loading |
| Chordwise shear | `vx_n` | *V*_x | +x (aft); positive under drag loading |
| Spanwise axial | `fy_n` | *F*_y | +y (outboard); tension positive |
| Out-of-plane bending | `mx_nm` | *M*_x | Upward bending; upper surface compression; Lomax positive |
| Torsion | `my_nm` | *M*_y | Leading edge UP (nose-up); Lomax positive torsion |
| In-plane bending | `mz_nm` | *M*_z | +x (aft) displacement; chordwise bending |

### Aircraft geometry and mass

| Quantity | Code variable | CSV symbol |
|---|---|---|
| Semi-span | `s_m` | *s* |
| Semi-chord (aeroelastics) | `b_m` | *b* |
| Wing reference area | `s_ref_m2` | *S*_ref |
| Mean aerodynamic chord | `mac_m` | *MAC* |
| Local chord | `c_m` | *c* |
| Spanwise station (normalised) | `eta_nd` | *η* = *y*/*s* |
| Spanwise coordinate | `y_m` | *y* |
| CG location (x, dimensional) | `x_cg_m` | *x*_CG |
| CG position (fraction MAC, dimensionless) | `x_cg_nd` | *h* |
| Aircraft gross weight | `w_aircraft_n` | *W* |
| Aircraft total mass | `m_ac_kg` | *m*_ac |

### Load factors and safety factors

| Quantity | Code variable | Notes |
|---|---|---|
| Normal load factor | `nz_nd` | dimensionless |
| Axial load factor | `nx_nd` | dimensionless |
| Side load factor | `ny_nd` | dimensionless |
| Maximum maneuver load factor | `nz_max_nd` | |
| Minimum maneuver load factor | `nz_min_nd` | |
| Factor of safety | `fos_nd` | per-condition input from condition list; see note below |
| Ultimate load factor | `nz_ult_nd` | = `nz_nd` × `fos_nd` |

`fos_nd` is a **per-condition** value supplied in the condition list CSV (column
`fos`). All outputs from WBT_LOADS are ultimate loads; `fos_nd` is the
multiplier applied to limit loads to produce them.

**Regulatory basis for `fos_nd` values:**

| `fos_nd` | Regulatory basis | Typical application |
|---|---|---|
| 1.5 | FAR/CS 25.303 — standard factor of safety on limit loads | All routine maneuver, gust, and ground conditions |
| 1.0 | FAR/CS 25.302 — system/structure interaction; load condition already defined as limit = ultimate | Certain failure cases where probability of occurrence makes limit treatment appropriate |
| Other | FAR/CS 25.302, advisory material | Intermediate values where failure probability falls between the bands above |

FAR 25.302 (CS 25.302 — Interaction of Systems and Structures) requires that
where a system failure affects structural performance, the required factor of
safety is a function of: (a) the probability of the failure occurring during a
single flight, and (b) whether structural failure is expected at the time of
the system event or only if flight is continued after it. The condition list
must carry the `fos` column so the analyst can encode these distinctions
per-condition. When `fos_nd = 1.0`, the condition is a limit load that
regulations treat as ultimate; no additional multiplication is applied.

Never substitute a bare literal for `fos_nd` inside `loads.py`. Never use a
module-level constant `FS = 1.5`; read `fos_nd` from the condition row.

### Gust and ground loads

| Quantity | Code variable | Notes |
|---|---|---|
| Design gust velocity | `u_gust_m_s` | EAS, m/s |
| Gust gradient distance | `h_gust_m` | gradient, m (not altitude) |
| Gust alleviation factor | `k_gust_nd` | dimensionless |
| Design sink rate | `v_sink_m_s` | m/s |
| Available gear stroke | `d_stroke_m` | m; from gear design data or condition input |
| Gear absorption efficiency | `eta_gear_nd` | dimensionless; typically 0.80 per FAR 25.473(b) |
| Peak gear reaction | `f_gear_n` | N; result of FAR 25.473 reserve energy formula |
| Effective load factor (landing) | `nz_eff_nd` | dimensionless; = `f_gear_n / w_aircraft_n` |
| Tail-down contact attitude | `alpha_td_rad` | rad; aircraft attitude when tail contacts runway |
| Ground speed | `v_ground_m_s` | m/s |
| Ground turn radius | `r_turn_m` | m |
| Gear normal load | `n_gear_n` | N at contact point |
| Brake torque | `t_brake_nm` | N·m |
| Brake friction coefficient | `mu_brake_nd` | dimensionless |
| Gust mass ratio | `mu_g_nd` | dimensionless; see `doc/analysis_dfl.md §b2` for formula |
| Vertical bump load factor | `nz_bump_nd` | dimensionless; taxi bump / rough runway |

### Continuous turbulence — 2-DOF model

| Quantity | Code variable | SI unit | Notes |
|---|---|---|---|
| Short-period natural frequency | `omega_sp_rad_s` | rad/s | from 2-DOF eigenvalue |
| Short-period damping ratio | `zeta_sp_nd` | — | dimensionless |
| PSD of gust velocity | `phi_u_m2_s` | m²·s/rad | Von Kármán spectrum at frequency ω |
| FRF of load response (generic) | `h_load_nd` | varies | complex ndarray over frequency grid |
| FRF of load factor | `h_nz_nd` | nd / (m/s) | complex; nz per unit gust velocity |
| FRF of wing root bending moment | `h_my_nm` | N·m / (m/s) | complex |
| RMS normal load factor | `sigma_nz_nd` | — | standard deviation |
| RMS wing root bending moment | `sigma_my_nm` | N·m | standard deviation |
| Turbulence intensity | `sigma_w_m_s` | m/s | from `APP_CONFIG`; default 1.0 m/s |
| Turbulence scale length | `l_turb_m` | m | 762 m (2 500 ft) per AC 25.341-1 |
| PSD limit load factor | `k_sigma_nd` | — | per AC 25.341-1; default 3.0 |
| Frequency integration variable | `omega_rad_s` | rad/s | frequency grid array |

### Condition list

Metadata and physical quantities specific to condition list parsing (`condition.py`).
Physical quantities (`h_m`, `v_eas_m_s`, `nz_nd`, `x_cg_nd`, `u_gust_m_s`,
`v_sink_m_s`, `p_roll_rad_s`, `nx_nd`, `ny_nd`, `m_ac_kg`) are defined in their
respective sections above; only the metadata columns are listed here.

| Quantity | Code variable | Notes |
|---|---|---|
| Condition identifier | `condition_id` | String; unique per CSV row |
| Condition description | `description` | String; human-readable label |
| Load category | `category` | String enum: `maneuver` \| `gust` \| `ground` |
| Case type | `maneuver_type` | String enum; see `decision.md §1b` for full list |
| Analysis type | *(CSV subdirectory)* | Determined by which `data/conditions/<type>/` subdirectory the CSV is in; not a column — see `decision.md §9` |
| Factor of safety | `fos_nd` | Float; per-condition multiplier applied to limit loads to produce ultimate loads. `1.5` for standard FAR 25.303 conditions; `1.0` where regulations define the condition as limit treated as ultimate (e.g. FAR/CS 25.302 failure cases). See §"Load factors and safety factors" for full regulatory basis. |

CSV columns carrying control surface deflections use `_deg` names
(`elevator_deg`, `aileron_deg`, `rudder_deg`, `flap_deg`, `spoiler_deg`,
`stabiliser_deg`). `condition.py` converts each to the corresponding `_rad`
variable (`delta_e_rad`, `delta_a_rad`, `delta_r_rad`, `delta_f_rad`,
`delta_sp_rad`, `delta_stab_rad`) via `DEG_RAD` before passing to any
computation module.

---

### Flap / high-lift pressure distribution (Category E)

Variables specific to the idealized Pn / Pc method in `doc/analysis_flaps.md`.

| Quantity | Code variable | SI unit | Notes |
|---|---|---|---|
| Normal pressure distribution | `pn_pa` | Pa | Chordwise pressure perpendicular to local flap chord; positive into upper surface |
| Chord pressure distribution | `pc_pa` | Pa | Chordwise pressure parallel to local flap chord; positive aft |
| Normal load per unit span | `fn_n_m` | N/m | Integral of `pn_pa` over flap chord at one strip station |
| Chord load per unit span | `fc_n_m` | N/m | Integral of `pc_pa` over flap chord at one strip station |
| Local flap chord | `c_flap_m` | m | Chord of flap element at strip station (hinge line to trailing edge) |
| Chordwise fraction (flap-local) | `x_f_nd` | — | 0 at hinge line, 1 at trailing edge |
| Reference WBT condition | `ref_condition_id` | — | String; `condition_id` of the parent Category A or B case whose section loads define `fn_n_m` and `fc_n_m` |

---

### Structural stiffness (elastic model)

Project-specific quantities not in the CSV, following the same naming convention:

| Quantity | Code variable | Notes |
|---|---|---|
| Bending stiffness | `ei_nm2` | N·m² |
| Torsional stiffness | `gj_nm2` | N·m² |
| Axial stiffness | `ea_n` | N |
| Flexibility matrix | `f_flex` | Interleaved transverse/rotation DOFs; entries m/N (disp/force), rad/(N·m) (rot/moment), m/(N·m) or rad/N (cross terms). See `doc/variable_definition.md §Flexibility matrix specification`. |
| Aeroelastic effectiveness (control) | `e_flex_nd` | dimensionless, ≤ 1.0 |

---

## Module-level constants

Physical constants use `ALL_CAPS` with a SI unit suffix.  These are constant
definitions, not variable references, so they do not follow the lowercase CSV
convention:

```python
G_M_S2        = 9.80665      # gravitational acceleration, m/s²
RHO_0_KG_M3   = 1.2250       # sea-level air density, kg/m³  (US Standard Atmosphere 1976)
P_0_PA        = 101325.0     # sea-level static pressure, Pa (US Standard Atmosphere 1976)
T_0_K         = 288.15       # sea-level temperature, K       (US Standard Atmosphere 1976)
GAMMA         = 1.4          # ratio of specific heats (dimensionless — no suffix)
```

Atmospheric model: US Standard Atmosphere 1976 (Decision 19). See also the ATMOS
project reference in `doc/variable_definition.md §Module-level constants`.

Tunable solver parameters (tolerances, iteration limits) belong in
`config/defaults.json`, not as module-level constants.

---

## Conversion constants (`unit_convert.py`)

Pattern `<FROM>_<TO>` in `ALL_CAPS`, where `<FROM>` and `<TO>` are unit
abbreviations. Provide both directions for every pair:

```python
DEG_RAD    = 0.017453293     # degrees → radians
RAD_DEG    = 57.295779513    # radians → degrees

FT_M       = 0.3048          # feet → metres
M_FT       = 1 / FT_M

IN_M       = 0.0254          # inches → metres
M_IN       = 1 / IN_M

FPS_M_S    = FT_M            # ft/s → m/s  (same factor as FT_M)
M_S_FPS    = M_FT

KTS_M_S    = 0.514444        # knots → m/s
M_S_KTS    = 1 / KTS_M_S

LBF_N      = 4.44822         # pounds-force → Newtons
N_LBF      = 1 / LBF_N

SLUG_KG    = 14.59390        # slugs → kilograms
KG_SLUG    = 1 / SLUG_KG

PSF_PA     = 47.88026        # lb/ft² → Pascals
PA_PSF     = 1 / PSF_PA

FTLBF_NM   = 1.355818        # ft·lbf → Newton-metres
NM_FTLBF   = 1 / FTLBF_NM
```

Never embed conversion factors as bare literals inside analysis functions.
Import from `unit_convert` and use the named constant.

---

## Intermediate / helper variables

Short-lived algebraic intermediates that correspond to no single aeronautical
symbol use a descriptive name that still carries SI units where applicable.
Prefer two or three components separated by `_`:

```python
# good — descriptive, SI unit suffix
lift_increment_n  = ...
moment_arm_m      = ...

# bad — cryptic single letters that are not established symbols
a = ...
b = ...
```

If an intermediate is a sub-expression of a larger formula with no independent
physical meaning, a short name is acceptable only inside a tightly scoped helper
function (fewer than ~15 lines).

---

## Function signatures

Apply the same symbol-and-SI-unit convention to parameter names.  Use the
`code_variable_name` from the CSV wherever applicable:

```python
# correct — CSV code_variable_names, SI units, radians internally
def interpolate_strip(alpha_rad: float, beta_rad: float,
                      p_roll_rad_s: float, q_pitch_rad_s: float,
                      r_yaw_rad_s: float, delta_e_rad: float) -> np.ndarray: ...

def solve_trim(h_m: float, v_eas_m_s: float,
               nz_nd: float, x_cg_m: float) -> dict: ...

# incorrect — imperial units, degrees for control deflection, no unit suffix
def solve_trim(h_press_ft, V_EAS_kts, n_z, x_cg_ft): ...
```

---

## Analysis methods

Six analysis method categories map to the six TUI analysis types from
`decision.md §9`. The same aerodynamic database, mass model, and LRA
infrastructure support all categories.

| TUI Category | TUI label | Specification document | Phase |
|---|---|---|---|
| A — Static Flight Loads | SFL | [`doc/analysis_sfl.md`](analysis_sfl.md) | 1 |
| B — Dynamic Flight Loads | DFL | [`doc/analysis_dfl.md`](analysis_dfl.md) | 1 (simplified); 2 (DLM, 1-cosine TDG) |
| C — Static Ground Loads | SGL | [`doc/analysis_sgl.md`](analysis_sgl.md) | 1 |
| D — Dynamic Ground Loads | DGL | [`doc/analysis_dgl.md`](analysis_dgl.md) | 1 (quasi-static); 2 (dynamic gear) |
| E — Flap / High-Lift Loads | FLAPS | [`doc/analysis_flaps.md`](analysis_flaps.md) | 2 (deferred) |
| F — Control Surface Loads | CONTROLS | [`doc/analysis_controls.md`](analysis_controls.md) | 2 (deferred) |

Each linked document covers: regulatory basis, analysis sequence, primary
variables, modules used, condition list columns, and any Phase 2 deferred
sub-sections. All equations use SI quantities throughout. The naming conventions,
unit rules, symbol tables, and module implementation notes on this page apply
uniformly to all categories.

---

## Module implementation notes

The sections below describe each computation module's role, allowed imports,
and internal behavior. These are the implementation counterpart to the analysis
method descriptions above.

### `atmos.py` — US Standard Atmosphere 1976 (Decision 30)

Implements altitude-dependent atmospheric properties for the subsonic flight
envelope (sea level to ~15 545 m / ~51 000 ft). All equations follow US
Standard Atmosphere 1976 (troposphere: lapse rate 6.5 K/km; lower stratosphere:
isothermal at 216.65 K above 11 000 m).

Public functions (SI inputs and outputs throughout):

| Function | Returns | Notes |
|---|---|---|
| `temperature(h_m)` | `t_k` | K; troposphere and stratosphere branches |
| `pressure(h_m)` | `p_static_pa` | Pa |
| `density(h_m)` | `rho_kg_m3` | kg/m³; used by `trim.py`, `gust.py` |
| `speed_of_sound(h_m)` | `a_m_s` | m/s; used for Mach in `trim.py` |
| `eas_to_tas(v_eas_m_s, h_m)` | `v_tas_m_s` | m/s; σ = ρ/ρ₀ |
| `dynamic_pressure(v_tas_m_s, h_m)` | `q_dyn_pa` | Pa; `0.5 × ρ × V_TAS²` |

Module-level constants (literals, no imports):
```python
T_0_K       = 288.15     # sea-level temperature, K
P_0_PA      = 101325.0   # sea-level pressure, Pa
RHO_0_KG_M3 = 1.225      # sea-level density, kg/m³
L_K_M       = 0.0065     # tropospheric lapse rate, K/m
G_M_S2      = 9.80665    # standard gravity, m/s²
R_J_KGK     = 287.058    # specific gas constant, J/(kg·K)
GAMMA       = 1.4        # ratio of specific heats
```

**Allowed to import:** `math`, `numpy` — nothing else. No WBT_LOADS imports.

**Independence guarantee:** `atmos.py` is safe to import and use in any Python
environment that has `numpy`, without installing or importing any other
WBT_LOADS module. Users may call it from standalone tools or scripts.

---

### `aero_db.py` — Aerodynamic database interpolation

Loads strip load tables (`cn_sec_nd`, `cm_sec_nd`, `cc_sec_nd`) and incremental
tables (control surface deflections, angular rates) from CSV files. Interpolates
to produce spanwise arrays for a given flight state. Used by static flight loads
(analysis_sfl.md), dynamic flight loads (analysis_dfl.md), and indirectly by ground loads when aerodynamic
loads are present (e.g. landing roll at V > 0).

**File format, column schema, interpolation method, and Mach extrapolation
policy are specified in `doc/loads_aero_db.md`.**

Key behaviours:
- All geometry in input files is SI (metres); no conversion required.
- 4-D interpolation over `(y_m, alpha_deg, beta_deg, mach_nd)` using
  `scipy.interpolate.RegularGridInterpolator`.
- If flight Mach falls outside the table range, Prandtl-Glauert extrapolation
  is applied and a TUI warning is emitted. See `doc/loads_aero_db.md §Mach
  extrapolation fallback`.
- Increment tables are summed onto the baseline at interpolation time.

**Outputs:** 1-D arrays over spanwise grid stations for `cn_sec_nd`,
`cm_sec_nd`, `cc_sec_nd`.

---

### `mass_model.py` — NASTRAN CONM2 parsing

Parses CONM2 bulk data cards from a NASTRAN input file. Accepts only CID=0
(basic / global coordinate system). Ignores off-diagonal inertia terms for the
distributed mass model (point mass only). Used by all four analysis methods.

**Unit conversion at ingestion:** NASTRAN CONM2 files are assumed to use
feet/slugs (the common aerospace convention). Positions are converted to metres
(`× FT_M`) and masses to kilograms (`× SLUG_KG`) when the file is parsed.
If a project uses metric CONM2 files, declare `"conm2_units": "SI"` in
`config/defaults.json` and the conversion is skipped.

**Output:** structured array or DataFrame of point masses with:
- Node ID
- Position vector `[x_m, y_m, z_m]`
- Mass `m_ac_kg` (per-node contribution; total aircraft mass is the sum)

---

### `lra.py` — Loads reference axis and grid

Defines the Loads Reference Axis (LRA) as a series of oriented reference points
along the span. Provides the spanwise reporting grid (`eta_nd` stations). Used by
all four analysis methods as the common reference for section-load output.

**Key functions:**

| Function | Purpose |
|---|---|
| `load_lra(filepath)` | Parse and validate one `lra_<surface>.json`; raises `ValueError` on any violation |
| `build_lra(filepaths)` | Load all surface LRA files; returns `{surface_tag: stations_list}` |
| `resolve_position(pos_m, stations)` | Return index of LRA station nearest to 3-D position `pos_m`; projects onto piecewise-linear spine — handles kinked (winglet) LRAs |
| `sum_to_lra(strip_forces_m, strip_positions_m, stations)` | Integrate strip loads to LRA section cuts using full 3-D moment arm; returns `(N, 6)` array `[vz_n, vx_n, fy_n, mx_nm, my_nm, mz_nm]` |

---

### `trim.py` — Trim solver

Used by: static flight loads (analysis_sfl.md) and as the initial state for dynamic flight
loads (analysis_dfl.md).

Solves the three-equation trim balance (lift = weight × `nz_nd`, pitch moment = 0,
thrust = drag) using `scipy.optimize.root` with tolerance `APP_CONFIG["trim_tol"]`.

**Solve variables:** `alpha_rad`, `delta_e_rad`, `t_thrust_n`

**Inputs:** `h_m`, `v_eas_m_s`, `nz_nd`, `x_cg_m`, aircraft geometry.

**Outputs:** dict of solved flight state variables plus residuals for convergence
checking. The trim result dict is passed as an argument to `loads.compute_loads`.

---

### `maneuver.py` — Maneuver time history

Used by: dynamic flight loads (analysis_dfl.md §b1).

Integrates the equations of motion over a prescribed maneuver profile using
`scipy.integrate.solve_ivp`. Supported types: symmetric pull-up, push-over,
checked maneuver, rolling pull-out, yaw maneuver.

**Output:** time array `t_s[k]` and section load arrays `vz_n[i,k]`,
`mx_nm[i,k]`, etc., at each LRA station `i` and time step `k`. Critical
instant per load component extracted by `argmax`/`argmin` over the time axis.

---

### `ground.py` — Ground loads

Used by: static ground loads (analysis_sgl.md) and dynamic ground and landing loads (analysis_dgl.md).
No aerodynamic contribution; no time integration. All Phase 1 methods are
quasi-static.

**Allowed to import:** `mass_model`, `lra`, `numpy`, `unit_convert`, `config`

**Key functions:**

| Function | Category | Supported `maneuver_type` values |
|---|---|---|
| `compute_static_ground_loads` | C (SGL) | `braked_roll`, `ground_turn`, `nose_wheel_yaw`, `towing`, `pivoting`, `jacking` |
| `compute_landing_loads` | D.1 (DGL) | `level_landing`, `tail_down_landing`, `one_gear_landing`, `lateral_drift`, `rebound_landing` |
| `compute_taxi_braking_loads` | D.2 (DGL) | `taxi_bump`, `rough_runway`, `abrupt_braking` |

**Return value** (all three functions): a state dict with keys:
- `applied_forces_n` — ndarray (n_attach, 3), applied force vectors in structural frame
- `attach_positions_m` — ndarray (n_attach, 3), attachment point positions
- `nz_nd`, `nx_nd`, `ny_nd` — effective load factors at CG
- `condition_id` — string, passed through from `condition_row`

The caller (`menu.py`) passes this dict to `loads.compute_ground_loads()`.

**Private helper:**

`_apply_ground_inertia(m_ac_kg, nx_nd, ny_nd, nz_nd, mass_df)` — returns
`(forces_n, positions_m)` inertia force arrays for all CONM2 mass points.

**FAR 25.473 peak gear reaction (used in `compute_landing_loads`):**

```python
f_gear_n = w_aircraft_n * eta_gear_nd * (1 + v_sink_m_s**2 / (2 * G_M_S2 * d_stroke_m))
nz_eff_nd = f_gear_n / w_aircraft_n
```

All quantities are SI; `G_M_S2 = 9.80665` is the module-level physics constant.
If `v_sink_m_s` arrives in fps (from a legacy input file), convert at ingestion
using `FPS_M_S` from `unit_convert.py` before this formula.

---

### `gust.py` — Gust loads

Used by: dynamic flight loads (analysis_dfl.md). Implements two Phase 1 gust paths.

**Static equivalent discrete gust (analysis_dfl.md §b2):** takes `u_gust_m_s`, `v_eas_m_s`,
`rho_kg_m3`, `mac_m`, `s_ref_m2`, `m_ac_kg`, and `a_slope_nd` from the trim
state. Returns `delta_nz_nd` as an increment on the trim load factor passed
to `loads.py`. Routing: `maneuver_type` in
`{discrete_gust_vertical, discrete_gust_lateral}`.

**2-DOF continuous turbulence (analysis_dfl.md §b3):** assembles the plunge-pitch system from
aircraft mass properties and strip-theory derivatives, computes complex FRFs
`h_nz_nd` and `h_my_nm` over the frequency grid, integrates the Von Kármán
PSD, and returns RMS loads `sigma_nz_nd` and `sigma_my_nm` and design limit
loads (`k_sigma_nd × σ`). Routing: `maneuver_type == continuous_turbulence`.

Phase 2 paths (1-cosine TDG, DLM PSD FRFs) are placeholders; the
`h_gust_m` and `n_gust_steps` condition columns are parsed but not used.

**Allowed to import:** `aero_db`, `mass_model`, `lra`, `numpy`, `scipy`,
`unit_convert`, `config`

**Must not import:** `trim`, `maneuver`, `ground`, `loads`, `aeroelastic`, `beam`

---

### `loads.py` — Loads summation

The final summation step for all four analysis methods. Receives the flight or
ground state as arguments (not by importing `trim` or `maneuver` directly).

**Trim state passing (Decision 12):** `loads.py` does not import `trim.py`.
`menu.py` (or `aero_trim.py` for aeroelastic cases) calls `trim.solve_trim(...)`
and passes the resulting trim state dict directly to `loads.compute_loads(trim_state, ...)`.
No upward import dependency is introduced.

**Aerodynamic contribution (flight loads):** integrates `cn_sec_nd`, `cm_sec_nd`,
`cc_sec_nd` arrays multiplied by `q_dyn_pa` and local chord over each strip panel
using the **trapezoidal rule** (Decision 18):
```
dF = 0.5 × (f[i] + f[i+1]) × (y[i+1] − y[i])
```
Summed to LRA section cuts via `lra.sum_to_lra` using the full 3-D moment arm.

**Inertia contribution (all methods):** for each point mass, computes
`f_inertia_n = m_ac_kg × G_M_S2 × nz_nd` (or `nx_nd`, `ny_nd` for ground
cases) and the moment arm to the LRA, then sums to section cuts.

**Applied load contribution (ground handling/landing):** external forces
(`f_gear_n`, tow force, `t_brake_nm`) are added at their attachment points and
summed to LRA section cuts identically to inertia loads.

Applies the per-condition `fos_nd` (passed in the condition state dict, read from
the condition list CSV `fos` column) to limit loads to produce ultimate loads.
Standard value is 1.5 per FAR 25.303; values as low as 1.0 are valid for
conditions defined as limit-treated-as-ultimate under FAR/CS 25.302.

**Output:** `vz_n[i]`, `vx_n[i]`, `fy_n[i]`, `mx_nm[i]`, `my_nm[i]`,
`mz_nm[i]` at each LRA station `i`. All output loads are **ultimate**
(limit × `fos_nd`). The applied `fos_nd` is carried through the output dict
alongside the load arrays so the multiplier is traceable in reports and NASTRAN
cards.

---

### `nastran_out.py` — NASTRAN FORCE/MOMENT card writer

Formats the per-condition section load arrays from `loads.py` as NASTRAN bulk
data cards and writes `<data_root>/outputs/<aircraft_id>_<load_cycle_id>_<load_case_id>.dat`
(one file per load case, all surfaces). Also writes
`<aircraft_id>_<load_cycle_id>_<component>_VMT.csv` and
`analysis_summary_<date>.out`. See `doc/architecture.md §CRITIC_LOADS interface`
for the full naming convention. No computation; pure formatting.

**FORCE card format (free-field):**
`FORCE, SID, GID, 0, 1.0, vx_n, fy_n, vz_n`

**MOMENT card format (free-field):**
`MOMENT, SID, GID, 0, 1.0, mx_nm, my_nm, mz_nm`

Where:
- `SID` — load set ID = condition sequence number (1-based integer)
- `GID` — grid ID = LRA station index (1-based; matches station order in JSON)
- Components are in the structural frame (x aft, y starboard, z up) in SI units
  (N for forces, N·m for moments); no unit conversion in this module
- Ultimate load cards are written in a separate block with `SID += 10000 × n_cond`

**Key variable:**

| Quantity | Code variable | Notes |
|---|---|---|
| NASTRAN load set ID | `sid_nd` | dimensionless integer; equals condition sequence number |
| NASTRAN grid point ID | `gid_nd` | dimensionless integer; equals 1-based LRA station index |

---

### `aeroelastic.py` — Aeroelastic corrections and jig shape

Used by: static flight loads (analysis_sfl.md) only. Not applied to ground loads.

Applies structural flexibility corrections via the flexibility matrix `f_flex`.
Iterates between aerodynamic load and elastic deflection until convergence
within `APP_CONFIG["flex_tol"]`.

**Aeroelastic effectiveness:** `e_flex_nd = η_flexible / η_rigid` per control
surface. When `e_flex_nd < 0` for any surface at any condition, `aeroelastic.py`
raises `ValueError("Control reversal: <surface> at condition <ID> "
"(e_flex_nd = <value>)")`. The calling `menu.py` handler catches this, prints
`[red]Error: <message>[/red]`, and returns to the menu without writing output.
Control reversal is treated as a hard error (Decision 17, Option C).

**Jig shape:** backs out the unloaded geometry from the cruise trim condition
by inverting the aero-structural coupling. The jig shape is the manufactured
geometry that deforms to the design cruise shape under cruise loads.

**Inputs:** `f_flex` (flexibility matrix, units m/N or m/(N·m) depending on
load type), cruise trim state dict, baseline rigid section loads from `loads.py`.

**Outputs:** flexibility-corrected section load arrays, `e_flex_nd` per surface,
jig shape station offsets in metres.

---

### `aero_trim.py` — Coupled aeroelastic trim (Decision 13)

Used by: static flight loads (analysis_sfl.md) when elastic corrections are active.
`menu.py` calls `aero_trim.solve(...)` instead of calling `trim` and
`aeroelastic` directly.

**Convergence loop (internal):**
1. `trim.solve_trim(h_m, v_eas_m_s, nz_nd, x_cg_m, ...)` → rigid trim state
2. `aeroelastic.apply_corrections(rigid_state, f_flex, ...)` → deflected shape + corrected loads
3. Repeat until section load change between iterations < `APP_CONFIG["flex_tol"]`
   (max iterations: `APP_CONFIG["flex_max_iter"]`)

**Purpose:** neither `trim.py` nor `aeroelastic.py` imports the other; the
coupling loop lives here so both modules remain independent.

**Allowed to import:** `trim`, `aeroelastic`, `aero_db`, `lra`, `numpy`,
`scipy`, `unit_convert`, `config`

**Must not contain:** display logic, ground load logic.

---

## FAR 23 regulatory formulas (deferred — reference specification)

FAR 23 is not implemented in the initial release (Decision 6, Option C). When
implemented, all FAR 23-specific regulatory formulas will reside in
`src/far_reg.py` in the support layer.

### Maneuver load factors — FAR 23.337

The limit maneuver load factor depends on aircraft gross weight converted to lbs
(use `LB_N` from `unit_convert.py`) and category:

| Category | n_max | Constraint | n_min |
|---|---|---|---|
| Normal | 2.1 + 24 000 / (w_lb + 10 000) | min 2.5, max 3.8 | −0.4 × n_max |
| Utility | 4.4 | — | −0.4 × n_max |
| Acrobatic | 6.0 | — | −0.5 × n_max |

The category must be a field in the condition list (or aircraft config) when FAR
23 is activated.

### Gust velocities — FAR 23.341

FAR 23.341 uses the same discrete gust method as FAR 25.341(a) with identical
design gust velocities to the pre-Amendment 25-86 FAR 25 table:

| Altitude | Imperial | SI |
|---|---|---|
| Sea level (0 m) | 50 fps EAS | 15.24 m/s EAS |
| 20 000 ft (6 096 m) | 25 fps EAS | 7.62 m/s EAS |

The gust alleviation factor formula is identical to FAR 25. FAR 23 does **not**
require continuous turbulence PSD analysis; `maneuver_type ==
"continuous_turbulence"` is invalid when `cert_basis == "FAR23"`.

### `src/far_reg.py` function signatures (to be implemented)

```python
def nz_maneuver_far23(m_ac_kg: float, category: str) -> tuple[float, float]:
    """Return (nz_max_nd, nz_min_nd) per FAR 23.337.
    category: 'normal' | 'utility' | 'acrobatic'
    """


def u_gust_far23_m_s(h_m: float) -> float:
    """Return FAR 23.341 design gust velocity (EAS) in m/s at altitude h_m.
    Policy above 6 096 m governed by APP_CONFIG['gust_velocity_above_20kft'].
    """
```
