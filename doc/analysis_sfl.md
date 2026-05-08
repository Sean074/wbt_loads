# Category A — Static Flight Loads (SFL)

> **General rules** (naming conventions, unit standards, symbol tables,
> module implementation notes) are in [`analysis_code.md`](analysis_code.md).
> This document covers the SFL-specific regulatory basis, analysis sequence,
> primary variables, and deferred sub-categories.

---

## Regulatory basis

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

---

## Sub-categories

| ID | Name | Description | Phase |
|---|---|---|---|
| A.1 | Longitudinal — Balanced | Symmetric pull-up and push-over at fixed `nz_nd` | 1 |
| A.2 | Longitudinal — Maneuver | Checked maneuver; load factor from ODE integration | 1 (via DFL §b1) |
| A.3 | Lateral — Balanced | Rolling pull-out; combined roll rate + symmetric pull-up | 1 |
| A.4 | Lateral — Maneuver | Yaw maneuver with prescribed rudder input | 1 |

Sub-categories A.2 and A.3/A.4 that require time integration are computed
via the DFL maneuver path (`maneuver.py`); their critical instant loads are then
treated as static equivalent Category A results for NASTRAN output purposes.

---

## Method

Quasi-static equilibrium. The aircraft is in a balanced, non-accelerating
flight state (or a steady-state maneuver) defined by a fixed load factor `nz_nd`.
No time integration is performed for A.1 balanced conditions.

---

## Analysis sequence

### 1. Trim solve (`trim.py`)

Find α, δ_e, and thrust such that the three equilibrium equations are satisfied
simultaneously:

```
L = nz_nd × w_aircraft_n           (lift equals weight × load factor)
ΣM_pitch = 0                        (pitching moment balance at CG)
T = D                               (thrust equals drag)
```

Solved by `scipy.optimize.root` with tolerance `APP_CONFIG["trim_tol"]`.
Solve variables: `alpha_rad`, `delta_e_rad`, `t_thrust_n`.

### 2. Aerodynamic interpolation (`aero_db.py`)

Evaluate strip load arrays at the trimmed flight state:

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

### 3. Loads summation (`loads.py`)

Integrate strip loads to LRA section cuts.

Aerodynamic contribution per strip panel of width `dy_m`:

```
dvz = cn_sec_nd × q_dyn_pa × c_m × dy_m
dmx = dvz × (y_lra_m - y_strip_m)          (bending moment arm)
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

### 4. Aeroelastic corrections (`aeroelastic.py`) — when elastic model present

Apply structural flexibility correction:

```
{δ} = [f_flex] × {P}     (deflection from flexibility matrix × load vector)
```

Re-evaluate strip loads at the deflected geometry. Iterate between steps 2–4
until the change in section loads between iterations is below
`APP_CONFIG["flex_tol"]`. When the elastic model is active, `menu.py` calls
`aero_trim.solve_trim(...)` instead of `trim.solve_trim(...)` directly; the
coupled loop lives in `aero_trim.py`.

Aeroelastic effectiveness: `e_flex_nd = η_flexible / η_rigid` per control
surface. When `e_flex_nd < 0`, `aeroelastic.py` raises
`ValueError("Control reversal: <surface> at condition <ID> (e_flex_nd = <value>)")`.
The calling handler catches this, prints `[red]Error: ...[/red]`, and skips
the condition without writing output. See `analysis_code.md §aeroelastic.py`.

### 5. Ultimate loads (`loads.py`)

Multiply limit loads by the per-condition `fos_nd` (read from the condition
row) to produce ultimate loads. `fos_nd = 1.5` is the standard value per
FAR 25.303; `fos_nd = 1.0` applies when regulations define the load condition
as limit treated as ultimate (e.g. certain failure cases under FAR/CS 25.302).
All WBT_LOADS outputs are ultimate loads; `fos_nd` is carried through the
output file alongside the load magnitudes so the derivation is traceable.

---

## Condition list columns (Category A)

| Column | Code variable | Notes |
|---|---|---|
| `condition_id` | `condition_id` | String; unique per CSV row |
| `description` | `description` | Human-readable label |
| `category` | `category` | Must be `maneuver` for symmetric, `gust` for gust sub-cases |
| `maneuver_type` | `maneuver_type` | `symmetric_pullup` \| `push_over` \| `rolling_pullout` \| `yaw` \| `checked` |
| `h_m` | `h_m` | Pressure altitude [m] |
| `v_eas_m_s` | `v_eas_m_s` | Equivalent airspeed [m/s] |
| `nz_nd` | `nz_nd` | Normal load factor (limit) |
| `m_ac_kg` | `m_ac_kg` | Aircraft gross mass [kg] |
| `x_cg_nd` | `x_cg_nd` | CG position, fraction MAC |
| `elevator_deg` | → `delta_e_rad` | Elevator trim input, degrees; `condition.py` converts |
| `aileron_deg` | → `delta_a_rad` | Aileron input, degrees |
| `rudder_deg` | → `delta_r_rad` | Rudder input, degrees |
| `fos` | `fos_nd` | Factor of safety; `1.5` standard, `1.0` for FAR 25.302 failure cases |

---

## Primary variables

`nz_nd`, `alpha_rad`, `q_dyn_pa`, `mach_nd`, `delta_e_rad`,
`cn_sec_nd`, `cm_sec_nd`, `cc_sec_nd`, `vz_n`, `mx_nm`,
`my_nm`, `nz_ult_nd`, `e_flex_nd`

## Modules

`trim.py` → `aero_db.py` → `loads.py` → `aeroelastic.py` (optional)
