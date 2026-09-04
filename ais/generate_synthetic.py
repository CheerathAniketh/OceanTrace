"""
ais/generate_synthetic.py

Generates fake AIS vessel tracks around a spill's estimated origin
point/time — since no real AIS is matched to a real spill event, this
fabricates a plausible traffic scene: a few "innocent" vessels passing
through the area, and one vessel deliberately routed close to the origin
in both space and time (the intended "suspect" for the demo).

Track format matches the pipeline contract: [lat, lon, timestamp].
"""

import random
from datetime import timedelta

VESSEL_NAMES = [
    "MV Kalindi Star", "MT Ocean Pearl", "SS Coral Voyager",
    "MV Sagar Ratna", "MT Indus Trader", "MV Konkan Queen",
]

VESSEL_IMOS = [
    "IMO9812345", "IMO9754321", "IMO9698765",
    "IMO9631234", "IMO9587654", "IMO9543210",
]


def _random_track_near(lat, lon, timestamp, n_points=4, spread_km=8,
                        time_spread_hours=3, seed=None):
    """
    Build a short track of n_points around (lat, lon, timestamp), with
    random spatial jitter and points spaced out in time.
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
    track.sort(key=lambda p: p[2])  # keep chronological order
    return track


def _suspect_track(origin_lat, origin_lon, origin_time, n_points=4, seed=None):
    """
    Build a track that plausibly passes directly through the origin
    point around the origin time — this is the vessel meant to score
    highest once ais/score_vessels.py runs.
    """
    rng = random.Random(seed)
    track = []
    # approach from a random bearing, pass through the origin, continue past it
    bearing_lat = rng.uniform(-1, 1)
    bearing_lon = rng.uniform(-1, 1)

    for i, offset_hours in enumerate([-1.5, -0.5, 0.0, 1.0]):
        frac = offset_hours / 1.5  # -1 at start, 0 at origin, >0 after
        lat = origin_lat + bearing_lat * 0.02 * frac
        lon = origin_lon + bearing_lon * 0.02 * frac
        t = origin_time + timedelta(hours=offset_hours)
        track.append([
            round(lat, 6),
            round(lon, 6),
            t.isoformat().replace("+00:00", "Z"),
        ])
    return track


def generate_synthetic_vessels(estimated_origin, region_bounds, n_vessels=4, seed=42):
    """
    estimated_origin: {"lat": ..., "lon": ..., "time": "ISO8601 string"}
    region_bounds: (min_lon, min_lat, max_lon, max_lat) — used to scatter
                   the "innocent" vessels somewhere plausible nearby.
    n_vessels: total vessels to generate, including the one suspect.

    Returns a list of vessel dicts (without scores yet — that's
    ais/score_vessels.py's job): [{vessel_id, name, track}, ...]
    """
    from datetime import datetime

    origin_lat = estimated_origin["lat"]
    origin_lon = estimated_origin["lon"]
    origin_time = datetime.fromisoformat(estimated_origin["time"].replace("Z", "+00:00"))

    min_lon, min_lat, max_lon, max_lat = region_bounds
    rng = random.Random(seed)

    vessels = []

    # one deliberate suspect, passing through the origin
    vessels.append({
        "vessel_id": VESSEL_IMOS[0],
        "name": VESSEL_NAMES[0],
        "track": _suspect_track(origin_lat, origin_lon, origin_time, seed=seed),
    })

    # remaining vessels: scattered nearby, not necessarily close to origin
    for i in range(1, n_vessels):
        # pick a random point somewhere in/near the region, not tied to origin
        rand_lat = rng.uniform(min_lat - 0.25, max_lat + 0.25)
        rand_lon = rng.uniform(min_lon - 0.25, max_lon + 0.25)
        # random time offset so some vessels aren't even near the origin time
        time_offset = timedelta(hours=rng.uniform(-8, 8))
        vessel_time = origin_time + time_offset

        vessels.append({
            "vessel_id": VESSEL_IMOS[i % len(VESSEL_IMOS)],
            "name": VESSEL_NAMES[i % len(VESSEL_NAMES)],
            "track": _random_track_near(rand_lat, rand_lon, vessel_time, seed=seed + i),
        })

    return vessels


if __name__ == "__main__":
    import json

    fake_origin = {"lat": 19.026, "lon": 72.814, "time": "2026-09-08T08:00:00Z"}
    fake_bounds = (72.70, 19.05, 72.76, 19.10)

    vessels = generate_synthetic_vessels(fake_origin, fake_bounds, n_vessels=4)
    print(json.dumps(vessels, indent=2))