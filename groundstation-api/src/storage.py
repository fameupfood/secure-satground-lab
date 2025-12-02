import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Optional, List

DB_PATH = os.getenv("TELEMETRY_DB", "/data/telemetry.db")


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                satellite_id TEXT NOT NULL,
                latitude_deg REAL,
                longitude_deg REAL,
                altitude_km REAL,
                battery_soc REAL,
                temperature_c REAL,
                health TEXT
            )"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                satellite_id TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                command_name TEXT NOT NULL,
                payload TEXT
            )"""
        )
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def insert_telemetry(row: Dict[str, Any]) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO telemetry (
                    timestamp, satellite_id, latitude_deg, longitude_deg,
                    altitude_km, battery_soc, temperature_c, health
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["timestamp"],
                row["satellite_id"],
                row.get("latitude_deg"),
                row.get("longitude_deg"),
                row.get("altitude_km"),
                row.get("battery_soc"),
                row.get("temperature_c"),
                row.get("health"),
            ),
        )
        conn.commit()


def get_latest_telemetry() -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT timestamp, satellite_id, latitude_deg, longitude_deg, altitude_km, "
            "battery_soc, temperature_c, health FROM telemetry ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            return None
        keys = [
            "timestamp",
            "satellite_id",
            "latitude_deg",
            "longitude_deg",
            "altitude_km",
            "battery_soc",
            "temperature_c",
            "health",
        ]
        return dict(zip(keys, row))


def insert_command(row: Dict[str, Any]) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO commands (
                    timestamp, satellite_id, sequence_number, command_name, payload
                ) VALUES (?, ?, ?, ?, ?)""",
            (
                row["timestamp"],
                row["satellite_id"],
                row["sequence_number"],
                row["command_name"],
                row.get("payload"),
            ),
        )
        conn.commit()


def get_last_command_seq(satellite_id: str) -> Optional[int]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT sequence_number FROM commands "
            "WHERE satellite_id = ? ORDER BY id DESC LIMIT 1",
            (satellite_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return int(row[0])
