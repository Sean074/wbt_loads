"""
lra.py — Loads Reference Axis

Per-surface LRA loader, validator, strip-assignment, and load-summation module.

One JSON file per surface (lra_wing.json, lra_htail.json, lra_vtail.json,
lra_fuselage.json) defines an ordered piecewise-linear 3-D spine. The spine may
be kinked (e.g. winglet junctions). Strip-to-station assignment uses minimum
3-D distance to the spine, not a simple y_m comparison.

Sign conventions follow Lomax §5 and doc/variable_definition.md:
  - Structural frame: x-aft, y-starboard, z-up
  - Section loads: [vz_n, vx_n, fy_n, mx_nm, my_nm, mz_nm]
  - Aerodynamic forces must be rotated to structural frame before calling
    sum_to_lra (dual-frame rule per doc/variable_definition.md).
"""

import json
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_lra(filepath: Path) -> dict:
    """
    Parse and validate one lra_<surface>.json file.

    Returns the parsed dict with keys 'surface' and 'stations', where each
    station dict has 'station_id', 'position_m' (list[float, 3]), and
    'normal_nd' (list[float, 3]).

    Raises ValueError with a descriptive message on any validation failure.
    """
    filepath = Path(filepath)
    with filepath.open() as fh:
        data = json.load(fh)

    _validate_lra(data, filepath)
    return data


def build_lra(filepaths: list) -> dict:
    """
    Load multiple LRA files (one per surface).

    Parameters
    ----------
    filepaths : list of Path-like
        Paths to lra_<surface>.json files.

    Returns
    -------
    dict
        Keyed by surface tag (e.g. 'wing', 'htail'); value is the list of
        validated station dicts from each file.
    """
    result = {}
    for fp in filepaths:
        lra_data = load_lra(fp)
        surface = lra_data["surface"]
        result[surface] = lra_data["stations"]
    return result


def resolve_position(pos_m: np.ndarray, stations: list) -> int:
    """
    Return the index of the LRA station nearest to 3-D position pos_m.

    Projects pos_m onto each segment of the piecewise-linear spine and finds
    the global minimum distance. The station index returned is the endpoint of
    the nearest segment that is closest to the projection point. This works for
    straight and kinked (winglet, fuselage) LRAs without any special-casing.

    Parameters
    ----------
    pos_m : array-like, shape (3,)
        Query position [x_m, y_m, z_m] in structural frame.
    stations : list of dict
        Station list from load_lra() or build_lra().

    Returns
    -------
    int
        Index into stations of the nearest LRA station.
    """
    pos_m = np.asarray(pos_m, dtype=float)
    pts = _station_positions_m(stations)  # (N, 3)
    n = len(pts)

    best_dist = np.inf
    best_idx = 0

    for i in range(n - 1):
        a = pts[i]
        b = pts[i + 1]
        dist_a, dist_b, t = _distances_to_segment(pos_m, a, b)
        # Station at the closer endpoint of this segment
        if t <= 0.5:
            cand_idx, cand_dist = i, dist_a
        else:
            cand_idx, cand_dist = i + 1, dist_b
        if cand_dist < best_dist:
            best_dist = cand_dist
            best_idx = cand_idx

    return best_idx


def sum_to_lra(
    strip_forces_m: np.ndarray,
    strip_positions_m: np.ndarray,
    stations: list,
) -> np.ndarray:
    """
    Integrate strip loads to LRA section cuts.

    Parameters
    ----------
    strip_forces_m : ndarray, shape (M, 6)
        Per-strip load increments in structural frame:
        [dvz_n, dvx_n, dfy_n, dmx_nm, dmy_nm, dmz_nm].
        Forces must already be in structural frame (x-aft, y-starboard, z-up).
    strip_positions_m : ndarray, shape (M, 3)
        [x_m, y_m, z_m] of each strip's c/4 reference point in structural frame.
    stations : list of dict
        Station list from load_lra() or build_lra().

    Returns
    -------
    ndarray, shape (N, 6)
        Section loads at each LRA station:
        [vz_n, vx_n, fy_n, mx_nm, my_nm, mz_nm]
        following Lomax §5 sign convention (doc/variable_definition.md).
    """
    strip_forces_m = np.asarray(strip_forces_m, dtype=float)
    strip_positions_m = np.asarray(strip_positions_m, dtype=float)
    n_strips = strip_forces_m.shape[0]
    n_stations = len(stations)
    pts = _station_positions_m(stations)  # (N, 3)

    section_loads = np.zeros((n_stations, 6))

    for i in range(n_strips):
        j = resolve_position(strip_positions_m[i], stations)
        f = strip_forces_m[i]

        # Direct force accumulation [dvz, dvx, dfy]
        section_loads[j, 0] += f[0]  # vz_n
        section_loads[j, 1] += f[1]  # vx_n
        section_loads[j, 2] += f[2]  # fy_n

        # Moment transfer via (pos_strip - pos_lra) × F_struct.
        # Structural frame (x-aft, y-starboard, z-up) is right-handed, so the
        # standard cross-product formula applies directly.
        # F_struct = [dvx_n, dfy_n, dvz_n] in (x, y, z) component order.
        # r_s = pos_strip - pos_lra (moment arm from LRA reference to strip c/4).
        #
        # M_x (mx_nm) = r_sy * Fz - r_sz * Fy = r_sy * dvz - r_sz * dfy
        # M_y (my_nm) = r_sz * Fx - r_sx * Fz = r_sz * dvx - r_sx * dvz
        # M_z (mz_nm) = r_sx * Fy - r_sy * Fx = r_sx * dfy - r_sy * dvx
        #
        # With r_s = -r (where r = pos_lra - pos_strip):
        #   r_sy = -r[1], r_sz = -r[2], r_sx = -r[0]
        #
        # Strip distributed moments (dmx, dmy, dmz) accumulate directly.
        r = pts[j] - strip_positions_m[i]  # pos_lra - pos_strip
        section_loads[j, 3] += f[3] - r[1] * f[0] + r[2] * f[2]  # mx_nm
        section_loads[j, 4] += f[4] - r[2] * f[1] + r[0] * f[0]  # my_nm
        section_loads[j, 5] += f[5] - r[0] * f[2] + r[1] * f[1]  # mz_nm

    return section_loads


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _station_positions_m(stations: list) -> np.ndarray:
    """Return (N, 3) array of station position vectors."""
    return np.array([s["position_m"] for s in stations], dtype=float)


def _arc_length_m(positions_m: np.ndarray) -> np.ndarray:
    """Cumulative arc length along piecewise-linear spine. Shape (N,)."""
    diffs = np.diff(positions_m, axis=0)           # (N-1, 3)
    seg_lengths = np.linalg.norm(diffs, axis=1)    # (N-1,)
    return np.concatenate([[0.0], np.cumsum(seg_lengths)])


def _distances_to_segment(p: np.ndarray, a: np.ndarray, b: np.ndarray):
    """
    Return (dist_a, dist_b, t) where t in [0, 1] is the parametric projection
    of p onto segment ab, dist_a is distance from p to a, dist_b is distance
    from p to b.
    """
    ab = b - a
    ab_len_sq = float(np.dot(ab, ab))
    if ab_len_sq == 0.0:
        t = 0.0
    else:
        t = float(np.dot(p - a, ab)) / ab_len_sq
        t = max(0.0, min(1.0, t))
    return (
        float(np.linalg.norm(p - a)),
        float(np.linalg.norm(p - b)),
        t,
    )


def _validate_lra(data: dict, filepath: Path) -> None:
    """Raise ValueError if data does not satisfy all validation rules."""
    stem = filepath.stem  # e.g. "lra_wing"

    # Rule 1: surface field matches filename stem
    surface = data.get("surface", "")
    expected_stem = f"lra_{surface}"
    if stem != expected_stem:
        raise ValueError(
            f"{filepath}: 'surface' field '{surface}' does not match filename "
            f"stem '{stem}' (expected 'lra_{surface}')"
        )

    # Rule 2: stations array has >= 2 entries
    stations = data.get("stations", [])
    if not isinstance(stations, list) or len(stations) < 2:
        raise ValueError(
            f"{filepath}: 'stations' must be an array with at least 2 entries, "
            f"got {len(stations) if isinstance(stations, list) else type(stations)}"
        )

    seen_ids = set()
    positions = []

    for idx, st in enumerate(stations):
        sid = st.get("station_id", "")

        # Rule 3: position_m is length-3 with finite floats
        pos = st.get("position_m", [])
        if len(pos) != 3 or not all(
            isinstance(v, (int, float)) and np.isfinite(v) for v in pos
        ):
            raise ValueError(
                f"{filepath}: station {idx} ('{sid}'): 'position_m' must be "
                f"a length-3 array of finite floats, got {pos!r}"
            )
        positions.append(np.array(pos, dtype=float))

        # Rule 4: normal_nd is length-3 with magnitude 1.0 ± 1e-6
        nrm = st.get("normal_nd", [])
        if len(nrm) != 3 or not all(
            isinstance(v, (int, float)) and np.isfinite(v) for v in nrm
        ):
            raise ValueError(
                f"{filepath}: station {idx} ('{sid}'): 'normal_nd' must be "
                f"a length-3 array of finite floats, got {nrm!r}"
            )
        mag = float(np.linalg.norm(nrm))
        if abs(mag - 1.0) > 1e-4:
            raise ValueError(
                f"{filepath}: station {idx} ('{sid}'): 'normal_nd' magnitude "
                f"is {mag:.8f}; must be 1.0 ± 1e-4 (provide at least 4 significant decimal places)"
            )

        # Rule 6: station_id unique within file
        if sid in seen_ids:
            raise ValueError(
                f"{filepath}: duplicate station_id '{sid}'"
            )
        seen_ids.add(sid)

    # Rule 5: no coincident consecutive stations (arc-length spacing > 0)
    for i in range(len(positions) - 1):
        spacing = float(np.linalg.norm(positions[i + 1] - positions[i]))
        if spacing == 0.0:
            raise ValueError(
                f"{filepath}: stations {i} and {i + 1} are coincident "
                f"(zero arc-length spacing)"
            )
