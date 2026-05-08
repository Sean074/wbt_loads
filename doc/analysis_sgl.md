# Category C — Static Ground Loads (SGL)

> **General rules** (naming conventions, unit standards, symbol tables,
> module implementation notes) are in [`analysis_code.md`](analysis_code.md).
> This document covers the SGL-specific regulatory basis, analysis sequence,
> primary variables, and condition list columns.

---

## Regulatory basis

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

---

## Method

Quasi-static force and moment balance. No aerodynamic loads; no time
integration. Applied loads (brake torque, tow force, centrifugal force) are
balanced by inertia reactions at the CG and structural loads at attachment points.

---

## Ground handling cases

| Case | Applied load | FAR 25 / CS-25 | FAR 23 / CS-23 |
|---|---|---|---|
| Braked roll | `t_brake_nm` = `mu_brake_nd` × `n_gear_n` × `r_wheel_m` | 25.493 | 23.493 |
| Ground turn (taxiing) | Centrifugal = `m_ac_kg` × `v_ground_m_s`² / `r_turn_m` | 25.495 | 23.495 |
| Nose-wheel yaw | Lateral side force at nose gear | 25.499 | 23.499 |
| Towing | Tow force at tow fitting; direction per FAR/CS 25.509 | 25.509 | 23.509 |
| Pivoting | Friction at one main gear with other gear as pivot | 25.503 | 23.503 |
| Jacking | Vertical jack load at each jack point | 25.519 | 23.519 |

> **FAR 23 / CS-23 column — reference only.** See regulatory basis note above.

Friction coefficient for braked roll: `mu_brake_nd` is specified in the
condition list; typical value 0.80 for dry runway per FAR 25.493.

---

## Analysis sequence

1. **Define ground load case** — applied load magnitude, direction, and
   attachment point from condition row.

2. **Compute inertia reactions at CG:**

   ```
   f_inertia_n = m_ac_kg × nx_nd × G_M_S2    (braking)
   f_inertia_n = m_ac_kg × ny_nd × G_M_S2    (lateral cases)
   ```

3. **Sum all applied and inertia loads to LRA section cuts** using `loads.py`.

4. **No aerodynamic contribution** (speed too low or aircraft at rest).

5. **Ultimate loads** — multiply limit section loads by `fos_nd` from the
   condition row.

---

## Condition list columns (Category C)

| Column | Code variable | Notes |
|---|---|---|
| `condition_id` | `condition_id` | String; unique per CSV row |
| `maneuver_type` | `maneuver_type` | `braked_roll` \| `ground_turn` \| `nose_wheel_yaw` \| `towing` \| `pivoting` \| `jacking` |
| `m_ac_kg` | `m_ac_kg` | Aircraft gross mass [kg] |
| `nx_nd` | `nx_nd` | Axial load factor (braking) |
| `ny_nd` | `ny_nd` | Lateral load factor (turning, yaw) |
| `nz_nd` | `nz_nd` | Vertical load factor |
| `v_ground_m_s` | `v_ground_m_s` | Ground speed [m/s] |
| `r_turn_m` | `r_turn_m` | Turn radius [m]; used for `ground_turn` |
| `mu_brake_nd` | `mu_brake_nd` | Brake friction coefficient; typically 0.80 |
| `r_wheel_m` | `r_wheel_m` | Wheel radius [m] |
| `fos` | `fos_nd` | Factor of safety; `1.5` standard |

---

## Primary variables

`nx_nd`, `ny_nd`, `t_brake_nm`, `mu_brake_nd`, `v_ground_m_s`, `r_turn_m`,
`n_gear_n`, `vz_n`, `vx_n`, `fy_n`, `mx_nm`, `my_nm`, `mz_nm`

## Modules

`ground.py` → `mass_model.py` → `loads.py`
