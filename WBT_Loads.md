# Overview

This is an external loads program to calculate aircraft Wing Body Tail (WBT) loads
for use in structural sizing. It computes distributed aerodynamic and inertia loads
at section cuts along the Loads Reference Axis (LRA) for every active condition in
the condition list.

Input data:
* Aircraft Loads Reference Axis (LRA) and load reporting grid definition.
* Elastic model — beam stiffness distributions (EI, GJ, EA) or a pre-computed
  aerodynamic influence coefficient / flexibility matrix. Optional; enables
  aeroelastic load redistribution.
* Aerodynamic database — strip load data (Cn, Cm, Cc) from CFD or wind tunnel.
* Distributed aircraft mass — NASTRAN CONM2 format, CID=0 (global frame).
* Condition list — CSV file (externally generated) containing one row per load
  condition. Each row specifies: condition ID, description, category
  (`maneuver` / `gust` / `ground`), maneuver type, pressure altitude, EAS,
  aircraft mass, CG fraction MAC, load factor, and per-surface control surface
  deflections. Physical quantities in SI; deflections in degrees and converted
  to radians at ingestion. Full column schema in `decision.md §1b` and
  `doc/analysis_code.md §Condition list`.

Outputs:
* Distributed section loads at each LRA station: shear (Vz, Vy), bending moment
  (Mx, Mz), torsion (My), axial force (Fx) — limit and ultimate.
* Load envelope — critical condition and load value per station per load component.
* Design load summary — critical case ID, flight condition, and load by station.
* Shear-moment-torque (SMT) diagrams.
* Trim balance verification — residual forces and moments for each condition.
* Aircraft simulation vs. load model checks.
* Aeroelastic effectiveness — flexible vs. rigid control surface effectiveness ratio
  per surface.
* Jig shape determination from the cruise condition.

Load conditions are per FAA/EASA regulations FAR/CS 23 and FAR/CS 25.

Analysis methods follow standard industry best practice as documented below.

---

# Load Case Categories

The condition list must cover the following categories. Each category maps to
the regulation sections listed.

## FAR/CS 25 — Transport Category

### Symmetric flight maneuvers (FAR 25.331, 25.333, 25.337)
* Symmetric pull-up — n_z = n_z_max (up to +2.5 g minimum, typically +2.5 to +3.8 g)
* Push-over — n_z = n_z_min (typically −1.0 g)
* Checked maneuver — transient exceeding steady n_z by pitch rate effect

### Asymmetric flight maneuvers (FAR 25.347, 25.349)
* Rolling pull-out — combined roll rate and symmetric pull-up
* Unsymmetric gust on horizontal tail — 100% symmetric + vertical gust on one
  surface, 80% on the other

### Yaw maneuver (FAR 25.351)
* Rudder input from VMC to VD at altitudes per the flight envelope

### Discrete gust

* **Phase 1 — static equivalent gust (pre-Amendment 25-86):** design gust
  velocity from original FAR Part 25 Appendix G (Lomax §4): 50 fps EAS
  (15.24 m/s) at sea level, 25 fps EAS (7.62 m/s) at 20 000 ft, linearly
  interpolated. No 1-cosine profile; no H sweep. Both positive and negative
  increments evaluated. Regulatory basis: FAR 25 Appendix G, pre-Amendment
  25-86 (1996).
* **Phase 2 (deferred) — 1-cosine TDG:** vertical and lateral gusts per current
  FAR 25.341(a) and AC 25.341-1; 56 ft/s EAS at sea level to 20.86 ft/s EAS at
  60 000 ft; H sweep 30–350 ft.

### Continuous turbulence — power spectral density (FAR 25.341(b), AC 25.341-1)

* **Phase 1 — 2-DOF rigid-body FRF:** self-contained plunge-pitch frequency
  response model with strip-theory aerodynamics; Von Kármán PSD per AC 25.341-1;
  turbulence scale L = 2 500 ft (762 m); RMS loads by numerical integration;
  design limit load = 3.0 × σ_load (limit load factor method).
* **Phase 2 (deferred) — full DLM/NASTRAN FRF:** frequency response functions
  from NASTRAN DLM or ZONA51 on the flexible structure.

### High-lift device conditions (FAR 25.345)
* Flap / slat extended at V_F (design flap speed) at approved configurations
* Vertical gust at V_F; asymmetric flap failure load case

### Engine failure (FAR 25.367)
* Asymmetric thrust yaw transient from one-engine-inoperative at V_MCG

### Control surface loads (FAR 25.391–25.427)
* Elevator, aileron, rudder, and tab loads from limit pilot forces and maximum
  control deflections
* Hinge moment loads used for surface structural sizing

### Ground loads (FAR 25.473–25.511)

* **Phase 1 — quasi-static reserve energy method (FAR 25.473):** peak gear
  reaction from energy conservation using design sink rate and gear stroke; no
  spring-damper model required. Landing sub-cases: level landing, tail-down
  landing, one-gear landing (FAR 25.479–25.483), lateral drift (FAR 25.485),
  rebound (FAR 25.487). Static ground handling: braked roll (FAR 25.493),
  ground turn (FAR 25.495), nose-wheel yaw, towing, pivoting, jacking.
* **Phase 2 (deferred) — dynamic gear model:** spring-damper gear model with
  integrated time history of gear attachment loads and airframe section loads.

## FAR/CS 23 — Normal / Utility / Acrobatic Category

Loads per FAR 23.301–23.511. Maneuver load factors per FAR 23.337.
Gust load factors per FAR 23.341. Ground loads per FAR 23.473–23.511.

---

# Plan Outline

## Aerodynamic Database

Developed from CFD or wind tunnel testing. This project imports the data — raw
aerodynamic data is not generated here.

Data coverage: wing, vertical stabilizer, horizontal stabilizer, fuselage.

Strip load quantities per spanwise station:
* Cn — section normal force coefficient
* Cm — section pitching moment coefficient (reference at 25% local chord)
* Cc — section chord force coefficient

Incremental tables (added to the baseline per active input):
* Control surface deflection increments — total induction on the main surface
  plus the deflected surface itself, tabulated by surface name and deflection
  angle δ (deg)
* Angular rate increments — pitch rate q, roll rate p, yaw rate r

Interpolation variables: α, β, p, q, r, and control deflections δ.

Compressibility corrections applied to strip data before use:
* Prandtl-Glauert correction (M < 0.7): Cn → Cn / sqrt(1 − M²)
* Downwash factor and tail-on-wing interference correction applied at the
  horizontal tail to account for wing wake on tail loads.

Fuselage aerodynamic loads derived from cross-flow drag and slender-body theory
for sideslip and yaw rate conditions.

Note: The Doublet Lattice Method (DLM) is the industry standard for computing
frequency-response functions required for the continuous turbulence (PSD) gust
analysis. If PSD gust is implemented, DLM-derived aerodynamic influence
coefficients should be used for that load path.

## Distributed Mass Model

Mass provided in NASTRAN CONM2 format, CID=0 (global coordinate system only).
Off-diagonal inertia terms are accepted for whole-aircraft inertia; the
distributed mass model uses point masses only.

Mass files using local coordinate systems (CID ≠ 0) are not supported. NASTRAN
RBE2 and CBAR/CBEAM distributed mass entries are outside scope; only CONM2
is parsed.

## Elastic Model (Aeroelastic Corrections)

Optional input. When provided, enables flexible-body load redistribution and
jig shape computation.

Accepted input formats:
* Beam stiffness distribution: spanwise stations y, bending stiffness EI
  (lbf·ft²), torsional stiffness GJ (lbf·ft²), axial stiffness EA (lbf).
* Pre-computed flexibility matrix (aerodynamic influence coefficient matrix,
  AIC): externally generated from a NASTRAN or equivalent FEM solve, supplied
  as a tabular file of deflection per unit load at each LRA station.

When the flexibility matrix is provided externally, aeroelastic.py reads it
directly. When beam stiffness data is provided, the module derives the
flexibility matrix by finite-difference or direct stiffness method before
applying corrections.

Structural bending-torsion coupling (relevant for swept or composite wings) is
accounted for through the off-diagonal terms in the flexibility matrix.

## Loads Reference Axis and Reporting Grid

LRA defined as a series of oriented reference points along the structural span.
Aerodynamic strip loads and inertia loads are both integrated and summed to
these section-cut points.

Standard output stations: wing root, mid-span, tip, and fuselage station cuts.
Additional user-defined stations may be added via the condition/LRA input file.

## Airplane Trim Model

Solves the three-equation longitudinal trim balance (lift = n_z × W, ΣM = 0,
thrust = drag) for each flight condition. Solve variables: α, δ_e, thrust.

For aeroelastic trim (when the elastic model is active), trim and flexibility
corrections are iterated simultaneously until both the equilibrium residuals and
the structural deflection converge.

## Maneuver Time History Model

Time-domain integration of the equations of motion for each dynamic maneuver
using scipy.integrate.solve_ivp. Critical instant extracted by scanning the
time history for maximum and minimum values of each load component.

Supported maneuver types: symmetric pull-up, push-over, rolling pull-out,
yaw maneuver.

---

# Load Factor Application

Per FAR 25.301(b) and FAR 25.303:

* **Limit loads** — the maximum loads expected in service. Defined by n_z,
  gust velocity, or structural limit.
* **Ultimate loads** — limit loads multiplied by a factor of safety of 1.5.

Both limit and ultimate section loads are computed and reported for every
active condition. The load envelope identifies the critical condition for each
load component at each station for both limit and ultimate.

---

# Outputs Detail

| Output | Description |
|---|---|
| Section loads per condition | Vz, Vy, Fx, Mx, My, Mz at each LRA station — limit and ultimate |
| Load envelope | Critical condition ID and load value per station per component |
| Design load summary | Table of critical case, condition, and load by station |
| SMT diagrams | Shear, bending moment, and torsion plotted vs. spanwise station |
| Trim balance check | Lift, drag, moment residuals; confirms balanced condition |
| Simulation vs. model check | Compares whole-aircraft forces/moments to flight simulation or DTA data |
| Aeroelastic effectiveness | Flexible / rigid effectiveness ratio per control surface vs. speed |
| Jig shape | Undeformed geometry required to achieve cruise shape under load |

---

# Code Standard

Code is in Python 3.9+. Standard packages: numpy, scipy, pandas, matplotlib,
plotly. No framework magic — explicit function calls only.

User interface is a TUI (terminal user interface):
* Theme: simple, dark scheme, 1990s engineering-program aesthetic.
* Libraries: rich (display), prompt_toolkit (input).
* Main page follows the workflow: load inputs → run analysis → view outputs.

---

# Scope Boundaries

The following are explicitly outside scope:

* Flutter analysis (requires unsteady aerodynamics and modal FEM — use ZAERO
  or NASTRAN SOL 145).
* Fatigue and damage tolerance (requires cycle counting and crack growth — use
  dedicated DTA programs).
* Ground-vibration test correlation.
* CFD mesh generation or aerodynamic database computation — aero data is an input.
* NASTRAN finite-element model assembly or solve — FEM results are inputs.
* Fuel system slosh loads.
* Pressurized cabin structural loads (hoop stress, pressure vessel sizing).

---

# References

## Regulatory — Airworthiness Standards

* CFR 14 FAR Part 25 Subpart C — Loads (transport category)
* CFR 14 FAR Part 23 Subpart C — Loads (normal/utility/acrobatic category)
* EASA CS-25 Subpart C — equivalent European standard

## FAA Advisory Circulars

* AC 25.341-1 — Dynamic Gust Loads (discrete 1-cosine and PSD continuous
  turbulence implementation guidance)
* AC 25.491-1 — Taxi, Takeoff, and Landing Roll Design Loads (ground load
  methodology and sink rate selection)

## Textbooks

* Ted L. Lomax — *Structural Loads Analysis for Commercial Transport Aircraft:
  Theory and Practice* (AIAA Education Series, 1996). Primary reference for all
  FAR/CS 25 load case implementation.
* J. Wright and J. Cooper — *Introduction to Aircraft Aeroelasticity and Loads*,
  2nd ed. (Wiley/AIAA, 2015). Aeroelastic corrections, gust response, control
  effectiveness.
* B. Etkin and L. D. Reid — *Dynamics of Flight: Stability and Control*, 3rd ed.
  (Wiley, 1996). Equations of motion, stability derivatives, maneuver simulation.

## Technical Reports

* FAR 23 Loads Program — https://apps.dtic.mil/sti/pdfs/ADA324952.pdf
  (DTIC ADA324952). Reference implementation for FAR 23 load cases.
* NACA TN 3030 — Gray & Schenk (1953). *A Method for Calculating the Subsonic
  Steady-State Loading on an Airplane with a Wing of Arbitrary Plan Form and
  Stiffness.* Foundational method for flexibility-corrected spanwise load
  distributions.
* NACA Report 1135 — *Equations, Tables, and Charts for Compressible Flow*
  (1953). Compressibility corrections and standard atmosphere relationships.

## Data and Supplementary Methods

* ESDU Data Items — aerodynamic correction factors, downwash estimation, body
  interference, strip theory extensions (e.g. ESDU 70011, ESDU 76003). Used as
  supplemental engineering data for corrections not covered by CFD/wind tunnel
  input data.
