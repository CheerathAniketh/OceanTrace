"""
ais/generate_synthetic.py

Generates fake AIS vessel tracks around a spill's estimated origin
point/time — since no real AIS is matched to a real spill event, this
fabricates a plausible traffic scene: several "innocent" vessels
following real headings through the area, and one vessel deliberately
routed close to the origin in both space and time (the intended
"suspect" for the demo).

Track format matches the pipeline contract: [lat, lon, timestamp].
"""

import math
import random
from datetime import timedelta

VESSEL_NAMES = [
    "MV Kalindi Star", "MT Ocean Pearl", "SS Coral Voyager",
    "MV Sagar Ratna", "MT Indus Trader", "MV Konkan Queen",
    "SS Malabar Wind", "MV Ratnagiri Voyager", "MT Ganga Mariner",
    "MV Sindhu Prakash", "SS Coastal Falcon", "MV Deccan Voyager",
]

# 7-digit IMO-shaped numbers, generated instead of a fixed short list,
# so going past 6 vessels no longer reuses IDs.
def _imo_for_index(i):
    return f"IMO{9500000 + i * 137 + 41}"


def _km_to_deg_lat(km):
    return km / 111.0


def _km_to_deg_lon(km, lat_deg):
    return km / (111.0 * math.cos(math.radians(lat_deg)))


def _random_track_near(lat, lon, timestamp, n_points=4, spread_km=8,
                        time_spread_hours=3, seed=None):
    """
    Unchanged from before — kept for compatibility, no longer used by
    the innocent-vessel path below (see _heading_track), but left here
    in case anything else imports it directly.
    """
    rng = random.Random(seed)
    track = []
    for i in range(n_points):
        dlat = rng.uniform(-spread_km, spread_km) / 111.0
        dlon = rng.uniform(-spread_km, spread_km) / 111.0
        dt = timedelta(hours=rng.uniform(-time_spread_hours, time_spread_hours) + i * 0.5)
        t = timestamp + dt
        track.append([
            round(lat + dlat, 6),
            round(lon + dlon, 6),
            t.isoformat().replace("+00:00", "Z"),
        ])
    track.sort(key=lambda p: p[2])
    return track


def _heading_track(start_lat, start_lon, start_time, heading_deg, speed_kmh,
                    n_points=4, interval_hours=0.75, seed=None):
    """
    Builds a track that actually moves along one heading at one speed,
    with small per-step noise — looks like a real ship's course on the
    map instead of scattered independent points.
    """
    rng = random.Random(seed)
    heading_rad = math.radians(heading_deg)
    track = []
    lat, lon, t = start_lat, start_lon, start_time
    for i in range(n_points):
        track.append([round(lat, 6), round(lon, 6), t.isoformat().replace("+00:00", "Z")])
        dist_km = speed_kmh * interval_hours + rng.uniform(-0.4, 0.4)
        lat += _km_to_deg_lat(dist_km * math.cos(heading_rad)) + rng.uniform(-0.002, 0.002)
        lon += _km_to_deg_lon(dist_km * math.sin(heading_rad), lat) + rng.uniform(-0.002, 0.002)
        t += timedelta(hours=interval_hours + rng.uniform(-0.1, 0.1))
    return track


def _suspect_track(origin_lat, origin_lon, origin_time, n_points=4, seed=None):
    """
    Unchanged — builds a track that plausibly passes directly through
    the origin point around the origin time, so it scores highest once
    ais/score_vessels.py runs.
    """
    rng = random.Random(seed)
    track = []
    bearing_lat = rng.uniform(-1, 1)
    bearing_lon = rng.uniform(-1, 1)

    for offset_hours in [-1.5, -0.5, 0.0, 1.0]:
        frac = offset_hours / 1.5
        lat = origin_lat + bearing_lat * 0.02 * frac
        lon = origin_lon + bearing_lon * 0.02 * frac
        t = origin_time + timedelta(hours=offset_hours)
        track.append([round(lat, 6), round(lon, 6), t.isoformat().replace("+00:00", "Z")])
    return track


def generate_synthetic_vessels(estimated_origin, region_bounds, n_vessels=8, seed=42):
    """
    estimated_origin: {"lat": ..., "lon": ..., "time": "ISO8601 string"}
    region_bounds: (min_lon, min_lat, max_lon, max_lat) — used to scatter
                   the "innocent" vessels somewhere plausible nearby.
    n_vessels: total vessels to generate, including the one suspect.
               Default bumped 4 -> 8 for a busier, more realistic-looking
               shipping lane in the demo.

    Returns a list of vessel dicts (without scores yet — that's
    ais/score_vessels.py's job): [{vessel_id, name, track}, ...]
    """
    from datetime import datetime

    n_vessels = max(1, n_vessels)  # guard against 0 (old bug: still returned 1)

    origin_lat = estimated_origin["lat"]
    origin_lon = estimated_origin["lon"]
    origin_time = datetime.fromisoformat(estimated_origin["time"].replace("Z", "+00:00"))

    min_lon, min_lat, max_lon, max_lat = region_bounds
    rng = random.Random(seed)

    vessels = []

    # one deliberate suspect, passing through the origin
    vessels.append({
        "vessel_id": _imo_for_index(0),
        "name": VESSEL_NAMES[0],
        "track": _suspect_track(origin_lat, origin_lon, origin_time, seed=seed),
    })

    # remaining vessels: real headings/speeds, spread across the region
    # at varying distances from the origin — some near, some far, so the
    # ranking looks like it's discriminating between genuine candidates
    for i in range(1, n_vessels):
        rand_lat = rng.uniform(min_lat - 0.25, max_lat + 0.25)
        rand_lon = rng.uniform(min_lon - 0.25, max_lon + 0.25)
        time_offset = timedelta(hours=rng.uniform(-8, 8))
        vessel_start_time = origin_time + time_offset

        heading_deg = rng.uniform(0, 360)
        speed_kmh = rng.uniform(9, 24)  # roughly 5-13 knots, plausible coastal traffic

        vessels.append({
            "vessel_id": _imo_for_index(i),
            "name": VESSEL_NAMES[i % len(VESSEL_NAMES)],
            "track": _heading_track(
                rand_lat, rand_lon, vessel_start_time,
                heading_deg=heading_deg, speed_kmh=speed_kmh,
                seed=seed + i,
            ),
        })

    return vessels


if __name__ == "__main__":
    import json

    fake_origin = {"lat": 19.026, "lon": 72.814, "time": "2026-09-08T08:00:00Z"}
    fake_bounds = (72.70, 19.05, 72.76, 19.10)

    vessels = generate_synthetic_vessels(fake_origin, fake_bounds, n_vessels=8)
    print(json.dumps(vessels, indent=2))

    