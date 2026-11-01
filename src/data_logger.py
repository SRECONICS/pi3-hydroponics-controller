"""
data_logger.py — SQLite time-series storage for sensor readings and dose events.
"""

from __future__ import annotations
import sqlite3, os, logging
from datetime import datetime
import config

log = logging.getLogger(__name__)

def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    con = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with _connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT    NOT NULL,
            ph          REAL,
            ec_us_cm    REAL,
            water_temp  REAL,
            level_pct   REAL,
            air_temp    REAL,
            air_rh      REAL
        );
        CREATE TABLE IF NOT EXISTS dose_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT    NOT NULL,
            pump        TEXT    NOT NULL,
            duration_s  REAL    NOT NULL,
            trigger     TEXT    DEFAULT 'auto'
        );
        CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(ts);
        """)
    log.info("DB ready at %s", config.DB_PATH)

def log_reading(data: dict):
    ts = datetime.utcnow().isoformat()
    with _connect() as con:
        con.execute(
            "INSERT INTO readings(ts,ph,ec_us_cm,water_temp,level_pct,air_temp,air_rh)"
            " VALUES(?,?,?,?,?,?,?)",
            (ts, data.get("ph"), data.get("ec_us_cm"), data.get("water_temp_c"),
             data.get("level_pct"), data.get("air_temp_c"), data.get("air_rh_pct"))
        )

def log_dose(pump: str, duration_s: float, trigger: str = "auto"):
    ts = datetime.utcnow().isoformat()
    with _connect() as con:
        con.execute(
            "INSERT INTO dose_events(ts,pump,duration_s,trigger) VALUES(?,?,?,?)",
            (ts, pump, duration_s, trigger)
        )

def latest_readings(n: int = 60) -> list[dict]:
    with _connect() as con:
        rows = con.execute(
            "SELECT * FROM readings ORDER BY ts DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]

def recent_doses(n: int = 20) -> list[dict]:
    with _connect() as con:
        rows = con.execute(
            "SELECT * FROM dose_events ORDER BY ts DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]
