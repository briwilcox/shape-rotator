"""Service layer: business logic between routes and storage."""
from models import Reading, Tank
from db import fetch_readings, insert_reading
from utils import celsius_to_f, rolling_mean


def latest_readings(tanks):
    out = {}
    for tank in tanks:
        rows = fetch_readings(tank.name, limit=10)
        out[tank.name] = [Reading(*row) for row in rows]
    return out


def tank_summary(tank):
    rows = fetch_readings(tank.name, limit=100)
    temps = [r[1] for r in rows]
    return {
        "tank": tank.name,
        "mean_temp_c": rolling_mean(temps, window=10),
        "mean_temp_f": celsius_to_f(rolling_mean(temps, window=10)),
        "samples": len(rows),
    }


def record_reading(tank_name, temp_c, ph):
    insert_reading(tank_name, temp_c, ph)
    return {"ok": True, "tank": tank_name}
