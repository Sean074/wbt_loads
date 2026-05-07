"""
Generate sample aerodynamic strip-load database for a BAe 146-sized aircraft.

Coefficients are synthetic, derived from 2-D strip theory with Prandtl-Glauert
compressibility correction. They are geometrically consistent with the four LRA
files in data/lra/ and physically representative of a Mach 0.72 regional jet.

Run from the project root:
    python data/aero/generate_sample_aero.py

Outputs (all in data/aero/):
    aero_wing_power_on_flaps_0.csv
    aero_htail_power_on_flaps_0.csv
    aero_vtail_power_on_flaps_0.csv
    aero_fuselage_power_on_flaps_0.csv
    aero_incr_htail_elevator.csv
"""

import itertools
import math
import pathlib

import numpy as np
import pandas as pd

OUT_DIR = pathlib.Path(__file__).parent


# ---------------------------------------------------------------------------
# Parameter grid
# ---------------------------------------------------------------------------

ALPHA_DEG = np.array([-6.0, -3.0, 0.0, 3.0, 6.0, 9.0, 12.0, 15.0])
BETA_DEG  = np.array([-10.0, -5.0, 0.0, 5.0, 10.0])
MACH_ND   = np.array([0.30, 0.50, 0.65, 0.72, 0.80])
DEFL_DEG  = np.array([-20.0, -10.0, 0.0, 10.0, 20.0])  # elevator only


def prandtl_glauert(mach):
    return 1.0 / np.sqrt(np.maximum(1.0 - mach ** 2, 1e-6))


# ---------------------------------------------------------------------------
# Surface geometry
# ---------------------------------------------------------------------------

def wing_stations():
    """Return (y_m, c_m) arrays for all 19 wing stations."""
    y_half = np.array([0.000, 1.463, 2.927, 4.390, 5.853,
                       7.317, 8.780, 10.243, 11.707, 13.170])
    c_half = 4.0 - 2.5 * y_half / 13.170
    # Full span: port (negative y) + starboard (positive y), root once
    y_all = np.concatenate([-y_half[1:][::-1], y_half])
    c_all = np.concatenate([ c_half[1:][::-1], c_half])
    return y_all, c_all


def htail_stations():
    """Return (y_m, c_m) arrays for all 11 horizontal tail stations."""
    y_half = np.array([0.000, 1.090, 2.180, 3.270, 4.360, 5.450])
    c_half = 2.5 - 1.3 * y_half / 5.45
    y_all = np.concatenate([-y_half[1:][::-1], y_half])
    c_all = np.concatenate([ c_half[1:][::-1], c_half])
    return y_all, c_all


def vtail_stations():
    """Return (y_m, c_m) arrays for 6 vtail stations (y = local span from root)."""
    y_local = np.array([0.000, 0.980, 1.960, 2.940, 3.920, 4.900])
    c_local = 3.0 - 1.5 * y_local / 4.90
    return y_local, c_local


def fuselage_stations():
    """Return (y_m, c_m) arrays for 11 fuselage stations (y = structural x)."""
    y_fus = np.array([2.0, 4.5, 7.0, 9.5, 12.0, 14.5, 17.0, 19.5, 22.0, 24.5, 27.0])
    c_fus = np.full_like(y_fus, 3.50)
    return y_fus, c_fus


# ---------------------------------------------------------------------------
# Coefficient models
# ---------------------------------------------------------------------------

def tip_efficiency(y_abs, half_span, loss_at_tip=0.15):
    return 1.0 - loss_at_tip * y_abs / half_span


def build_wing(y_all, c_all):
    rows = []
    cn_alpha = 0.100   # per degree
    alpha_0  = -2.0    # deg
    for y_m, c_m in zip(y_all, c_all):
        eta = tip_efficiency(abs(y_m), 13.170)
        for alpha_deg, beta_deg, mach_nd in itertools.product(ALPHA_DEG, BETA_DEG, MACH_ND):
            pg  = prandtl_glauert(mach_nd)
            cn  = cn_alpha * (alpha_deg - alpha_0) * pg * eta
            cm  = -0.050 - 0.003 * alpha_deg * pg
            cc  = cn * math.sin(math.radians(alpha_deg)) - 0.008
            rows.append({
                "y_m": round(y_m, 6),
                "c_m": round(c_m, 6),
                "alpha_deg": alpha_deg,
                "beta_deg":  beta_deg,
                "mach_nd":   mach_nd,
                "cn_sec_nd": round(cn, 6),
                "cm_sec_nd": round(cm, 6),
                "cc_sec_nd": round(cc, 6),
            })
    return pd.DataFrame(rows)


def build_htail(y_all, c_all):
    rows = []
    cn_alpha = 0.095
    alpha_0  = 0.0
    for y_m, c_m in zip(y_all, c_all):
        eta = tip_efficiency(abs(y_m), 5.45)
        for alpha_deg, beta_deg, mach_nd in itertools.product(ALPHA_DEG, BETA_DEG, MACH_ND):
            pg  = prandtl_glauert(mach_nd)
            cn  = cn_alpha * (alpha_deg - alpha_0) * pg * eta
            cm  = -0.004 * alpha_deg * pg
            cc  = cn * math.sin(math.radians(alpha_deg)) - 0.006
            rows.append({
                "y_m": round(y_m, 6),
                "c_m": round(c_m, 6),
                "alpha_deg": alpha_deg,
                "beta_deg":  beta_deg,
                "mach_nd":   mach_nd,
                "cn_sec_nd": round(cn, 6),
                "cm_sec_nd": round(cm, 6),
                "cc_sec_nd": round(cc, 6),
            })
    return pd.DataFrame(rows)


def build_vtail(y_all, c_all):
    rows = []
    cn_beta = -0.090   # vtail cn sign: β>0 → starboard inflow → cn negative (port-side reaction)
    for y_m, c_m in zip(y_all, c_all):
        eta = tip_efficiency(y_m, 4.90)
        for alpha_deg, beta_deg, mach_nd in itertools.product(ALPHA_DEG, BETA_DEG, MACH_ND):
            pg  = prandtl_glauert(mach_nd)
            cn  = cn_beta * beta_deg * pg * eta
            cm  = 0.0
            beta_rad = math.radians(beta_deg)
            cc  = abs(cn) * math.sin(abs(beta_rad)) - 0.006
            rows.append({
                "y_m": round(y_m, 6),
                "c_m": round(c_m, 6),
                "alpha_deg": alpha_deg,
                "beta_deg":  beta_deg,
                "mach_nd":   mach_nd,
                "cn_sec_nd": round(cn, 6),
                "cm_sec_nd": round(cm, 6),
                "cc_sec_nd": round(cc, 6),
            })
    return pd.DataFrame(rows)


def build_fuselage(y_all, c_all):
    rows = []
    cn_alpha = 0.015   # body lift curve slope per degree
    for y_m, c_m in zip(y_all, c_all):
        for alpha_deg, beta_deg, mach_nd in itertools.product(ALPHA_DEG, BETA_DEG, MACH_ND):
            cn  = cn_alpha * alpha_deg
            cm  = -0.005
            cc  = 0.0
            rows.append({
                "y_m": round(y_m, 6),
                "c_m": round(c_m, 6),
                "alpha_deg": alpha_deg,
                "beta_deg":  beta_deg,
                "mach_nd":   mach_nd,
                "cn_sec_nd": round(cn, 6),
                "cm_sec_nd": round(cm, 6),
                "cc_sec_nd": round(cc, 6),
            })
    return pd.DataFrame(rows)


def build_elevator_increment(y_all, c_all):
    rows = []
    dcn_per_deg = 0.040    # elevator Cn effectiveness per degree
    dcm_per_deg = -0.015   # trailing-edge down → nose-down Cm
    for y_m, c_m in zip(y_all, c_all):
        eta = tip_efficiency(abs(y_m), 5.45)
        for alpha_deg, beta_deg, mach_nd, defl_deg in itertools.product(
                ALPHA_DEG, BETA_DEG, MACH_ND, DEFL_DEG):
            pg  = prandtl_glauert(mach_nd)
            dcn = dcn_per_deg * defl_deg * pg * eta
            dcm = dcm_per_deg * defl_deg * pg
            alpha_rad = math.radians(alpha_deg)
            dcc = dcn * math.sin(alpha_rad) * 0.5
            rows.append({
                "y_m":            round(y_m, 6),
                "alpha_deg":      alpha_deg,
                "beta_deg":       beta_deg,
                "mach_nd":        mach_nd,
                "deflection_deg": defl_deg,
                "delta_cn_sec_nd": round(dcn, 6),
                "delta_cm_sec_nd": round(dcm, 6),
                "delta_cc_sec_nd": round(dcc, 6),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Generating sample aerodynamic database …")

    y_wing, c_wing = wing_stations()
    df = build_wing(y_wing, c_wing)
    path = OUT_DIR / "aero_wing_power_on_flaps_0.csv"
    df.to_csv(path, index=False)
    print(f"  {path.name}  ({len(df)} rows)")

    y_htail, c_htail = htail_stations()
    df = build_htail(y_htail, c_htail)
    path = OUT_DIR / "aero_htail_power_on_flaps_0.csv"
    df.to_csv(path, index=False)
    print(f"  {path.name}  ({len(df)} rows)")

    y_vtail, c_vtail = vtail_stations()
    df = build_vtail(y_vtail, c_vtail)
    path = OUT_DIR / "aero_vtail_power_on_flaps_0.csv"
    df.to_csv(path, index=False)
    print(f"  {path.name}  ({len(df)} rows)")

    y_fus, c_fus = fuselage_stations()
    df = build_fuselage(y_fus, c_fus)
    path = OUT_DIR / "aero_fuselage_power_on_flaps_0.csv"
    df.to_csv(path, index=False)
    print(f"  {path.name}  ({len(df)} rows)")

    df = build_elevator_increment(y_htail, c_htail)
    path = OUT_DIR / "aero_incr_htail_elevator.csv"
    df.to_csv(path, index=False)
    print(f"  {path.name}  ({len(df)} rows)")

    print("Done.")


if __name__ == "__main__":
    main()
