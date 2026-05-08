# Category E — Flap / High-Lift Loads (FLAPS)

> **General rules** (naming conventions, unit standards, symbol tables,
> module implementation notes) are in [`analysis_code.md`](analysis_code.md).
> This document is the **Phase 2 design specification** for the Flap/High-Lift
> analysis method. No analysis code or CSV schema is defined in Phase 1.
> The Category E TUI slot is reserved and `data/conditions/flap/` is created
> but remains empty.

---

## Status

**Deferred to Phase 2.** See `dev_plan.md §Deferred` and `decision.md §9`.

---

## Regulatory basis

| Load case | FAR 25 / CS-25 |
|---|---|
| High lift device — flap/slat extended conditions | 25.345 |
| Limit maneuver load factors with high-lift devices | 25.345(a) |
| Gust loads with high-lift devices | 25.345(b) |

---

## Method

Idealized pressure distributions matched to the section loads of a referenced
parent WBT condition. The parent condition (a Category A or B case already
solved) provides the integrated normal and chord loads at each strip station
over the flap span. An idealized chordwise pressure distribution is then
constructed so that:

- **Pn** (normal load, perpendicular to local chord) integrates over the flap
  chord to match the parent WBT strip normal load per unit span at that station.
- **Pc** (chord load, parallel to local chord) integrates over the flap chord to
  match the parent WBT strip chord load per unit span at that station.

The induced aeroelastic deflection is taken directly from the parent WBT case
result (the flexibility-corrected deflected geometry stored in the parent
condition output). No separate aeroelastic iteration is performed for the flap
case; the flap loads are applied to the already-deflected shape.

---

## Analysis sequence (Phase 2 specification)

### 1. Parent WBT case lookup

The condition list `ref_condition_id` column identifies the parent Category A or
B condition. Load the parent case output section loads and aeroelastic deflection
from the results cache.

### 2. Strip normal and chord loads from parent

At each spanwise station over the flap extent, extract:

```
fn_n_m[j]  = vz_n_parent[j] / dy_m[j]    (normal load per unit span, N/m)
fc_n_m[j]  = vx_n_parent[j] / dy_m[j]    (chord load per unit span, N/m)
```

### 3. Idealized chordwise pressure distribution

Construct Pn and Pc as distributions over the flap chord fraction `x_f` ∈ [0, 1]
(0 = flap hinge, 1 = trailing edge). The distribution shape (uniform, linear,
or user-supplied) is specified in the condition row via `pn_shape` and `pc_shape`.
Distributions are scaled so that:

```
∫ pn_pa(x_f) dx_f × c_flap_m = fn_n_m[j]
∫ pc_pa(x_f) dx_f × c_flap_m = fc_n_m[j]
```

where `c_flap_m` is the local flap chord (m).

Supported distribution shapes:

| Shape keyword | Pn / Pc profile | Notes |
|---|---|---|
| `uniform` | constant across chord | Conservative; default if not specified |
| `linear_LE` | linearly decreasing from hinge to TE | Higher loading near hinge |
| `linear_TE` | linearly increasing from hinge to TE | Higher loading near TE |
| `user` | tabulated in condition CSV columns `pn_x_*` / `pc_x_*` | Analyst-supplied shape |

### 4. Section loads summation (`loads.py`)

Integrate the Pn and Pc strip distributions over the flap span to LRA section
cuts, producing `vz_n`, `vx_n`, `mx_nm`, `my_nm` at each LRA station.
Moment arms are computed to the LRA using the deflected geometry from the
parent case.

### 5. Ultimate loads

Apply per-condition `fos_nd` from the condition list, identical to all other
categories.

---

## Condition list columns (Category E — Phase 2 specification)

| Column | Code variable | Notes |
|---|---|---|
| `condition_id` | `condition_id` | String; unique per CSV row |
| `ref_condition_id` | `ref_condition_id` | String; `condition_id` of the parent WBT Category A or B case |
| `flap_chord_m` | `c_flap_m` | Local flap chord (m); may be spanwise-varying via `flap_chord_*` columns |
| `pn_shape` | `pn_shape` | Distribution shape keyword for Pn; see table above |
| `pc_shape` | `pc_shape` | Distribution shape keyword for Pc; see table above |
| `flap_deg` | → `delta_f_rad` | Flap deflection [deg]; activates Category E handler when > 0 |
| `fos` | `fos_nd` | Factor of safety; `1.5` standard |

A non-zero `flap_deg` column in the condition CSV activates the Category E
handler. Routing to §e is triggered by `flap_deg > 0`; `ref_condition_id` is
then mandatory.

---

## Flap / high-lift pressure distribution variables

Variables specific to the idealized Pn / Pc method:

| Quantity | Code variable | SI unit | Notes |
|---|---|---|---|
| Normal pressure distribution | `pn_pa` | Pa | Chordwise pressure perpendicular to local flap chord; positive into upper surface |
| Chord pressure distribution | `pc_pa` | Pa | Chordwise pressure parallel to local flap chord; positive aft |
| Normal load per unit span | `fn_n_m` | N/m | Integral of `pn_pa` over flap chord at one strip station |
| Chord load per unit span | `fc_n_m` | N/m | Integral of `pc_pa` over flap chord at one strip station |
| Local flap chord | `c_flap_m` | m | Chord of flap element at strip station (hinge line to trailing edge) |
| Chordwise fraction (flap-local) | `x_f_nd` | — | 0 at hinge line, 1 at trailing edge |
| Reference WBT condition | `ref_condition_id` | — | String; `condition_id` of the parent Category A or B case |

---

## Primary variables

`pn_pa`, `pc_pa`, `fn_n_m`, `fc_n_m`, `c_flap_m`, `ref_condition_id`,
`delta_f_rad`, `vz_n`, `vx_n`, `mx_nm`, `my_nm`

## Modules

`loads.py` (using parent case output; no trim or aero DB call)
