"""HTTP-ish route table wiring handlers to the service layer."""
from services import latest_readings, tank_summary, record_reading
from models import Tank


def build_routes(cfg):
    tanks = [Tank(name) for name in cfg["tank_names"]]

    def get_readings():
        return latest_readings(tanks)

    def get_summary():
        return [tank_summary(t) for t in tanks]

    def post_reading(tank_name, temp_c, ph):
        return record_reading(tank_name, temp_c, ph)

    return {
        "/api/readings": get_readings,
        "/api/summary": get_summary,
        "/api/reading": post_reading,
    }
