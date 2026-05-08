# Category D — Dynamic Ground Loads (DGL)

> **General rules** (naming conventions, unit standards, symbol tables,
> module implementation notes) are in [`analysis_code.md`](analysis_code.md).
> This document covers the DGL-specific regulatory basis, analysis sequences
> for landing and taxi/braking loads, primary variables, and the deferred
> Phase 2 dynamic impact method.

---

## Regulatory basis

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

---

## d1) Quasi-static reserve energy method — Phase 1 (FAR/CS 25.473)

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
gear attachment point. The resulting effective load factor is:

```
nz_eff_nd = f_gear_n / w_aircraft_n
```

---

## d2) Landing sub-cases

Each sub-case modifies how the gear reaction is distributed and adds additional
load components:

| Sub-case | `maneuver_type` | Vertical load | Lateral load | Drag load | FAR 25 / CS-25 |
|---|---|---|---|---|---|
| Level landing (2-point) | `level_landing` | Full gear reaction split per strut geometry | — | 0.25 × vertical (aft) | 25.479 |
| Tail-down landing | `tail_down_landing` | Main gear only; nose gear unloaded | — | 0.25 × vertical | 25.481 |
| One-gear landing | `one_gear_landing` | 100% of limit vertical at one main gear | 0.25 × vertical (outboard) | per 25.479 | 25.483 |
| Lateral drift | `lateral_drift` | Per level landing | 0.25 × vertical (side) | — | 25.485 |
| Rebound | `rebound_landing` | Aircraft lifts off after ground contact; gear fully extended | — | — | 25.487 |

For tail-down landing, the aircraft contacts at angle `alpha_td_rad` (the attitude
at which the tail structure first contacts the runway), applying a nose-up
pitching moment in addition to the vertical gear reaction.

---

## d3) Dynamic impact analysis — Phase 2 (deferred)

Model landing gear as a spring-damper system:

```
f_gear_n(t) = k_gear_n_m × x_m(t) + c_gear_ns_m × x_dot_m_s(t)
```

Integrate the coupled aircraft + gear equations of motion from initial conditions
(aircraft at `v_sink_m_s` descent rate, gear unloaded) until gear stroke is
exhausted or the aircraft rebounds. Extract the time history of gear attachment
loads and airframe section loads. Critical loads are the extrema over the time
history.

Status: **Deferred to Phase 2.** Phase 1 uses only the quasi-static method (d1).

---

## Analysis sequence (Phase 1 — quasi-static)

1. **Read condition row** — identify `maneuver_type` and extract `v_sink_m_s`,
   `d_stroke_m`, `eta_gear_nd` from the condition or gear properties file.

2. **Compute peak gear reaction** using the FAR 25.473 formula (§d1 above).

3. **Apply sub-case load distribution** (§d2) — distribute vertical, lateral,
   and drag loads per the active sub-case; place at gear attachment points.

4. **Compute inertia loads** at all mass points:

   ```
   f_inertia_n = m_ac_kg × G_M_S2 × nz_eff_nd    (vertical)
   ```

   Additional `nx_nd`, `ny_nd` for sub-cases with drag or lateral components.

5. **Sum to LRA section cuts** using `loads.py` → `vz_n`, `mx_nm`, etc.

6. **Ultimate loads** — multiply by `fos_nd` from the condition row.

---

## Condition list columns (Category D)

| Column | Code variable | Notes |
|---|---|---|
| `condition_id` | `condition_id` | String; unique per CSV row |
| `maneuver_type` | `maneuver_type` | See sub-case table above; also `taxi_bump` \| `abrupt_braking` |
| `m_ac_kg` | `m_ac_kg` | Aircraft gross mass [kg] |
| `v_sink_m_s` | `v_sink_m_s` | Design sink rate [m/s]; from FAR 25.473 or condition |
| `d_stroke_m` | `d_stroke_m` | Available gear stroke [m] |
| `eta_gear_nd` | `eta_gear_nd` | Gear absorption efficiency; typically 0.80 |
| `nz_bump_nd` | `nz_bump_nd` | Taxi bump load factor; used for `taxi_bump` (no energy formula) |
| `nx_nd` | `nx_nd` | Axial load factor; used for `abrupt_braking` |
| `alpha_td_rad` | `alpha_td_rad` | Tail-down contact attitude [rad]; used for `tail_down_landing` |
| `fos` | `fos_nd` | Factor of safety; `1.5` standard |

---

## Primary variables

`v_sink_m_s`, `d_stroke_m`, `eta_gear_nd`, `nz_eff_nd`, `f_gear_n`,
`alpha_td_rad`, `k_gear_n_m`, `c_gear_ns_m`, `nx_nd`, `ny_nd`,
`vz_n`, `mx_nm`, `my_nm`

## Modules

`ground.py` → `mass_model.py` → `loads.py`
