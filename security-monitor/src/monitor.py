import os
import sqlite3
import time
import json
from typing import List, Tuple

DB_PATH = os.getenv("TELEMETRY_DB", "/data/telemetry.db")


def fetch_telemetry() -> List[Tuple]:
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT timestamp, satellite_id, altitude_km, battery_soc, temperature_c "
            "FROM telemetry ORDER BY id ASC"
        )
        return cur.fetchall()
    finally:
        conn.close()


def analyse(telemetry_rows: List[Tuple]) -> None:
    if len(telemetry_rows) < 2:
        return

    last = None
    for row in telemetry_rows:
        ts, sat_id, alt, batt, temp = row
        if last is not None:
            _, _, last_alt, last_batt, last_temp = last
            # Very simple anomaly rules
            if abs((batt or 0) - (last_batt or 0)) > 20.0:
                alert = {
                    "type": "ANOMALY_BATTERY_JUMP",
                    "timestamp": ts,
                    "satellite_id": sat_id,
                    "details": {
                        "prev": last_batt,
                        "curr": batt,
                    },
                }
                print(json.dumps(alert))
            if alt is not None and (alt < 100 or alt > 2000):
                alert = {
                    "type": "ANOMALY_ALTITUDE_RANGE",
                        "timestamp": ts,
                        "satellite_id": sat_id,
                        "details": {
                            "altitude_km": alt,
                        },
                }
                print(json.dumps(alert))
            if abs((temp or 0) - (last_temp or 0)) > 15.0:
                alert = {
                    "type": "ANOMALY_TEMPERATURE_JUMP",
                    "timestamp": ts,
                    "satellite_id": sat_id,
                    "details": {
                        "prev": last_temp,
                        "curr": temp,
                    },
                }
                print(json.dumps(alert))
        last = row


def main():
    print("[security-monitor] Starting telemetry anomaly checks.")
    seen_rows = 0
    while True:
        rows = fetch_telemetry()
        if len(rows) > seen_rows:
            new_rows = rows[seen_rows:]
            analyse(new_rows)
            seen_rows = len(rows)
        time.sleep(10)


if __name__ == "__main__":
    main()
