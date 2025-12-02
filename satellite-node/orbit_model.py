import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class CircularOrbit:
    period_s: float = 5400.0  # orbital period in seconds (~90 min)
    inclination_deg: float = 55.0
    altitude_km: float = 600.0

    def position(self, t: float) -> Tuple[float, float, float]:
        """
        Return (lat, lon, alt_km) for a given epoch time t (seconds).

        This is a deliberately simplified model. We assume:
        - circular orbit
        - Earth as a sphere
        - argument of latitude grows linearly with time
        """
        inc_rad = math.radians(self.inclination_deg)
        phase = 2.0 * math.pi * ((t % self.period_s) / self.period_s)

        # latitude oscillates between -inclination and +inclination
        lat_rad = math.asin(math.sin(inc_rad) * math.sin(phase))
        # longitude increases with phase, wrapped into [-pi, pi]
        lon_rad = (phase - math.pi)  # arbitrary reference

        lat_deg = math.degrees(lat_rad)
        lon_deg = math.degrees(lon_rad)

        # normalize longitude to [-180, 180]
        if lon_deg > 180.0:
            lon_deg -= 360.0
        if lon_deg < -180.0:
            lon_deg += 360.0

        return lat_deg, lon_deg, self.altitude_km


def great_circle_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine distance between two points on Earth in km.
    """
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def in_contact(
    lat_sat: float,
    lon_sat: float,
    gs_lat: float,
    gs_lon: float,
    max_distance_km: float = 20000.0,
) -> bool:
    """
    Return True if the satellite is within line-of-sight radius of the ground station.

    max_distance_km is a very rough parameter and does not model real link budgets.
    """
    d = great_circle_distance_km(lat_sat, lon_sat, gs_lat, gs_lon)
    print(f"[orbit_model] distance to GS: {d:.1f} km")
    return d <= max_distance_km