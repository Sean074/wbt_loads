# Analysis Code Standards — Variable Naming and Methods

Applies to all computation modules: `aero_db.py`, `mass_model.py`, `lra.py`,
`trim.py`, `maneuver.py`, `gust.py`, `ground.py`, `loads.py`, `aeroelastic.py`,
`beam.py`, and any helper functions called from them. UI and menu code is excluded.

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
| Factor of safety (always 1.5) | module constant `FS = 1.5` | |
| Ultimate load factor | `nz_ult_nd` | = `nz_nd` × 1.5 |

`FS = 1.5` is a module-level constant in `loads.py`. Never substitute a
bare literal `1.5` where the factor of safety is applied.

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
| Gust mass ratio | `mu_g_nd` | dimensionless; see §b2 formula |
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

CSV columns carrying control surface deflections use `_deg` names
(`elevator_deg`, `aileron_deg`, `rudder_deg`, `flap_deg`, `spoiler_deg`,
`stabiliser_deg`). `condition.py` converts each to the corresponding `_rad`
variable (`delta_e_rad`, `delta_a_rad`, `delta_r_rad`, `delta_f_rad`,
`delta_sp_rad`, `delta_stab_rad`) via `DEG_RAD` before passing to any
computation module.

---

### Structural stiffness (elastic model)

Project-specific quantities not in the CSV, following the same naming convention:

| Quantity | Code variable | Notes |
|---|---|---|
| Bending stiffness | `ei_nm2` | N·m² |
| Torsional stiffness | `gj_nm2` | N·m² |
| Axial stiffness | `ea_n` | N |
| Flexibility matrix | `f_flex` | m/N or m/(N·m) depending on load type |
| Aeroelastic effectiveness (control) | `e_flex_nd` | dimensionless, ≤ 1.0 |

---

## Module-level constants

Physical constants use `ALL_CAPS` with a SI unit suffix.  These are constant
definitions, not variable references, so they do not follow the lowercase CSV
convention:

```python
G_M_S2        = 9.80665      # gravitational acceleration, m/s²
RHO_0_KG_M3   = 1.2250       # sea-level air density, kg/m³
P_0_PA        = 101325.0     # sea-level static pressure, Pa
GAMMA         = 1.4          # ratio of specific heats (dimensionless — no suffix)
```

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
infrastructure support all categories. Each is described below.

| TUI Category | TUI label | Sub-categories | Analysis method section | Phase |
|---|---|---|---|---|
| A — Static Flight Loads | SFL | A.1 Longitudinal – Balanced, A.2 Longitudinal – Maneuver, A.3 Lateral – Balanced, A.4 Lateral – Maneuver | §a | 1 |
| B — Dynamic Flight Loads | DFL | B.1 PSD (continuous turbulence), B.2 TDG (discrete gust) | §b | 1 (both Phase 1 simplified); 2 (DLM, 1-cosine TDG) |
| C — Static Ground Loads | SGL | — | §c | 1 |
| D — Dynamic Ground Loads | DGL | D.1 Landing, D.2 Taxi/Braking | §d | 1 (quasi-static); 2 (dynamic gear) |
| E — Flap / High-Lift Loads | FLAPS | — | §e | 1 |
| F — Control Surface Loads | CONTROLS | — | §f | 2 (deferred) |

All equations use SI quantities throughout.

---

### a) Static flight loads

**Regulatory basis:**

| Load case | FAR 25 / CS-25 | FAR 23 / CS-23 |
|---|---|---|
| General structural loads — limit and ultimate definition | 25.301 | 23.301 |
| Factor of safety (1.5 on limit loads) | 25.303 | 23.303 |
| Flight maneuvering envelope (V-n diagram) | 25.333 | 23.333 |
| Design airspeeds (V_A, V_B, V_C, V_D) | 25.335 | 23.335 |
| Limit maneuver load factors | 25.337 | 23.337 |
| Symmetric pull-up and push-over | 25.331 | 23.331 |
| Unsymmetrical loads (100%/80% HT loading) | 25.347 | 23.347 |
| Rolling pull-out | 25.349 | 23.349 |
| Yaw maneuver conditions | 25.351 | 23.351 |
| High lift devices (flap/slat extended) | 25.345 | 23.345 |
| Engine failure / asymmetric thrust | 25.367 | 23.367 |
| Control surface and tab loads | 25.391–25.427 | 23.391–23.427 |

> **FAR 23 / CS-23 column — reference only.** FAR 23 is not implemented in the
> current release (Decision 6, Option C). All computation uses FAR 25 / CS-25
> formulas. When FAR 23 is implemented, formula dispatch will occur via
> `src/far_reg.py` and a `cert_basis` field in the condition list; see
> `doc/architecture.md §FAR 23 provision`.

CS-25 and CS-23 section numbers are identical to their FAR counterparts.

**Method:** Quasi-static equilibrium. The aircraft is in a balanced, non-accelerating
flight state (or a steady-state maneuver) defined by a fixed load factor `nz_nd`.
No time integration is performed.

**Sequence:**

1. **Trim solve** (`trim.py`) — find α, δ_e, and thrust such that the three
   equilibrium equations are satisfied simultaneously:

   ```
   L = nz_nd × w_aircraft_n           (lift equals weight × load factor)
   ΣM_pitch = 0                        (pitching moment balance at CG)
   T = D                               (thrust equals drag)
   ```

   Solved by `scipy.optimize.root` with tolerance `APP_CONFIG["trim_tol"]`.
   Solve variables: `alpha_rad`, `delta_e_rad`, `t_thrust_n`.

2. **Aerodynamic interpolation** (`aero_db.py`) — evaluate strip load arrays at
   the trimmed flight state:

   ```
   cn_sec_nd(y), cm_sec_nd(y), cc_sec_nd(y) =
       interpolate(alpha_rad, beta_rad, p_roll_rad_s,
                   q_pitch_rad_s, r_yaw_rad_s, delta_e_rad, ...)
   ```

   Add control surface and rate increments. If flight Mach falls outside the
   aero database table range, `aero_db.py` applies Prandtl-Glauert extrapolation
   and emits a TUI warning. See `doc/loads_aero_db.md §Mach extrapolation
   fallback` for the formula and warning text.

   Apply downwash correction at the horizontal tail.

3. **Loads summation** (`loads.py`) — integrate strip loads to LRA section cuts.

   Aerodynamic contribution per strip panel of width `dy_m`:

   ```
   dvz = cn_sec_nd × q_dyn_pa × c_m × dy_m
   dmx = dvz × (y_lra_m - y_strip_m)       (bending moment arm)
   dmy = cm_sec_nd × q_dyn_pa × c_m² × dy_m  (torsion from Cm about c/4)
   ```

   Inertia contribution per point mass:

   ```
   f_inertia_n = m_ac_kg × G_M_S2 × nz_nd
   ```

   Moment arm from mass point to LRA determines inertia bending and torsion
   contributions. Aerodynamic and inertia contributions are summed at each LRA
   station to give net section loads: `vz_n`, `vx_n`, `fy_n`, `mx_nm`, `my_nm`,
   `mz_nm`.

4. **Aeroelastic corrections** (`aeroelastic.py`) — when the elastic model is
   present, apply structural flexibility correction:

   ```
   {δ} = [f_flex] × {P}     (deflection from flexibility matrix × load vector)
   ```

   Re-evaluate strip loads at the deflected geometry. Iterate between steps 2–4
   until the change in section loads between iterations is below
   `APP_CONFIG["flex_tol"]`.

5. **Limit and ultimate loads** (`loads.py`) — multiply limit loads by `FS = 1.5`
   to obtain ultimate loads per FAR 25.303.

**Primary variables:** `nz_nd`, `alpha_rad`, `q_dyn_pa`, `mach_nd`,
`delta_e_rad`, `cn_sec_nd`, `cm_sec_nd`, `cc_sec_nd`, `vz_n`, `mx_nm`,
`my_nm`, `nz_ult_nd`, `e_flex_nd`

**Modules:** `trim.py` → `aero_db.py` → `loads.py` → `aeroelastic.py`

---

### b) Dynamic flight loads

**Regulatory basis:**

| Load case | FAR 25 / CS-25 | FAR 23 / CS-23 |
|---|---|---|
| Checked maneuver (pitch rate reversal) | 25.331(c) | 23.331 |
| Rolling pull-out | 25.349 | 23.349 |
| Yaw maneuver | 25.351 | 23.351 |
| Discrete vertical and lateral gust (1-cosine) | 25.341(a) | 23.341 |
| Continuous turbulence — power spectral density | 25.341(b) | — |
| Dynamic gust loads implementation guidance | AC 25.341-1 / AMC 25.341-1 | — |

> **FAR 23 / CS-23 column — reference only.** FAR 23 is not implemented in the
> current release (Decision 6, Option C). All computation uses FAR 25 / CS-25
> formulas. When FAR 23 is implemented, formula dispatch will occur via
> `src/far_reg.py` and a `cert_basis` field in the condition list; see
> `doc/architecture.md §FAR 23 provision`.

FAR 23 does not require continuous turbulence PSD analysis; the discrete gust
method per 23.341 is sufficient for FAR 23 certification.

Two separate dynamic load paths exist: maneuver time history and gust response.
Both produce a time-varying load array from which the critical instant is extracted.

#### b1) Maneuver time history

**Method:** Integrate the rigid-body equations of motion over a prescribed
maneuver profile using `scipy.integrate.solve_ivp`.

State vector: `[alpha_rad, q_pitch_rad_s, p_roll_rad_s, r_yaw_rad_s, phi_rad]`

At each time step:
1. Interpolate strip loads at the current flight state → `cn_sec_nd(y,t)`, `cm_sec_nd(y,t)`, `cc_sec_nd(y,t)`
2. Compute section loads via `loads.py` summation
3. Store section load arrays at this time step

Supported maneuver types and their governing DOF:

| Maneuver | Active DOF | FAR 25 / CS-25 | FAR 23 / CS-23 |
|---|---|---|---|
| Symmetric pull-up | α, q | 25.331(b) | 23.331 |
| Push-over | α, q | 25.331(b) | 23.331 |
| Checked maneuver | α, q (with pitch rate reversal) | 25.331(c) | 23.331 |
| Rolling pull-out | α, q, p, φ | 25.349 | 23.349 |
| Yaw maneuver | β, r (with prescribed δ_r input) | 25.351 | 23.351 |

> **FAR 23 / CS-23 column — reference only.** FAR 23 is not implemented in the
> current release (Decision 6, Option C). All computation uses FAR 25 / CS-25
> formulas. When FAR 23 is implemented, formula dispatch will occur via
> `src/far_reg.py` and a `cert_basis` field in the condition list; see
> `doc/architecture.md §FAR 23 provision`.

**Critical instant extraction:** scan the complete time history for the maximum
positive and maximum negative value of each load component at each LRA station.
The time-point that produces each extremum is the critical instant for that
component.

**Primary variables:** `t_s`, `alpha_rad`, `q_pitch_rad_s`, `p_roll_rad_s`,
`r_yaw_rad_s`, `phi_rad`, `beta_rad`, `delta_r_rad`, `vz_n`, `mx_nm`

**Modules:** `maneuver.py` → `aero_db.py` → `loads.py`

#### b2) Discrete gust — static equivalent method (Phase 1)

**Regulatory basis:** original FAR Part 25 Appendix G, pre-Amendment 25-86
(1996), as described in Lomax, *Structural Loads Analysis for Commercial
Transport Aircraft*, AIAA 1996, Chapter 4.

**Phase 1 method — no 1-cosine profile; no H sweep.**

Design gust velocities (pre-1996 FAR Part 25 Appendix G, converted to SI at
ingestion in `gust.py`):

| Altitude | Imperial | SI |
|---|---|---|
| Sea level (0 m) | 50 fps EAS | 15.24 m/s EAS |
| 20 000 ft (6 096 m) | 25 fps EAS | 7.62 m/s EAS |

Interpolation: linear between 0 m and 6 096 m. Above 6 096 m: controlled by
`APP_CONFIG["gust_velocity_above_20kft"]` — `"extrapolate"` (default) or `"cap"`.

Gust alleviation factor (identical formula to the current regulation):

```
k_gust_nd = 0.88 × mu_g_nd / (5.3 + mu_g_nd)

mu_g_nd = 2 × m_ac_kg / (rho_kg_m3 × mac_m × s_ref_m2 × a_slope_nd)
```

Incremental load factor (all quantities in SI):

```
delta_nz_nd = (k_gust_nd × u_gust_m_s × v_eas_m_s × a_slope_nd)
              / (2 × (w_aircraft_n / s_ref_m2))
```

where `w_aircraft_n = m_ac_kg × G_M_S2`. Both positive and negative increments
are evaluated: `nz_nd = 1.0 ± delta_nz_nd`. `a_slope_nd` is the whole-aircraft
lift curve slope (per radian) from the trim aerodynamic state.

`h_gust_m`, `gust_gradient_min_ft`, `gust_gradient_max_ft`, and `n_gust_steps`
are **not used** in Phase 1; they are reserved for the Phase 2 TDG.

**Primary variables:** `u_gust_m_s`, `k_gust_nd`, `mu_g_nd`, `a_slope_nd`,
`delta_nz_nd`, `rho_kg_m3`, `mac_m`, `s_ref_m2`, `m_ac_kg`, `w_aircraft_n`,
`v_eas_m_s`

**Modules:** `gust.py` (see decision.md §11) → `aero_db.py` → `loads.py`

##### b2-Phase2) Discrete gust — 1-cosine TDG (Phase 2 / deferred)

**Regulatory basis:** FAR 25.341(a); AC 25.341-1 (Amendment 25-86 and later).

Gust velocity profile:
`u_gust_inst_m_s(s) = (u_gust_m_s / 2) × (1 − cos(π × s / h_gust_m))`
for `0 ≤ s ≤ 2 × h_gust_m`. Design gust velocities from current FAR 25.341(a)
table: 17.07 m/s EAS at sea level, 6.36 m/s at 18 288 m. H sweep from 9 to
107 m (30–350 ft) using `n_gust_steps`. This sub-section is a placeholder only;
Phase 2 implementation is deferred.

#### b3) Continuous turbulence — 2-DOF rigid-body frequency response (Phase 1)

**Regulatory basis:** FAR 25.341(b); AC 25.341-1.

**Phase 1 method:** self-contained 2-DOF rigid-body plunge-pitch model with
strip-theory aerodynamics. No DLM, no NASTRAN required.

**Equations of motion (frequency domain):**

State vector: `[w_m_s (heave velocity), theta_rad (pitch angle)]`.
The 2×2 system in the frequency domain:

```
(-ω² × M_sys + j×ω × C_sys + K_sys) × X(ω) = F_gust(ω)
```

`M_sys`, `C_sys`, `K_sys` are assembled from aircraft mass properties and
strip-theory derivatives (`a_slope_nd`, `a_tail_nd`, `v_tail_nd`). The
short-period natural frequency and damping ratio are extracted from the
eigenvalues of the system matrix and stored as `omega_sp_rad_s` and
`zeta_sp_nd`.

**Frequency response functions:**

For each frequency in the grid `omega_rad_s`, solve the 2×2 system to yield:

```
h_nz_nd(jω)  — complex FRF: load factor per unit gust velocity [(m/s)/(m/s)]
h_my_nm(jω)  — complex FRF: wing root bending moment per unit gust velocity [N·m/(m/s)]
```

Frequency grid: logarithmically spaced, 0.01–100 rad/s, ≥ 500 points.

**Von Kármán turbulence PSD (FAR 25.341(b), AC 25.341-1):**

```
phi_u_m2_s(ω) = sigma_w_m_s² × (l_turb_m / π) ×
    (1 + (8/3) × (1.339 × l_turb_m × ω / v_tas_m_s)²) /
    (1 + (1.339 × l_turb_m × ω / v_tas_m_s)²)^(11/6)
```

`sigma_w_m_s` from `APP_CONFIG` (default 1.0 m/s).
`l_turb_m = 762 m` (2 500 ft) per AC 25.341-1.

**RMS load computation:**

```python
sigma_nz_nd = sqrt(trapz(abs(h_nz_nd)**2 * phi_u_m2_s, omega_rad_s))
sigma_my_nm = sqrt(trapz(abs(h_my_nm)**2 * phi_u_m2_s, omega_rad_s))
```

**Design limit loads:**

```
nz_limit_nd = k_sigma_nd × sigma_nz_nd
my_limit_nm = k_sigma_nd × sigma_my_nm
```

`k_sigma_nd = 3.0` (limit load factor method per AC 25.341-1); configurable
in `config/defaults.json`.

**Primary variables:** `omega_sp_rad_s`, `zeta_sp_nd`, `phi_u_m2_s`,
`h_nz_nd`, `h_my_nm`, `sigma_nz_nd`, `sigma_my_nm`, `sigma_w_m_s`,
`l_turb_m`, `k_sigma_nd`, `omega_rad_s`

**Modules:** `gust.py` (see decision.md §11) → `aero_db.py` → `loads.py`

##### b3-Phase2) Continuous turbulence — DLM/NASTRAN PSD (Phase 2 / deferred)

Phase 2 replaces the 2-DOF rigid-body FRF with FRFs from a full NASTRAN DLM or
ZONA51 aerodynamic analysis on the flexible structure. Regulatory basis: FAR
25.341(b); AC 25.341-1. Deferred to a future release.

---

### c) Static ground loads (ground handling)

**Regulatory basis:**

| Case | FAR 25 / CS-25 | FAR 23 / CS-23 |
|---|---|---|
| Ground handling conditions — general | 25.489 | 23.489 |
| Taxi, takeoff and landing roll | 25.491 | 23.491 |
| Side load (lateral) | 25.485 | 23.485 |
| Braked roll | 25.493 | 23.493 |
| Turning (taxiing) | 25.495 | 23.495 |
| Tail wheel yawing | 25.497 | 23.497 |
| Nose-wheel yaw and steering | 25.499 | 23.499 |
| Pivoting | 25.503 | 23.503 |
| Reversed braking | 25.507 | 23.507 |
| Towing loads | 25.509 | 23.509 |
| Jacking and tie-down provisions | 25.519 | 23.519 |

> **FAR 23 / CS-23 column — reference only.** FAR 23 is not implemented in the
> current release (Decision 6, Option C). All computation uses FAR 25 / CS-25
> formulas. When FAR 23 is implemented, formula dispatch will occur via
> `src/far_reg.py` and a `cert_basis` field in the condition list; see
> `doc/architecture.md §FAR 23 provision`.

**Method:** Quasi-static force and moment balance. No aerodynamic loads; no time
integration. Applied loads (brake torque, tow force, centrifugal force) are
balanced by inertia reactions at the CG and structural loads at attachment points.

Ground handling cases and their governing applied loads:

| Case | Applied load | FAR 25 / CS-25 | FAR 23 / CS-23 |
|---|---|---|---|
| Braked roll | `t_brake_nm` = `mu_brake_nd` × `n_gear_n` × `r_wheel_m` | 25.493 | 23.493 |
| Ground turn (taxiing) | Centrifugal = `m_ac_kg` × `v_ground_m_s`² / `r_turn_m` | 25.495 | 23.495 |
| Nose-wheel yaw | Lateral side force at nose gear | 25.499 | 23.499 |
| Towing | Tow force at tow fitting; direction per FAR/CS 25.509 | 25.509 | 23.509 |
| Pivoting | Friction at one main gear with other gear as pivot | 25.503 | 23.503 |
| Jacking | Vertical jack load at each jack point | 25.519 | 23.519 |

> **FAR 23 / CS-23 column — reference only.** FAR 23 is not implemented in the
> current release (Decision 6, Option C). All computation uses FAR 25 / CS-25
> formulas. When FAR 23 is implemented, formula dispatch will occur via
> `src/far_reg.py` and a `cert_basis` field in the condition list; see
> `doc/architecture.md §FAR 23 provision`.

**Sequence:**

1. Define ground load case: applied load magnitude, direction, and attachment point.
2. Compute inertia reactions at CG:
   ```
   f_inertia_n = m_ac_kg × nx_nd × G_M_S2    (braking)
   f_inertia_n = m_ac_kg × ny_nd × G_M_S2    (lateral cases)
   ```
3. Sum all applied and inertia loads to LRA section cuts using `loads.py`.
4. No aerodynamic contribution (speed too low or aircraft at rest).

Friction coefficient for braked roll: `mu_brake_nd` is specified in the
condition list; typical value 0.80 for dry runway per FAR 25.493.

**Primary variables:** `nx_nd`, `ny_nd`, `t_brake_nm`, `mu_brake_nd`,
`v_ground_m_s`, `r_turn_m`, `n_gear_n`

**Modules:** `ground.py` → `mass_model.py` → `loads.py`

---

### d) Dynamic ground and landing loads

**Regulatory basis:**

| Case | FAR 25 / CS-25 | FAR 23 / CS-23 |
|---|---|---|
| Landing loads — general conditions and assumptions | 25.473 | 23.473 |
| Landing gear arrangement | 25.477 | 23.477 |
| Level landing conditions | 25.479 | 23.479 |
| Tail-down landing conditions | 25.481 | 23.481 |
| One-gear landing conditions | 25.483 | 23.483 |
| Side load / lateral drift | 25.485 | 23.485 |
| Rebound landing | 25.487 | 23.487 |
| Taxi, takeoff and landing roll | 25.491 | 23.491 |
| Ground load dynamic conditions | 25.511 | 23.511 |
| Landing gear dynamic loads — implementation guidance | AC 25.491-1 | — |

> **FAR 23 / CS-23 column — reference only.** FAR 23 is not implemented in the
> current release (Decision 6, Option C). All computation uses FAR 25 / CS-25
> formulas. When FAR 23 is implemented, formula dispatch will occur via
> `src/far_reg.py` and a `cert_basis` field in the condition list; see
> `doc/architecture.md §FAR 23 provision`.

**Method:** Two options — quasi-static reserve energy method (simpler) or dynamic
impact analysis (higher fidelity). The method is subject to decision.md §3.

#### d1) Quasi-static reserve energy method (FAR/CS 25.473 default)

The peak vertical gear reaction is derived from energy conservation, assuming the
gear absorbs the kinetic energy of the sink rate over the gear stroke:

```
f_gear_n = w_aircraft_n × eta_gear_nd
           × (1 + v_sink_m_s² / (2 × G_M_S2 × d_stroke_m))
```

where:
- `eta_gear_nd` = gear absorption efficiency (typically 0.80 per FAR 25.473(b))
- `d_stroke_m` = available gear stroke (from gear design data or condition input)
- `v_sink_m_s` = design sink rate (3.05 m/s at max landing weight; 1.83 m/s at
  max takeoff weight, per FAR/CS 25.473(a))

This peak gear reaction is treated as a quasi-static vertical load applied at the
gear attachment point. The resulting aircraft loads are computed as a static case
with an effective load factor:

```
nz_eff_nd = f_gear_n / w_aircraft_n
```

#### d2) Landing sub-cases

Each sub-case modifies how the gear reaction is distributed and applies additional
load components:

| Sub-case | Vertical load | Lateral load | Drag load | FAR 25 / CS-25 | FAR 23 / CS-23 |
|---|---|---|---|---|---|
| Level landing (2-point) | Full gear reaction split per strut geometry | — | 0.25 × vertical (aft) | 25.479 | 23.479 |
| Tail-down landing | Main gear reaction only; nose gear unloaded | — | 0.25 × vertical | 25.481 | 23.481 |
| One-gear landing | 100% of limit vertical at one main gear | 0.25 × vertical (outboard) | per 25.479 | 25.483 | 23.483 |
| Lateral drift | Per level landing | 0.25 × vertical (side) | — | 25.485 | 23.485 |
| Rebound | Aircraft lifts off after ground contact; gear fully extended | — | — | 25.487 | 23.487 |

> **FAR 23 / CS-23 column — reference only.** FAR 23 is not implemented in the
> current release (Decision 6, Option C). All computation uses FAR 25 / CS-25
> formulas. When FAR 23 is implemented, formula dispatch will occur via
> `src/far_reg.py` and a `cert_basis` field in the condition list; see
> `doc/architecture.md §FAR 23 provision`.

For tail-down landing, the aircraft contacts at angle `alpha_td_rad` (the attitude
at which the tail structure first contacts the runway), applying a nose-up
pitching moment in addition to the vertical gear reaction.

#### d3) Dynamic impact analysis (if selected in decision.md §3)

Model landing gear as a spring-damper system:

```
f_gear_n(t) = k_gear_n_m × x_m(t) + c_gear_ns_m × x_dot_m_s(t)
```

Integrate the coupled aircraft + gear equations of motion from initial conditions
(aircraft at `v_sink_m_s` descent rate, gear unloaded) until gear stroke is exhausted
or the aircraft rebounds. Extract the time history of gear attachment loads and
airframe section loads. Critical loads are the extrema over the time history.

**Primary variables:** `v_sink_m_s`, `d_stroke_m`, `eta_gear_nd`, `nz_eff_nd`,
`f_gear_n`, `alpha_td_rad`, `k_gear_n_m`, `c_gear_ns_m`, `nx_nd`, `ny_nd`

**Modules:** `ground.py` → `mass_model.py` → `loads.py`

---

### e) Flap / high-lift loads

**Regulatory basis:**

| Load case | FAR 25 / CS-25 |
|---|---|
| High lift device — flap/slat extended conditions | 25.345 |
| Limit maneuver load factors with high-lift devices | 25.345(a) |
| Gust loads with high-lift devices | 25.345(b) |

**Method:** Identical to the static flight loads method (§a) for maneuver cases and
the discrete gust method (§b2) for gust cases, with the following differences:

1. A non-zero `flap_deg` column in the condition CSV activates the Category E
   handler. Routing to §e is triggered by `flap_deg > 0`, not by a separate
   `maneuver_type` value.
2. The aerodynamic database uses the flap-deployed configuration increment tables
   (baseline table tag includes the flap configuration; see `doc/loads_aero_db.md`).
3. The maneuver load factor envelope is limited per FAR 25.345(a): at V_F, n_z
   must not exceed the value from the condition list (supplied by LOAD_CASE).
4. Aeroelastic corrections apply to flap-deployed configurations using the same
   `aeroelastic.py` path as §a.

**Supported `maneuver_type` values:** `symmetric_pullup`, `pushover`,
`high_lift_gust`.

**Primary variables:** `delta_f_rad`, `nz_nd`, `v_eas_m_s`, `u_gust_m_s`,
plus all §a and §b2 primary variables.

**Modules:** `trim.py` → `aero_db.py` → `loads.py` → `aeroelastic.py`

---

### f) Control surface loads (deferred — Phase 2)

**Regulatory basis:** FAR 25.395 (pilot applied loads), 25.397 (surface balance
loads), 25.405 (secondary control loads).

**Status:** Deferred to Phase 2. No analysis code or CSV schema is defined in Phase 1.
The Category F slot is reserved in the TUI and `data/conditions/control_surface/`
directory. This section is a placeholder; content will be added when Phase 2 is
implemented.

---

## Module implementation notes

The sections below describe each computation module's role, allowed imports,
and internal behavior. These are the implementation counterpart to the analysis
method descriptions above.

### `aero_db.py` — Aerodynamic database interpolation

Loads strip load tables (`cn_sec_nd`, `cm_sec_nd`, `cc_sec_nd`) and incremental
tables (control surface deflections, angular rates) from CSV files. Interpolates
to produce spanwise arrays for a given flight state. Used by static flight loads
(§a), dynamic flight loads (§b), and indirectly by ground loads when aerodynamic
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

Used by: static flight loads (§a) and as the initial state for dynamic flight
loads (§b).

Solves the three-equation trim balance (lift = weight × `nz_nd`, pitch moment = 0,
thrust = drag) using `scipy.optimize.root` with tolerance `APP_CONFIG["trim_tol"]`.

**Solve variables:** `alpha_rad`, `delta_e_rad`, `t_thrust_n`

**Inputs:** `h_m`, `v_eas_m_s`, `nz_nd`, `x_cg_m`, aircraft geometry.

**Outputs:** dict of solved flight state variables plus residuals for convergence
checking. The trim result dict is passed as an argument to `loads.compute_loads`.

---

### `maneuver.py` — Maneuver time history

Used by: dynamic flight loads (§b1).

Integrates the equations of motion over a prescribed maneuver profile using
`scipy.integrate.solve_ivp`. Supported types: symmetric pull-up, push-over,
checked maneuver, rolling pull-out, yaw maneuver.

**Output:** time array `t_s[k]` and section load arrays `vz_n[i,k]`,
`mx_nm[i,k]`, etc., at each LRA station `i` and time step `k`. Critical
instant per load component extracted by `argmax`/`argmin` over the time axis.

---

### `ground.py` — Ground loads

Used by: static ground loads (§c) and dynamic ground and landing loads (§d).
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

### `loads.py` — Loads summation

The final summation step for all four analysis methods. Receives the flight or
ground state as arguments (not by importing `trim` or `maneuver` directly).

**Aerodynamic contribution (flight loads):** integrates `cn_sec_nd`, `cm_sec_nd`,
`cc_sec_nd` arrays multiplied by `q_dyn_pa` and local chord over each strip panel
(trapezoid rule), then sums to LRA section cuts via `lra.sum_to_lra`.

**Inertia contribution (all methods):** for each point mass, computes
`f_inertia_n = m_ac_kg × G_M_S2 × nz_nd` (or `nx_nd`, `ny_nd` for ground
cases) and the moment arm to the LRA, then sums to section cuts.

**Applied load contribution (ground handling/landing):** external forces
(`f_gear_n`, tow force, `t_brake_nm`) are added at their attachment points and
summed to LRA section cuts identically to inertia loads.

Applies `FS = 1.5` to all limit loads to produce ultimate loads per FAR 25.303.

**Output:** `vz_n[i]`, `vx_n[i]`, `fy_n[i]`, `mx_nm[i]`, `my_nm[i]`,
`mz_nm[i]` at each LRA station `i` — both limit and ultimate.

---

### `nastran_out.py` — NASTRAN FORCE/MOMENT card writer

Formats the per-condition section load arrays from `loads.py` as NASTRAN bulk
data cards and writes `data/outputs/<name>_loads.bdf`. No computation; pure
formatting.

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

Used by: static flight loads (§a) only. Not applied to ground loads.

Applies structural flexibility corrections via the flexibility matrix `f_flex`.
Iterates between aerodynamic load and elastic deflection until convergence
within `APP_CONFIG["flex_tol"]`.

**Aeroelastic effectiveness:** `e_flex_nd = η_flexible / η_rigid` per control
surface. Values below zero indicate control reversal; see decision.md §17.

**Jig shape:** backs out the unloaded geometry from the cruise trim condition
by inverting the aero-structural coupling. The jig shape is the manufactured
geometry that deforms to the design cruise shape under cruise loads.

**Inputs:** `f_flex` (flexibility matrix, units m/N or m/(N·m) depending on
load type), cruise trim state dict, baseline rigid section loads from `loads.py`.

**Outputs:** flexibility-corrected section load arrays, `e_flex_nd` per surface,
jig shape station offsets in metres.

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
