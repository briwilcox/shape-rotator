"""Data classes shared across the app."""
from db import ensure_schema


class Tank:
    def __init__(self, name):
        self.name = name
        ensure_schema()

    def __repr__(self):
        return f"Tank({self.name!r})"


class Reading:
    def __init__(self, tank_name, temp_c, ph, taken_at=None):
        self.tank_name = tank_name
        self.temp_c = temp_c
        self.ph = ph
        self.taken_at = taken_at

    def is_alert(self, threshold_c):
        return self.temp_c >= threshold_c
