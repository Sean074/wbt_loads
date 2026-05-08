# Category B — Dynamic Flight Loads (DFL)

> **General rules** (naming conventions, unit standards, symbol tables,
> module implementation notes) are in [`analysis_code.md`](analysis_code.md).
> This document covers the DFL-specific regulatory basis, analysis sequences
> for maneuver time history and gust response, primary variables, and deferred
> Phase 2 sub-sections.

---

## Regulatory basis

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

---

## b1) Maneuver time history

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
| Checked maneuver | α, q (pitch rate reversal at peak n_z) | 25.331(c) | 23.331 |
| Rolling pull-out | α, q, p, φ | 25.349 | 23.349 |
| Yaw maneuver | β, r (with prescribed δ_r input) | 25.351 | 23.351 |

> **FAR 23 / CS-23 column — reference only.** See regulatory basis note above.

**Critical instant extraction:** scan the complete time history for the maximum
positive and maximum negative value of each load component at each LRA station.
The time-point that produces each extremum is the critical instant for that
component.

**Primary variables:** `t_s`, `alpha_rad`, `q_pitch_rad_s`, `p_roll_rad_s`,
`r_yaw_rad_s`, `phi_rad`, `beta_rad`, `delta_r_rad`, `vz_n`, `mx_nm`

**Modules:** `maneuver.py` → `aero_db.py` → `loads.py`

---

## b2) Discrete gust — static equivalent method (Phase 1)

**Regulatory basis:** original FAR Part 25 Appendix G, pre-Amendment 25-86
(1996), as described in Lomax, *Structural Loads Analysis for Commercial
Transport Aircraft*, AIAA 1996, Chapter 4.

**Phase 1 method — no 1-cosine profile; no H sweep.**

### Design gust velocities

Pre-1996 FAR Part 25 Appendix G table, converted to SI at ingestion in `gust.py`:

| Altitude | Imperial | SI |
|---|---|---|
| Sea level (0 m) | 50 fps EAS | 15.24 m/s EAS |
| 20 000 ft (6 096 m) | 25 fps EAS | 7.62 m/s EAS |

Interpolation: linear between 0 m and 6 096 m. Above 6 096 m: controlled by
`APP_CONFIG["gust_velocity_above_20kft"]` — `"extrapolate"` (default) or `"cap"`.

### Gust alleviation factor

```
k_gust_nd = 0.88 × mu_g_nd / (5.3 + mu_g_nd)

mu_g_nd = 2 × m_ac_kg / (rho_kg_m3 × mac_m × s_ref_m2 × a_slope_nd)
```

### Incremental load factor

All quantities in SI:

```
delta_nz_nd = (k_gust_nd × u_gust_m_s × v_eas_m_s × a_slope_nd)
              / (2 × (w_aircraft_n / s_ref_m2))
```

where `w_aircraft_n = m_ac_kg × G_M_S2`. Both positive and negative increments
are evaluated: `nz_nd = 1.0 ± delta_nz_nd`. `a_slope_nd` is the whole-aircraft
lift curve slope (per radian) from the trim aerodynamic state.

`h_gust_m`, `gust_gradient_min_ft`, `gust_gradient_max_ft`, and `n_gust_steps`
are **not used** in Phase 1; they are reserved for the Phase 2 TDG.

**Routing:** `maneuver_type` in `{discrete_gust_vertical, discrete_gust_lateral}`

**Primary variables:** `u_gust_m_s`, `k_gust_nd`, `mu_g_nd`, `a_slope_nd`,
`delta_nz_nd`, `rho_kg_m3`, `mac_m`, `s_ref_m2`, `m_ac_kg`, `w_aircraft_n`,
`v_eas_m_s`

**Modules:** `gust.py` → `aero_db.py` → `loads.py`

---

### b2-Phase2) Discrete gust — 1-cosine TDG (Phase 2 / deferred)

**Regulatory basis:** FAR 25.341(a); AC 25.341-1 (Amendment 25-86 and later).

Gust velocity profile:
`u_gust_inst_m_s(s) = (u_gust_m_s / 2) × (1 − cos(π × s / h_gust_m))`
for `0 ≤ s ≤ 2 × h_gust_m`. Design gust velocities from current FAR 25.341(a)
table: 17.07 m/s EAS at sea level, 6.36 m/s at 18 288 m. H sweep from 9 to
107 m (30–350 ft) using `n_gust_steps`. This sub-section is a placeholder only;
Phase 2 implementation is deferred.

---

## b3) Continuous turbulence — 2-DOF rigid-body frequency response (Phase 1)

**Regulatory basis:** FAR 25.341(b); AC 25.341-1.

**Phase 1 method:** self-contained 2-DOF rigid-body plunge-pitch model with
strip-theory aerodynamics. No DLM, no NASTRAN required.

### Equations of motion (frequency domain)

State vector: `[w_m_s (heave velocity), theta_rad (pitch angle)]`.
The 2×2 system in the frequency domain:

```
(-ω² × M_sys + j×ω × C_sys + K_sys) × X(ω) = F_gust(ω)
```

`M_sys`, `C_sys`, `K_sys` are assembled from aircraft mass properties and
strip-theory derivatives (`a_slope_nd`, `a_tail_nd`, `v_tail_nd`). The
short-period natural frequency and damping ratio are extracted from the
eigenvalues of the system matrix and stored as `omega_sp_rad_s` and `zeta_sp_nd`.

### Frequency response functions

For each frequency in the grid `omega_rad_s`, solve the 2×2 system to yield:

```
h_nz_nd(jω)  — complex FRF: load factor per unit gust velocity [(m/s)/(m/s)]
h_my_nm(jω)  — complex FRF: wing root bending moment per unit gust velocity [N·m/(m/s)]
```

Frequency grid: logarithmically spaced, 0.01–100 rad/s, ≥ 500 points.

### Von Kármán turbulence PSD (FAR 25.341(b), AC 25.341-1)

```
phi_u_m2_s(ω) = sigma_w_m_s² × (l_turb_m / π) ×
    (1 + (8/3) × (1.339 × l_turb_m × ω / v_tas_m_s)²) /
    (1 + (1.339 × l_turb_m × ω / v_tas_m_s)²)^(11/6)
```

`sigma_w_m_s` from `APP_CONFIG` (default 1.0 m/s).
`l_turb_m = 762 m` (2 500 ft) per AC 25.341-1.

### RMS load computation

```python
sigma_nz_nd = sqrt(trapz(abs(h_nz_nd)**2 * phi_u_m2_s, omega_rad_s))
sigma_my_nm = sqrt(trapz(abs(h_my_nm)**2 * phi_u_m2_s, omega_rad_s))
```

### Design limit loads

```
nz_limit_nd = k_sigma_nd × sigma_nz_nd
my_limit_nm = k_sigma_nd × sigma_my_nm
```

`k_sigma_nd = 3.0` (limit load factor method per AC 25.341-1); configurable
in `config/defaults.json`.

**Routing:** `maneuver_type == continuous_turbulence`

**Primary variables:** `omega_sp_rad_s`, `zeta_sp_nd`, `phi_u_m2_s`,
`h_nz_nd`, `h_my_nm`, `sigma_nz_nd`, `sigma_my_nm`, `sigma_w_m_s`,
`l_turb_m`, `k_sigma_nd`, `omega_rad_s`

**Modules:** `gust.py` → `aero_db.py` → `loads.py`

---

### b3-Phase2) Continuous turbulence — DLM/NASTRAN PSD (Phase 2 / deferred)

Phase 2 replaces the 2-DOF rigid-body FRF with FRFs from a full NASTRAN DLM or
ZONA51 aerodynamic analysis on the flexible structure. Regulatory basis:
FAR 25.341(b); AC 25.341-1. Deferred to a future release.

---

## Condition list columns (Category B)

| Column | Code variable | Notes |
|---|---|---|
| `condition_id` | `condition_id` | String; unique per CSV row |
| `maneuver_type` | `maneuver_type` | `symmetric_pullup` \| `push_over` \| `checked` \| `rolling_pullout` \| `yaw` \| `discrete_gust_vertical` \| `discrete_gust_lateral` \| `continuous_turbulence` |
| `h_m` | `h_m` | Pressure altitude [m] |
| `v_eas_m_s` | `v_eas_m_s` | Equivalent airspeed [m/s] |
| `nz_nd` | `nz_nd` | Trim load factor (used as initial state for integration) |
| `m_ac_kg` | `m_ac_kg` | Aircraft gross mass [kg] |
| `x_cg_nd` | `x_cg_nd` | CG position, fraction MAC |
| `h_gust_m` | `h_gust_m` | Gust gradient distance [m] — Phase 2 TDG only; parsed but unused in Phase 1 |
| `fos` | `fos_nd` | Factor of safety; `1.5` standard |
