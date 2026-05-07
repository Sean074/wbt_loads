import pandas as pd
from pathlib import Path

from .unit_convert import DEG_RAD

_DEG_COLS = {
    "elevator_deg": "delta_e_rad",
    "aileron_deg":  "delta_a_rad",
    "rudder_deg":   "delta_r_rad",
    "flap_deg":     "delta_f_rad",
    "spoiler_deg":  "delta_sp_rad",
    "stabiliser_deg": "delta_stab_rad",
}

REQUIRED_COLUMNS = {
    "A": [
        "condition_id", "description", "maneuver_type",
        "h_m", "v_eas_m_s", "m_ac_kg", "x_cg_nd", "nz_nd", "fos_nd",
    ],
    "B": [
        "condition_id", "description", "maneuver_type",
        "h_m", "v_eas_m_s", "m_ac_kg", "x_cg_nd", "fos_nd",
    ],
    "C": [
        "condition_id", "description", "maneuver_type",
        "nz_nd", "nx_nd", "ny_nd", "fos_nd",
    ],
    "D": [
        "condition_id", "description", "maneuver_type",
        "v_sink_m_s", "d_stroke_m", "eta_gear_nd", "nz_nd", "fos_nd",
    ],
    "E": [
        "condition_id", "description", "maneuver_type",
        "h_m", "v_eas_m_s", "m_ac_kg", "x_cg_nd", "nz_nd", "delta_f_rad", "fos_nd",
    ],
}


def load_conditions(csv_path, analysis_type: str) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Condition file not found: {path}")

    df = pd.read_csv(path, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]

    required = REQUIRED_COLUMNS.get(analysis_type)
    if required is None:
        raise NotImplementedError(f"Analysis type {analysis_type!r} not yet supported")

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for type {analysis_type}: {missing}")

    # Convert degree columns to radians
    for deg_col, rad_col in _DEG_COLS.items():
        if deg_col in df.columns:
            df[rad_col] = df[deg_col] * DEG_RAD

    return df
