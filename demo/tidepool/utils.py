"""Small shared helpers."""
from config import DEFAULTS


def celsius_to_f(c):
    if c is None:
        return None
    return round(c * 9 / 5 + 32, 1)


def rolling_mean(values, window=10):
    values = [v for v in values if v is not None]
    if not values:
        return None
    tail = values[-window:]
    return round(sum(tail) / len(tail), 2)


def is_alert_temp(temp_c):
    return temp_c is not None and temp_c >= DEFAULTS["alert_temp_c"]
