"""
loads.py — Strip-to-section-load integration and rigid trim solver.

Converts aerodynamic strip coefficients (cn, cm, cc) and a flight state into
distributed forces/moments in the structural frame, integrates them to LRA
station loads via lra.sum_to_lra(), and computes integrated totals.

Also provides compute_inertia_vmt() for distributing mass model inertia loads
to LRA stations, and solve_rigid_alpha_trim() for the simplified rigid-body
alpha trim used in pre-analysis validation.

All computations are in SI throughout. Structural frame: x-aft, y-starboard,
z-up. Section load sign convention follows Lomax §5 (doc/variable_definition.md):
[vz_n, vx_n, fy_n, mx_nm, my_nm, mz_nm].
"""

import numpy as np

from . import aero_db as _aero_db
from . import lra as _lra
from .unit_convert import DEG_RAD

G_M_S2 = 9.80665  # m/s²


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def strip_coefficients_to_forces(
    cn_sec_nd: np.ndarray,
    cm_sec_nd: np.ndarray,
    cc_sec_nd: np.ndarray,
    c_m: np.ndarray,
    y_m: np.ndarray,
    q_dyn_pa: float,
) -> np.ndarray:
    """
    Convert strip coefficients to per-strip force/moment increments in the
    structural frame (x-aft, y-starboard, z-up).

    Parameters
    ----------
    cn_sec_nd : section normal force coefficient, shape (M,)
    cm_sec_nd : section pitching moment coefficient (LE-up positive), shape (M,)
    cc_sec_nd : section chord force coefficient (drag-direction positive), shape (M,)
    c_m       : local chord at each strip [m], shape (M,)
    y_m       : spanwise position of each strip [m], shape (M,)
    q_dyn_pa  : dynamic pressure [Pa]

    Returns
    -------
    ndarray, shape (M, 6)
        Per-strip increments [dvz_n, dvx_n, dfy_n, dmx_nm, dmy_nm, dmz_nm].
        dvz_n  = +cn × q × c × dy   (normal force → +z_struct, upward)
        dvx_n  = −cc × q × c × dy   (chord force; cc positive = aft in aero →
                                      wait — cc is drag-direction = forward in
                                      aero frame = −x_struct; vx_n positive =
                                      +x_struct = aft; so dvx_n = −cc × q × c × dy)
        dmy_nm = +cm × q × c² × dy  (pitching moment; cm LE-up = my_nm LE-up ✓)
        dfy_n = dmx_nm = dmz_nm = 0  (summed at LRA station via moment transfer)
    """
    cn_sec_nd = np.asarray(cn_sec_nd, dtype=float)
    cm_sec_nd = np.asarray(cm_sec_nd, dtype=float)
    cc_sec_nd = np.asarray(cc_sec_nd, dtype=float)
    c_m       = np.asarray(c_m,       dtype=float)
    y_m       = np.asarray(y_m,       dtype=float)

    dy_m = _strip_widths_m(y_m)

    dvz_n  =  cn_sec_nd * q_dyn_pa * c_m * dy_m
    dvx_n  = -cc_sec_nd * q_dyn_pa * c_m * dy_m
    dfy_n  = np.zeros_like(dvz_n)
    dmx_nm = np.zeros_like(dvz_n)
    dmy_nm =  cm_sec_nd * q_dyn_pa * c_m**2 * dy_m
    dmz_nm = np.zeros_like(dvz_n)

    return np.column_stack([dvz_n, dvx_n, dfy_n, dmx_nm, dmy_nm, dmz_nm])


def compute_aero_vmt(
    cn_sec_nd: np.ndarray,
    cm_sec_nd: np.ndarray,
    cc_sec_nd: np.ndarray,
    c_m: np.ndarray,
    y_m: np.ndarray,
    q_dyn_pa: float,
    stations: list,
) -> np.ndarray:
    """
    Full pipeline: strip coefficients → structural frame forces → LRA station loads.

    Each strip c/4 is placed on the LRA spine at its spanwise position (x and z
    coordinates interpolated linearly from the LRA stations).

    Parameters
    ----------
    cn_sec_nd, cm_sec_nd, cc_sec_nd : shape (M,)
    c_m, y_m                        : shape (M,)
    q_dyn_pa                        : float
    stations                        : list from lra.load_lra()['stations']

    Returns
    -------
    ndarray, shape (N, 6)
        Section load concentrations at each LRA station:
        [vz_n, vx_n, fy_n, mx_nm, my_nm, mz_nm].
    """
    y_m = np.asarray(y_m, dtype=float)
    lra_pts = np.array([s["position_m"] for s in stations], dtype=float)  # (N, 3)
    lra_y   = lra_pts[:, 1]

    # Place each aero strip at its spanwise position on the LRA spine
    strip_x = np.interp(y_m, lra_y, lra_pts[:, 0])
    strip_z = np.interp(y_m, lra_y, lra_pts[:, 2])
    strip_positions_m = np.column_stack([strip_x, y_m, strip_z])  # (M, 3)

    strip_forces = strip_coefficients_to_forces(
        cn_sec_nd, cm_sec_nd, cc_sec_nd, c_m, y_m, q_dyn_pa
    )

    return _lra.sum_to_lra(strip_forces, strip_positions_m, stations)


def compute_integrated_totals(
    cn_sec_nd: np.ndarray,
    cm_sec_nd: np.ndarray,
    cc_sec_nd: np.ndarray,
    c_m: np.ndarray,
    y_m: np.ndarray,
    q_dyn_pa: float,
    alpha_rad: float,
) -> dict:
    """
    Compute integrated lift, drag, and pitching moment from strip data.

    Transforms strip normal/chord forces to stability-axis lift and drag using
    angle of attack. Pitching moment is about c/4 for the full planform.

    Returns
    -------
    dict with keys: 'lift_n', 'drag_n', 'm_pitch_nm'
    """
    cn_sec_nd = np.asarray(cn_sec_nd, dtype=float)
    cm_sec_nd = np.asarray(cm_sec_nd, dtype=float)
    cc_sec_nd = np.asarray(cc_sec_nd, dtype=float)
    c_m       = np.asarray(c_m,       dtype=float)
    y_m       = np.asarray(y_m,       dtype=float)

    dy_m = _strip_widths_m(y_m)
    cos_a = np.cos(alpha_rad)
    sin_a = np.sin(alpha_rad)

    dL = (cn_sec_nd * cos_a - cc_sec_nd * sin_a) * q_dyn_pa * c_m * dy_m
    dD = (cn_sec_nd * sin_a + cc_sec_nd * cos_a) * q_dyn_pa * c_m * dy_m
    dM = cm_sec_nd * q_dyn_pa * c_m**2 * dy_m

    return {
        "lift_n":     float(np.sum(dL)),
        "drag_n":     float(np.sum(dD)),
        "m_pitch_nm": float(np.sum(dM)),
    }


def compute_inertia_vmt(
    mass_model: dict,
    nz_nd: float,
    stations: list,
) -> np.ndarray:
    """
    Compute inertia load concentrations at LRA stations for a given load factor.

    Each mass point contributes a vertical inertia force:
        f_z = −mass_kg × G_M_S2 × nz_nd  (downward = −z_struct)

    Parameters
    ----------
    mass_model : dict from mass_model.load_mass_model()
    nz_nd      : normal load factor (1.0 for 1g)
    stations   : list from lra.load_lra()['stations']

    Returns
    -------
    ndarray, shape (N, 6)
        Inertia load concentrations [vz_n, vx_n, fy_n, mx_nm, my_nm, mz_nm]
        at each LRA station. Moment transfer from mass point to LRA reference
        is performed by lra.sum_to_lra().
    """
    mass_kg = mass_model["mass_kg"]
    pos_m   = mass_model["pos_m"]
    n       = len(mass_kg)

    # Inertia force on structure: downward = −z_struct → dvz_n is negative
    dvz_n = -mass_kg * G_M_S2 * nz_nd

    strip_forces = np.zeros((n, 6))
    strip_forces[:, 0] = dvz_n  # vz_n component only; other components zero

    return _lra.sum_to_lra(strip_forces, pos_m, stations)


def solve_rigid_alpha_trim(
    aero_db_data: dict,
    mach_nd: float,
    cl_required_nd: float,
    s_ref_m2: float,
    alpha_min_deg: float = -10.0,
    alpha_max_deg: float = 25.0,
    tol_nd: float = 1e-4,
    max_iter: int = 50,
) -> dict:
    """
    Find trim angle of attack by bisection to match a required lift coefficient.

    Rigid-body only: does not balance pitching moment (no elevator loop).
    Intended for pre-analysis validation; use trim.py for formal loads cases.

    Parameters
    ----------
    aero_db_data   : dict from aero_db.load_aero_db()
    mach_nd        : Mach number
    cl_required_nd : required whole-aircraft CL (W × nz / (q × S_ref))
    s_ref_m2       : wing reference area [m²]
    alpha_min_deg  : lower bound for bisection [deg]
    alpha_max_deg  : upper bound for bisection [deg]
    tol_nd         : CL convergence tolerance
    max_iter       : maximum bisection iterations

    Returns
    -------
    dict with keys:
        'alpha_deg'    : float — trim angle of attack [deg]
        'alpha_rad'    : float — trim angle of attack [rad]
        'cl_trim_nd'   : float — achieved CL
        'cm_trim_nd'   : float — unbalanced Cm at trim alpha (informational)
        'converged'    : bool
        'residual_cl'  : float — |CL_achieved − CL_required|
    """
    c_m    = aero_db_data["c_m"]
    y_m    = aero_db_data["y_m"]
    dy_m   = _strip_widths_m(y_m)

    def _cl_at_alpha(alpha_deg_val: float) -> tuple:
        alpha_rad_val = alpha_deg_val * DEG_RAD
        cn, cm, _, _ = _aero_db.interpolate_strips(
            aero_db_data, alpha_rad_val, 0.0, mach_nd
        )
        cl = float(np.sum(cn * c_m * dy_m)) / s_ref_m2
        cm_nd = float(np.sum(cm * c_m**2 * dy_m)) / (s_ref_m2 * float(np.mean(c_m)))
        return cl, cm_nd

    cl_lo, _ = _cl_at_alpha(alpha_min_deg)
    cl_hi, _ = _cl_at_alpha(alpha_max_deg)

    converged = True
    a_lo, a_hi = alpha_min_deg, alpha_max_deg

    if not (cl_lo <= cl_required_nd <= cl_hi):
        converged = False
        # Return closest bound
        if abs(cl_lo - cl_required_nd) < abs(cl_hi - cl_required_nd):
            alpha_trim_deg = a_lo
        else:
            alpha_trim_deg = a_hi
    else:
        for _ in range(max_iter):
            alpha_mid = 0.5 * (a_lo + a_hi)
            cl_mid, _ = _cl_at_alpha(alpha_mid)
            if abs(cl_mid - cl_required_nd) < tol_nd:
                a_lo = a_hi = alpha_mid
                break
            if cl_mid < cl_required_nd:
                a_lo = alpha_mid
            else:
                a_hi = alpha_mid
        else:
            converged = False
        alpha_trim_deg = 0.5 * (a_lo + a_hi)

    cl_final, cm_final = _cl_at_alpha(alpha_trim_deg)

    return {
        "alpha_deg":   alpha_trim_deg,
        "alpha_rad":   alpha_trim_deg * DEG_RAD,
        "cl_trim_nd":  cl_final,
        "cm_trim_nd":  cm_final,
        "converged":   converged,
        "residual_cl": abs(cl_final - cl_required_nd),
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _strip_widths_m(y_m: np.ndarray) -> np.ndarray:
    """
    Compute strip widths using central differences for interior stations and
    one-sided differences at the endpoints.
    """
    y_m = np.asarray(y_m, dtype=float)
    n = len(y_m)
    dy = np.empty(n)
    if n == 1:
        dy[0] = 1.0
        return dy
    dy[0]    = y_m[1]    - y_m[0]
    dy[-1]   = y_m[-1]   - y_m[-2]
    dy[1:-1] = 0.5 * (y_m[2:] - y_m[:-2])
    return np.abs(dy)
