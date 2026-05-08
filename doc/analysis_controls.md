# Category F — Control Surface Loads (CONTROLS)

> **General rules** (naming conventions, unit standards, symbol tables,
> module implementation notes) are in [`analysis_code.md`](analysis_code.md).
> This document is the **Phase 2 design specification** for control surface
> structural load analysis. No analysis code or CSV schema is defined in Phase 1.
> The Category F TUI slot is reserved and `data/conditions/control_surface/`
> is created but remains empty.

---

## Status

**Deferred to Phase 2.** See `dev_plan.md §Deferred` and `decision.md §9`.

---

## Regulatory basis

| Load case | FAR 25 / CS-25 |
|---|---|
| Control surface loads — general | 25.391 |
| Pilot applied limit loads | 25.395 |
| Balance loads | 25.397 |
| Dual control systems | 25.399 |
| Trim tabs | 25.405 |
| Secondary control system loads | 25.405 |
| Hinge moment loads | 25.407 |
| Ground gust conditions | 25.415 |
| Control system locking | 25.417 |
| Aileron and rudder loads | 25.423–25.427 |

---

## Method (Phase 2 specification)

Control surface structural loads are derived from limit pilot-applied forces and
maximum control deflections. Three sub-paths are required:

### F.1 — Hinge moment from aerodynamic loading

At maximum control deflection (and maximum pilot-applied hinge moment), the
aerodynamic hinge moment is the primary structural load on the surface structure.
Computed from the `aero_db.py` increment table at the design deflection and
the associated trim flight state:

```
hm_aero_nm = cm_hinge_nd × q_dyn_pa × c_control_m² × s_control_m2
```

where `cm_hinge_nd` is the hinge moment coefficient, `c_control_m` is the
control surface chord, and `s_control_m2` is the control surface planform area.

### F.2 — Limit pilot force loads

Per FAR 25.395, the structure must withstand the loads produced by the
limit pilot forces applied simultaneously with the maximum control deflection:

```
f_pilot_n  = limit_pilot_force_n   (from FAR 25.397 table, function of control type)
hm_pilot_nm = f_pilot_n × arm_m    (moment arm from hinge to actuator/cable attachment)
```

### F.3 — Balance (mass balance and aerodynamic balance) loads

Tab and balance loads from the configuration geometry. Applied as concentrated
moments at the hinge line.

---

## Condition list columns (Category F — Phase 2 specification)

| Column | Code variable | Notes |
|---|---|---|
| `condition_id` | `condition_id` | String; unique per CSV row |
| `control_surface` | `control_surface` | String: `elevator` \| `aileron` \| `rudder` \| `tab` |
| `delta_control_deg` | → `delta_control_rad` | Control deflection [deg]; `condition.py` converts |
| `f_pilot_n` | `f_pilot_n` | Limit pilot force [N]; per FAR 25.397 |
| `h_m` | `h_m` | Pressure altitude [m] |
| `v_eas_m_s` | `v_eas_m_s` | Design speed for the case [m/s] |
| `fos` | `fos_nd` | Factor of safety; `1.5` standard |

---

## Primary variables (Phase 2 specification)

`cm_hinge_nd`, `hm_aero_nm`, `f_pilot_n`, `hm_pilot_nm`, `c_control_m`,
`s_control_m2`, `delta_e_rad`, `delta_a_rad`, `delta_r_rad`, `q_dyn_pa`

## Modules (Phase 2 specification)

`aero_db.py` (for aerodynamic hinge moments) → `loads.py`
