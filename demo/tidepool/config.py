"""Configuration: the deepest module. Everything leans on it."""
import json
import os

DEFAULTS = {
    "port": 8420,
    "db_path": "tidepool.db",
    "tank_names": ["reef-1", "reef-2", "kelp-forest"],
    "alert_temp_c": 28.5,
}


def load_config(path="tidepool.json"):
    cfg = dict(DEFAULTS)
    if os.path.exists(path):
        with open(path) as f:
            cfg.update(json.load(f))
    return cfg
