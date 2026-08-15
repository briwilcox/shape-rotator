"""SQLite storage: the core the whole program drains into."""
import sqlite3
from config import load_config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    tank_name TEXT,
    temp_c REAL,
    ph REAL,
    taken_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


def _connect():
    cfg = load_config()
    return sqlite3.connect(cfg["db_path"])


def ensure_schema():
    with _connect() as conn:
        conn.execute(_SCHEMA)


def insert_reading(tank_name, temp_c, ph):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO readings (tank_name, temp_c, ph) VALUES (?, ?, ?)",
            (tank_name, temp_c, ph),
        )


def fetch_readings(tank_name, limit=10):
    with _connect() as conn:
        cur = conn.execute(
            "SELECT tank_name, temp_c, ph, taken_at FROM readings "
            "WHERE tank_name = ? ORDER BY taken_at DESC LIMIT ?",
            (tank_name, limit),
        )
        return cur.fetchall()
