# CLAUDE.md — WBT Loads

## Project overview

WBT Loads is a Python-based aircraft **Wing Body Tail structural loads** program.
It calculates distributed aerodynamic and inertia loads for structural sizing of
fixed-wing aircraft per FAA/EASA regulations (FAR/CS 23 and FAR/CS 25).

**Inputs:** aerodynamic database, elastic/beam model, distributed mass model
(NASTRAN CONM2 format), loads reference axis, condition list.

**Outputs:** distributed loads, trim balance checks, aeroelastic effectiveness,
jig shape determination from cruise condition.

**Regulatory basis:** CFR 14 FAR Part 25 Subpart C, CFR 14 FAR Part 23 Subpart C.

---

## Unit system

**SI is the internal standard for this project.** All computation module variables,
function parameters, return values, and stored data use SI units without exception.

| Dimension | SI unit | Suffix |
|---|---|---|
| Length | metre | `_m` |
| Area | square metre | `_m2` |
| Mass | kilogram | `_kg` |
| Force | Newton | `_N` |
| Moment / torque | Newton-metre | `_Nm` |
| Pressure | Pascal | `_Pa` |
| Speed | metre per second | `_m_s` |
| Angular rate | radian per second | `_rad_s` |
| Angle (user boundary) | degree | `_deg` |
| Angle (internal solver) | radian | `_rad` |
| Dimensionless | — | _(no suffix)_ |

**Imperial input files and empirical equations:**

- Input files that arrive in imperial units (NASTRAN CONM2 in feet/slugs, aero
  databases in feet, FAR gust tables in fps/knots) are converted to SI
  **immediately at ingestion**, before any internal variable is assigned.
- FAR/CS regulatory equations stated in imperial units are evaluated with
  quantities converted to the required imperial units *within the equation scope
  only*; the result is converted back to SI before assignment.
- `src/unit_convert.py` provides all named conversion constants.
  Bare numeric literals used as conversion factors inside analysis functions
  are a defect.

**User interface boundaries:**

Prompts accept SI units by default. Traditional aviation units (knots for
airspeed, feet for altitude) may be offered as an alternative via the
`ask_unit` helper, provided the result is converted to SI before being passed
to any computation module.

**Variable naming authority:**

`doc/aerospace_variables_reference.csv` is the authoritative source for Python
variable names. The `code_variable_name` column defines the required identifier
for every quantity listed. For project-specific quantities not in the CSV, follow
the same convention: all-lowercase, underscore-separated, SI unit suffix. See
`doc/analysis_code.md` for the complete symbol tables.

---

## Technology stack

| Concern | Library |
|---|---|
| TUI display | `rich` |
| TUI input | `prompt_toolkit` |
| Numerics / linear algebra | `numpy`, `scipy` |
| Data handling | `pandas` |
| Charting | `matplotlib`, `plotly` |
| Config files | stdlib `json`, `pathlib` |

Python version: 3.9+. No framework magic — explicit function calls only.

---

## Authoritative project documentation

The `doc/` directory contains the authoritative standards for this project.
**These documents must be read and followed for any work in this codebase.**

| Document | Covers |
|---|---|
| [`doc/architecture.md`](doc/architecture.md) | Design principles, layer diagram, directory structure, module responsibilities, dependency rules, data flow, adding new features, what does not belong in the source tree |
| [`doc/analysis_code.md`](doc/analysis_code.md) | Variable naming conventions, unit suffix reference, standard symbol tables, module-level constants, conversion constants, function signatures, analysis method notes per module |
| [`doc/loads_aero_db.md`](doc/loads_aero_db.md) | Aerodynamic database file format, column schema, interpolation method, Mach extrapolation policy — authoritative reference for `aero_db.py` |
| [`doc/ui.md`](doc/ui.md) | TUI aesthetic, library roles, workflow pattern (input → analysis → output), colour palette, panel/table/prompt/navigation conventions, module structure, cross-platform notes |

---

## Mandatory documentation maintenance

**For every change to source code or project documentation**, Claude Code MUST:

1. **Identify** which `doc/` files are affected by the change (architecture,
   analysis code conventions, TUI standards, or a combination).
2. **Read** those files before writing any code.
3. **Edit and revise** every affected `doc/` file so it accurately reflects the
   updated state of the codebase — do not leave documentation stale.
4. **Never** leave a `doc/` file inconsistent with the implemented code.

If a new module, capability, or convention is introduced that is not yet covered
by any `doc/` file, add coverage to the appropriate file as part of the same
change.

---

## Regulatory context

Load conditions are developed per:

- **FAR/CS 25 Subpart C** — transport category (symmetric/asymmetric maneuvers,
  gust, ground loads)
- **FAR/CS 23 Subpart C** — normal/utility/acrobatic category

Key load cases to support: symmetric pull-up, push-over, rolling pull-out, yaw
maneuver, discrete and continuous gust (1-cosine and power spectral). The
condition list input file specifies which cases are active.
