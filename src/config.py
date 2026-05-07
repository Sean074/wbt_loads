import json
from pathlib import Path

_DEFAULTS = {
    "trim_tol": 1e-6,
    "trim_max_iter": 100,
    "flex_tol": 1e-4,
    "flex_max_iter": 50,
    "data_root": "data",
    "display_units": "si",
    "output_dir": "data/outputs",
    "gust_velocity_above_20kft": 15.24,
    "sigma_w_m_s": 1.0,
    "k_sigma_nd": 3.0,
}

def _load() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "defaults.json"
    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
        merged = dict(_DEFAULTS)
        merged.update(data)
        return merged
    return dict(_DEFAULTS)

APP_CONFIG: dict = _load()
