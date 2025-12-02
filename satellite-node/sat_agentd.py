import json
import os
import time
import hmac
import hashlib
import random
from datetime import datetime, timezone

import requests

from orbit_model import CircularOrbit, in_contact


def compute_hmac(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
    return mac.hexdigest()


def main():
    groundstation_url = os.getenv("GROUNDSTATION_URL", "http://localhost:8000")
    sat_id = os.getenv("SATELLITE_ID", "SAT-001")
    hmac_secret = os.getenv("HMAC_SECRET", "changeme")

    orbit_period = float(os.getenv("ORBIT_PERIOD_S", "5400"))
    inclination = float(os.getenv("ORBIT_INCLINATION_DEG", "55"))
    gs_lat = float(os.getenv("GS_LAT", "50.0"))
    gs_lon = float(os.getenv("GS_LON", "7.5"))

    orbit = CircularOrbit(period_s=orbit_period, inclination_deg=inclination)
    session = requests.Session()

    print(f"[sat_agentd] Starting with GS at lat={gs_lat}, lon={gs_lon}")
    print(f"[sat_agentd] Using HMAC secret length: {len(hmac_secret)}")

    while True:
        now = time.time()
        lat, lon, alt_km = orbit.position(now)

        visible = in_contact(lat, lon, gs_lat, gs_lon)
        if visible:
            # Simple telemetry model
            batt = 80.0 + 5.0 * random.uniform(-1.0, 1.0)
            temp = 10.0 + 2.0 * random.uniform(-1.0, 1.0)
            health = "NOMINAL"

            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "satellite_id": sat_id,
                "latitude_deg": lat,
                "longitude_deg": lon,
                "altitude_km": alt_km,
                "battery_soc": batt,
                "temperature_c": temp,
                "health": health,
            }

            body = json.dumps(payload).encode("utf-8")
            sig = compute_hmac(body, hmac_secret)

            try:
                resp = session.post(
                    f"{groundstation_url}/telemetry",
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Signature": sig,
                    },
                    timeout=5.0,
                )
                if resp.status_code != 200:
                    print(f"[sat_agentd] Warning: groundstation replied {resp.status_code}: {resp.text}")
                else:
                    print(f"[sat_agentd] Telemetry sent. lat={lat:.2f}, lon={lon:.2f}, batt={batt:.1f}")
            except Exception as exc:
                print(f"[sat_agentd] Error sending telemetry: {exc}")

        else:
            print("[sat_agentd] Ground station not in view. Skipping telemetry.")

        time.sleep(5.0)


if __name__ == "__main__":
    main()
