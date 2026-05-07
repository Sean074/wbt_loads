# Variable Naming, Unit, and Sign-Convention Standard

Applies to **all computation modules** in the WBT Loads project (`src/*.py`).
UI and menu code is excluded from the computation-variable rules but must convert
to/from SI at the presentation boundary.

**Cross-references:**
- `doc/aerospace_variables_reference.csv` — authoritative variable name registry
  (code name, SI unit, sign convention for every listed quantity)
- `CLAUDE.md` — project-wide SI requirement and mandatory documentation rules

---

## Core rules

1. **Use the registered name.** Every quantity with a row in
   `doc/aerospace_variables_reference.csv` must use the identifier in the
   `code_variable_name` column. Using any other name is a defect.

2. **Append the SI unit as a suffix.** The suffix makes the unit visible at
   every point of use. Pattern: `<symbol>_<si_unit_suffix>`.

3. **Observe the sign convention.** The `definition_of_positive` column in
   `aerospace_variables_reference.csv` defines the required positive direction.
   An opposite sign is a code defect even if the magnitude is correct.

4. **Convert at the boundary.** Input files in imperial units are converted to
   SI immediately at ingestion using named constants from `src/unit_convert.py`.
   Bare numeric conversion literals inside analysis functions are a defect.

---

## Unit suffix reference (SI throughout)

| Dimension | SI unit | Suffix | Common import name |
|---|---|---|---|
| Length / coordinate | metre | `_m` | — |
| Area | square metre | `_m2` | — |
| Mass | kilogram | `_kg` | — |
| Force | Newton | `_n` | lower-case `n`; distinguishes from `_nd` |
| Moment / torque | Newton-metre | `_nm` | lower-case `nm` |
| Pressure / stress | Pascal | `_pa` | — |
| Density | kg/m³ | `_kg_m3` | — |
| Speed | metre per second | `_m_s` | — |
| Angular rate | radian per second | `_rad_s` | — |
| Angle (internal) | radian | `_rad` | convert from `_deg` before computation |
| Angle (UI boundary) | degree | `_deg` | never pass to computation functions |
| Dimensionless | — | `_nd` | coefficients, ratios, Mach, load factors |
| Frequency (circular) | rad/s | `_rad_s` | same suffix as angular rate |
| Frequency (cyclic) | hertz | `_hz` | — |
| Spring stiffness | N/m | `_n_m` | e.g. `k_gear_n_m` |
| Damping | N·s/m | `_ns_m` | e.g. `c_gear_ns_m` |

---

## Coordinate systems

Two coordinate frames are used. Mixing them without an explicit transformation
is a defect.

### 1. Global structural reference frame

**Used for:** all position coordinates (LRA stations, beam nodes, mass model
attachment points), section-load reporting, and any structural geometry.

| Axis | Positive direction | Aircraft geometry |
|---|---|---|
| **x** | **AFT** | Fuselage station (FS) increases from nose (FS 0) toward tail |
| **y** | **STARBOARD** | Butt line (BL) increases from centerline (BL 0) outboard to right |
| **z** | **UP** | Waterline (WL) increases from datum (WL 0) upward |

**Origin:** aircraft datum — FS 0 / BL 0 / WL 0.

Variable names for structural frame positions: `x_m`, `y_m`, `z_m`.

**Frame handedness note:** This IS a right-handed coordinate system.
`x_aft × y_starboard = z_up` is exact: the cross product follows the standard
right-hand rule. Code computing cross-products in this frame may use standard
right-hand-rule formulas without any sign correction. The system differs from
the aerodynamic body-axis frame (x forward, z down) but both are right-handed;
the choice here matches the aircraft structural convention (fuselage stations /
butt lines / waterlines) used in NASTRAN aircraft models.

### 2. Aerodynamic body-axis frame

**Used for:** all aerodynamic coefficients (CL, CD, CM, Cn, Cl, CY), angles
(α, β), angular rates (p, q, r), body-axis velocity perturbations (u, v, w),
and all control surface deflections (δ_e, δ_a, δ_r, δ_f, δ_sp, δ_stab).

| Axis | Positive direction | Relation to structural frame |
|---|---|---|
| Body x | **FORWARD** | Opposite to structural x (aft) |
| Body y | **STARBOARD** | Same as structural y |
| Body z | **DOWN** | Opposite to structural z (up) |

Sign conventions per Anderson (*Introduction to Flight*) and Etkin (*Dynamics of
Flight*). This is a true right-handed frame (x_fwd × y_stbd = z_down).

**Important:** aerodynamic quantities must NOT be used directly in structural
frame computations. An explicit rotation (negating x and z components) is
required when transferring forces or moments from the aerodynamic frame to the
structural frame.

| Transformation | Formula |
|---|---|
| Force in structural frame | `[Fx_struct, Fy_struct, Fz_struct] = [-Fx_aero, Fy_aero, -Fz_aero]` |
| Moment in structural frame | `[Mx_struct, My_struct, Mz_struct] = [-Mx_aero, My_aero, -Mz_aero]` |

---

## Section loads sign convention (Lomax)

Section loads at each LRA cut follow **Lomax §5** (*Structural Loads Analysis
for Commercial Transport Aircraft*, AIAA 1996, Chapter 5). All loads are
referenced to the structural frame (x aft, y starboard, z up).

For a **right-wing cut** at spanwise coordinate `y_m = y_cut` (outboard free
body; cut-face normal = −ŷ):

| Quantity | Variable | Positive direction | Physical meaning under standard flight load |
|---|---|---|---|
| Vertical shear | `vz_n` | +z (upward) | Upward shear under lift; Lomax positive S |
| Chordwise shear | `vx_n` | +x (aft) | Aft-directed shear under drag |
| Spanwise axial | `fy_n` | +y (outboard) | Tension in span direction |
| Out-of-plane bending | `mx_nm` | Upward bending | Upper surface in compression; `Mx = ∫ fz·(y−y_cut) dy` |
| Torsion | `my_nm` | Leading edge UP | Nose-up twist; Lomax positive torsion |
| In-plane bending | `mz_nm` | +x displacement (aft) | Wing bends toward trailing edge |

**Sign derivations (structural frame):**

- **Vertical shear `vz_n`:** Force from inboard on outboard section in +z direction.
  Under positive lift (upward, +z), `vz_n > 0`. ✓

- **Out-of-plane bending `mx_nm`:** Right-hand rule about +x_aft axis: moment
  from inboard on outboard section that rotates the cut face from +y (starboard)
  toward +z (up). For the outboard free body loaded by upward lift:
  `Mx = ∫_y_cut^s_m fz(y) × (y − y_cut) dy > 0`. ✓

- **Torsion `my_nm`:** Right-hand rule about +y_starboard axis: positive rotation
  carries +z (up) toward +x (aft). A point at −x (the leading edge, which is
  forward of the elastic axis = negative x) rotates toward +z (upward).
  Therefore positive `my_nm` = leading edge moves upward = **Lomax positive
  torsion**. ✓

- **For the left wing** (y_cut < 0, outboard free body has cut-face normal = +ŷ),
  the signs of `vz_n` and `mx_nm` are unchanged (still Lomax positive for
  upward loading), but `fy_n` is in the −y direction. Results are typically
  reported for the right wing only (y ≥ 0) and mirrored as required.

---

## Standard symbol tables

### Atmospheric state

| Quantity | Variable | SI unit | Notes |
|---|---|---|---|
| Pressure altitude | `h_m` | m | Geopotential; convert from `_ft` at input |
| Static pressure | `p_static_pa` | Pa | |
| Sea-level reference pressure | `p_0_pa` | Pa | 101 325 Pa |
| Air density | `rho_kg_m3` | kg/m³ | |
| Sea-level reference density | `rho_0_kg_m3` | kg/m³ | 1.225 kg/m³ (US Standard Atmosphere 1976) |
| Density ratio | `rho_ratio` | — | σ = ρ/ρ₀; dimensionless, no suffix |
| Temperature | `t_k` | K | |
| Sea-level reference temperature | `t_0_k` | K | 288.15 K (US Standard Atmosphere 1976) |

### Speed

| Quantity | Variable | SI unit | Notes |
|---|---|---|---|
| True airspeed | `v_tas_m_s` | m/s | |
| Equivalent airspeed | `v_eas_m_s` | m/s | Used for structural load calculations |
| Calibrated airspeed | `v_cas_m_s` | m/s | |
| Mach number | `mach_nd` | — | No unit suffix; dimensionless |
| Local speed of sound | `a_m_s` | m/s | |

### Compressible flow

| Quantity | Variable | SI unit | Notes |
|---|---|---|---|
| Dynamic pressure (compressible) | `q_c_pa` | Pa | Impact pressure; `q_c = p_0[(1+0.2M²)^3.5 − 1]` |
| Dynamic pressure (incompressible) | `q_dyn_pa` | Pa | `q_dyn = 0.5 × rho_kg_m3 × v_tas_m_s²` |
| Ratio of specific heats | `GAMMA` | — | Module constant = 1.4; no suffix |
| Standard gravity | `G_M_S2` | m/s² | Module constant = 9.80665 |

---

## Module-level constants

Physical constants and fixed reference values use `ALL_CAPS` with a unit suffix:

```python
GAMMA        = 1.4             # ratio of specific heats; dimensionless
A_0_M_S      = 340.294         # sea-level speed of sound, m/s
P_0_PA       = 101325.0        # sea-level static pressure, Pa
RHO_0_KG_M3  = 1.225           # sea-level density, kg/m³  (US Standard Atmosphere 1976)
T_0_K        = 288.15          # sea-level temperature, K   (US Standard Atmosphere 1976)
G_M_S2       = 9.80665         # standard gravity, m/s²
```

**Atmospheric model (Decision 19):** the US Standard Atmosphere 1976 is the
authoritative reference for all altitude-dependent atmospheric properties
(density, pressure, temperature, speed of sound). The ATMOS project at
`/Users/seanomeara/Documents/99-Tests/atmos/20_ATMOS` contains candidate
implementation code. Before coding the atmosphere module, review ATMOS to
determine whether to port its routines into `src/atmos.py` or to call ATMOS
as an external dependency. WBT_LOADS is subsonic only; the atmosphere model
is required only from sea level to ~51 000 ft (0–15 545 m).

Tunable solver parameters (`trim_tol`, `flex_max_iter`, etc.) belong in
`config/defaults.json`, not as module-level constants.

---

## Conversion constants (`src/unit_convert.py`)

Pattern: `<FROM>_<TO>` in `ALL_CAPS`.

```python
FT_M       = 0.30480          # feet → metres
M_FT       = 1.0 / FT_M
KTS_M_S    = 0.514444         # knots → m/s
M_S_KTS    = 1.0 / KTS_M_S
FPS_M_S    = 0.30480          # feet/s → m/s
LBF_N      = 4.44822          # pound-force → Newtons
N_LBF      = 1.0 / LBF_N
SLUG_KG    = 14.5939          # slug → kg
KG_SLUG    = 1.0 / SLUG_KG
PSF_PA     = 47.8803          # lbf/ft² → Pa
PA_PSF     = 1.0 / PSF_PA
FT_LBF_NM  = 1.35582          # ft·lbf → N·m
NM_FT_LBF  = 1.0 / FT_LBF_NM
DEG_RAD    = 0.017453         # degrees → radians (π/180)
RAD_DEG    = 1.0 / DEG_RAD
```

---

## Function signatures

Apply the variable name and unit-suffix rules to every parameter:

```python
# correct — SI units, registered names
def solve_trim(v_eas_m_s: float, h_m: float, m_ac_kg: float,
               x_cg_nd: float) -> dict: ...

def compute_section_loads(trim_state: dict, strip_aero: dict,
                          lra: list) -> dict: ...

# incorrect — no unit, ambiguous names
def solve_trim(speed, altitude, weight, cg): ...
```

Return dicts use the registered `code_variable_name` keys.

---

## Flexibility matrix specification (Decision 15)

The flexibility matrix `f_flex` used in `aeroelastic.py` and `beam.py`:

- **Dimensions:** (n_dofs × n_dofs) where `n_dofs = 2 × n_lra_stations` per
  surface (one transverse displacement DOF and one rotation DOF per station).
- **DOF ordering:** interleaved — `[u₁, θ₁, u₂, θ₂, …, uₙ, θₙ]` where `u` is
  transverse displacement (m) and `θ` is rotation (rad).
- **Entry units:** depend on the DOF types of the row and column:

| Row DOF | Column DOF | Entry units | Physical meaning |
|---|---|---|---|
| displacement `u` | force | m/N | transverse deflection per unit force |
| rotation `θ` | moment | rad/(N·m) | rotation per unit moment |
| displacement `u` | moment | m/(N·m) | displacement per unit moment |
| rotation `θ` | force | rad/N | rotation per unit force |

The matrix is symmetric: `F_flex[i,j] == F_flex[j,i]` (Maxwell reciprocity).

Computed by `beam.py` as the modal truncated flexibility: `F_flex = Φ Λ⁻¹ Φᵀ`
where `Λ = diag(ω²)` contains modal stiffnesses (rad²/s²) and `Φ` is the
mass-normalised mode shape matrix (mass units absorbed into normalisation so
the product has units m²/N or rad²/(N·m) at diagonal terms, consistent with
the table above).

All values in SI throughout computation. No unit conversion is applied to
`f_flex` after it is built by `beam.py`.

---

## Legacy notes

The file `doc/variable_definition.md` previously described `atmos.py`-specific
variables with US customary primary units (`_ft`, `_psf`, `_degR`, `_kts`).
That convention is superseded by CLAUDE.md (SI internal standard) and this
document. Any legacy names (`pho_ratio`, `h_press_ft`, `p_static_psf`, etc.)
must be replaced with the SI names above when the relevant function is
substantively rewritten.
