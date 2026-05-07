"""
mass_model.py — NASTRAN CONM2 mass model parser.

Parses NASTRAN bulk data files containing GRID and CONM2 cards. Converts
positions (feet → metres) and masses (slugs → kilograms) at ingestion when
input_units='imperial' (default). Only CID=0 (basic global frame) is
supported for CONM2 cards.

Output: total mass, CG position, inertia tensor about the aircraft CG,
and per-point mass/position arrays for downstream load computation.
"""

from pathlib import Path

import numpy as np

from .unit_convert import FT_M, SLUG_KG

G_M_S2 = 9.80665  # m/s²


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_mass_model(
    filepath: Path,
    input_units: str = "imperial",
) -> dict:
    """
    Parse a NASTRAN bulk data file containing GRID and CONM2 cards.

    Parameters
    ----------
    filepath     : Path to the .bdf or .dat file
    input_units  : "imperial" (feet/slugs, default) or "si" (metres/kg)

    Returns
    -------
    dict with keys:
        'n_masses'     : int
        'm_total_kg'   : float — total mass [kg]
        'w_total_n'    : float — total weight (m_total × g) [N]
        'x_cg_m'       : float — CG x-coord, structural frame [m]
        'y_cg_m'       : float — CG y-coord [m]
        'z_cg_m'       : float — CG z-coord [m]
        'i_xx_kg_m2'   : float — roll inertia about CG [kg·m²]
        'i_yy_kg_m2'   : float — pitch inertia about CG [kg·m²]
        'i_zz_kg_m2'   : float — yaw inertia about CG [kg·m²]
        'i_xy_kg_m2'   : float — product of inertia Ixy [kg·m²]
        'i_xz_kg_m2'   : float — product of inertia Ixz [kg·m²]
        'i_yz_kg_m2'   : float — product of inertia Iyz [kg·m²]
        'mass_kg'      : ndarray (N,) — per-point mass [kg]
        'pos_m'        : ndarray (N,3) — per-point position [x,y,z] [m]

    Raises
    ------
    FileNotFoundError, ValueError
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Mass model not found: {filepath}")

    with filepath.open() as fh:
        lines = fh.readlines()

    grids, mass_cards = _parse_bulk(lines, input_units)

    if not mass_cards:
        raise ValueError(f"No CONM2 cards found in {filepath.name}")

    n = len(mass_cards)
    mass_kg = np.zeros(n)
    pos_m   = np.zeros((n, 3))
    i_local = np.zeros((n, 3, 3))

    inertia_factor = (SLUG_KG * FT_M**2) if input_units == "imperial" else 1.0

    for k, card in enumerate(mass_cards):
        grid_pos = np.array(grids.get(card["g"], [0.0, 0.0, 0.0]))
        offset   = np.array(card["xoff"])
        pos_m[k]   = grid_pos + offset
        mass_kg[k] = card["mass"]
        i_local[k] = np.array([
            [card["i11"], card["i21"], card["i31"]],
            [card["i21"], card["i22"], card["i32"]],
            [card["i31"], card["i32"], card["i33"]],
        ]) * inertia_factor

    _validate(mass_kg, pos_m)

    m_total = float(np.sum(mass_kg))
    cg = np.average(pos_m, axis=0, weights=mass_kg)

    ixx = iyy = izz = ixy = ixz = iyz = 0.0
    for k in range(n):
        r = pos_m[k] - cg
        m = mass_kg[k]
        ixx += i_local[k, 0, 0] + m * (r[1]**2 + r[2]**2)
        iyy += i_local[k, 1, 1] + m * (r[0]**2 + r[2]**2)
        izz += i_local[k, 2, 2] + m * (r[0]**2 + r[1]**2)
        ixy += i_local[k, 0, 1] - m * r[0] * r[1]
        ixz += i_local[k, 0, 2] - m * r[0] * r[2]
        iyz += i_local[k, 1, 2] - m * r[1] * r[2]

    return {
        "n_masses":   n,
        "m_total_kg": m_total,
        "w_total_n":  m_total * G_M_S2,
        "x_cg_m":     float(cg[0]),
        "y_cg_m":     float(cg[1]),
        "z_cg_m":     float(cg[2]),
        "i_xx_kg_m2": ixx,
        "i_yy_kg_m2": iyy,
        "i_zz_kg_m2": izz,
        "i_xy_kg_m2": ixy,
        "i_xz_kg_m2": ixz,
        "i_yz_kg_m2": iyz,
        "mass_kg":    mass_kg,
        "pos_m":      pos_m,
    }


def compute_inertia_summary(mass_model: dict) -> dict:
    """
    Re-derive CG and inertia tensor from the per-point arrays in mass_model.

    Returns a dict with the same summary keys as load_mass_model(). Used to
    cross-check that the parsed totals are self-consistent.
    """
    mass_kg = mass_model["mass_kg"]
    pos_m   = mass_model["pos_m"]
    m_total = float(np.sum(mass_kg))
    if m_total <= 0:
        raise ValueError("Total mass is zero or negative")
    cg = np.average(pos_m, axis=0, weights=mass_kg)
    ixx = iyy = izz = ixy = ixz = iyz = 0.0
    for k in range(len(mass_kg)):
        r = pos_m[k] - cg
        m = mass_kg[k]
        ixx += m * (r[1]**2 + r[2]**2)
        iyy += m * (r[0]**2 + r[2]**2)
        izz += m * (r[0]**2 + r[1]**2)
        ixy -= m * r[0] * r[1]
        ixz -= m * r[0] * r[2]
        iyz -= m * r[1] * r[2]
    return {
        "n_masses":   len(mass_kg),
        "m_total_kg": m_total,
        "w_total_n":  m_total * G_M_S2,
        "x_cg_m":     float(cg[0]),
        "y_cg_m":     float(cg[1]),
        "z_cg_m":     float(cg[2]),
        "i_xx_kg_m2": ixx,
        "i_yy_kg_m2": iyy,
        "i_zz_kg_m2": izz,
        "i_xy_kg_m2": ixy,
        "i_xz_kg_m2": ixz,
        "i_yz_kg_m2": iyz,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_bulk(lines: list, input_units: str) -> tuple:
    """
    Scan all lines for GRID and CONM2 small-field and free-field cards.

    Returns (grids dict, mass_cards list).
    grids: {node_id (int): [x_m, y_m, z_m]}
    mass_cards: list of dicts with keys: g, mass, xoff, i11..i33.
    """
    pos_factor  = FT_M   if input_units == "imperial" else 1.0
    mass_factor = SLUG_KG if input_units == "imperial" else 1.0

    grids = {}
    mass_cards = []

    bulk_lines = _extract_bulk_lines(lines)

    i = 0
    while i < len(bulk_lines):
        line = bulk_lines[i]
        raw = line.strip()
        if not raw or raw.startswith("$"):
            i += 1
            continue

        card_name = _card_name(line)

        if card_name == "GRID":
            fields = _split_fields(line)
            gid = _int_field(fields, 1)
            x1  = _float_field(fields, 3) * pos_factor
            x2  = _float_field(fields, 4) * pos_factor
            x3  = _float_field(fields, 5) * pos_factor
            grids[gid] = [x1, x2, x3]

        elif card_name == "CONM2":
            fields = _split_fields(line)
            eid = _int_field(fields, 1)
            g   = _int_field(fields, 2)
            cid_str = fields[3].strip() if len(fields) > 3 else ""
            cid = int(cid_str) if cid_str else 0
            if cid != 0:
                raise ValueError(
                    f"CONM2 EID={eid}: CID={cid} is not supported. "
                    f"Only CID=0 (basic global frame) is accepted."
                )
            mass = _float_field(fields, 4) * mass_factor
            xoff = [
                _float_field(fields, 5) * pos_factor,
                _float_field(fields, 6) * pos_factor,
                _float_field(fields, 7) * pos_factor,
            ]

            i11 = i21 = i22 = i31 = i32 = i33 = 0.0
            if i + 1 < len(bulk_lines):
                nxt = bulk_lines[i + 1]
                if _is_continuation(nxt):
                    nf = _split_fields(nxt)
                    i11 = _float_field(nf, 1)
                    i21 = _float_field(nf, 2)
                    i22 = _float_field(nf, 3)
                    i31 = _float_field(nf, 4)
                    i32 = _float_field(nf, 5)
                    i33 = _float_field(nf, 6)
                    i += 1

            mass_cards.append({
                "g":    g,
                "mass": mass,
                "xoff": xoff,
                "i11": i11, "i21": i21, "i22": i22,
                "i31": i31, "i32": i32, "i33": i33,
            })

        i += 1

    return grids, mass_cards


def _extract_bulk_lines(lines: list) -> list:
    """
    Return lines that are inside the NASTRAN bulk data section.
    If no BEGIN BULK / ENDDATA markers are found, treat all lines as bulk.
    """
    in_bulk = False
    bulk = []
    for line in lines:
        upper = line.strip().upper()
        if not in_bulk:
            if upper.startswith("BEGIN BULK"):
                in_bulk = True
            else:
                # Also accumulate lines that look like data cards even without BEGIN BULK
                stripped = line.strip()
                if stripped and not stripped.startswith("$") and not upper.startswith("NASTRAN"):
                    bulk.append(line.rstrip("\n"))
            continue
        if upper.startswith("ENDDATA"):
            break
        bulk.append(line.rstrip("\n"))

    if in_bulk:
        return bulk

    # No BEGIN BULK found — re-scan all lines treating as bulk
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("$"):
            result.append(line.rstrip("\n"))
    return result


def _card_name(line: str) -> str:
    """Return the uppercase card keyword stripped of large-field markers."""
    if "," in line:
        return line.split(",")[0].strip().upper().rstrip("*")
    return line[:8].strip().upper().rstrip("*")


def _is_continuation(line: str) -> bool:
    """True if the line is a continuation card (starts with + or space)."""
    stripped = line.strip()
    if not stripped or stripped.startswith("$"):
        return False
    if "," in line:
        return line[0] in (" ", "+")
    return line[0] in (" ", "+")


def _split_fields(line: str) -> list:
    """
    Split a NASTRAN line into fields.

    Free-field (comma-separated) or small-field (8-char fixed columns).
    Returns a list of at least 10 string elements.
    """
    if "," in line:
        parts = line.split(",")
        return [p.strip() for p in parts] + [""] * max(0, 10 - len(parts))
    line = line.ljust(80)
    return [line[k * 8:(k + 1) * 8] for k in range(10)]


def _int_field(fields: list, idx: int) -> int:
    if idx >= len(fields):
        return 0
    s = fields[idx].strip()
    return int(s) if s else 0


def _float_field(fields: list, idx: int) -> float:
    if idx >= len(fields):
        return 0.0
    s = fields[idx].strip()
    if not s:
        return 0.0
    s = s.replace("D", "e").replace("d", "e")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _validate(mass_kg: np.ndarray, pos_m: np.ndarray) -> None:
    if np.sum(mass_kg) <= 0:
        raise ValueError("Total mass is zero or negative")
    if not np.all(np.isfinite(pos_m)):
        raise ValueError("Non-finite position value in mass model")
    if not np.all(np.isfinite(mass_kg)):
        raise ValueError("Non-finite mass value in mass model")
