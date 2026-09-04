"""
ais/score_vessels.py

Scores candidate vessels by how likely they are to be responsible for
a detected spill, based on:
  - proximity: how close the vessel ever got to the estimated origin
  - trajectory: how close in both space AND time (closest approach,
    not just closest distance ignoring when)
  - anomaly: behavioral red flags — here, irregular AIS reporting gaps
    (a vessel "going dark" for a while is a classic real-world evasion
    tactic, so large gaps between consecutive track points are treated
    as suspicious)

Combines the three into one overall score per vessel, sorted descending.
"""

import math
from datetime import datetime


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points, in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _parse_ts(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _proximity_score(track, origin_lat, origin_lon, max_dist_km=60):
    """
    Best (minimum) distance from any track point to the origin,
    converted to a 0-1 score. Closer = higher score.
    """
    min_dist = min(_haversine_km(p[0], p[1], origin_lat, origin_lon) for p in track)
    score = max(0.0, 1.0 - (min_dist / max_dist_km))
    return score, min_dist


def _trajectory_score(track, origin_lat, origin_lon, origin_time,
                       max_dist_km=60, max_time_hours=6):
    """
    Finds the track point closest in TIME to the origin, then scores
    based on how close that same point is in SPACE. This catches
    vessels that were near the right place but at the wrong time (or
    vice versa) and scores them lower than a true space+time match.
    """
    origin_dt = _parse_ts(origin_time)
    best = min(track, key=lambda p: abs((_parse_ts(p[2]) - origin_dt).total_seconds()))

    time_diff_hours = abs((_parse_ts(best[2]) - origin_dt).total_seconds()) / 3600.0
    space_dist_km = _haversine_km(best[0], best[1], origin_lat, origin_lon)

    time_score = max(0.0, 1.0 - (time_diff_hours / max_time_hours))
    space_score = max(0.0, 1.0 - (space_dist_km / max_dist_km))

    # both need to be reasonably good — multiply rather than average,
    # so a vessel that's close in space but way off in time doesn't
    # still score highly
    return time_score * space_score


def _anomaly_score(track):
    """
    Flags irregular gaps between consecutive AIS reports. A vessel
    "going dark" (a real evasion tactic — turning off AIS transponders)
    shows up as an unusually large gap compared to its own other
    intervals. Returns higher score = more anomalous/suspicious.
    """
    timestamps = sorted(_parse_ts(p[2]) for p in track)
    if len(timestamps) < 2:
        return 0.0

    gaps_hours = [
        (timestamps[i + 1] - timestamps[i]).total_seconds() / 3600.0
        for i in range(len(timestamps) - 1)
    ]
    max_gap = max(gaps_hours)
    avg_gap = sum(gaps_hours) / len(gaps_hours)

    if avg_gap == 0:
        return 0.0

    # how much bigger is the largest gap than the average gap?
    ratio = max_gap / avg_gap
    # scale: ratio of 1 (perfectly even spacing) -> 0 score
    #        ratio of 4+ (one gap much bigger than the rest) -> 1 score
    score = min(1.0, max(0.0, (ratio - 1.0) / 3.0))
    return score


def score_vessels(vessels, estimated_origin, weights=None):
    """
    vessels: list of {"vessel_id", "name", "track"} (from
             generate_synthetic_vessels or real AIS data in the same shape)
    estimated_origin: {"lat", "lon", "time"}

    Returns vessels list with scores added, sorted by overall score
    descending — matches the pipeline contract's vessel shape.
    """
    if weights is None:
        weights = {"proximity": 0.4, "trajectory": 0.4, "anomaly": 0.2}

    origin_lat = estimated_origin["lat"]
    origin_lon = estimated_origin["lon"]
    origin_time = estimated_origin["time"]

    scored = []
    for v in vessels:
        track = v["track"]

        prox_score, _ = _proximity_score(track, origin_lat, origin_lon)
        traj_score = _trajectory_score(track, origin_lat, origin_lon, origin_time)
        anom_score = _anomaly_score(track)

        overall = (
            weights["proximity"] * prox_score
            + weights["trajectory"] * traj_score
            + weights["anomaly"] * anom_score
        )

        scored.append({
            "vessel_id": v["vessel_id"],
            "name": v["name"],
            "score": round(overall, 4),
            "proximity_score": round(prox_score, 4),
            "trajectory_score": round(traj_score, 4),
            "anomaly_score": round(anom_score, 4),
            "track": track,
        })

    scored.sort(key=lambda v: v["score"], reverse=True)
    return scored


if __name__ == "__main__":
    import json
    from ais.generate_synthetic import generate_synthetic_vessels

    fake_origin = {"lat": 19.026, "lon": 72.814, "time": "2026-09-08T08:00:00Z"}
    fake_bounds = (72.70, 19.05, 72.76, 19.10)

    vessels = generate_synthetic_vessels(fake_origin, fake_bounds, n_vessels=4)
    ranked = score_vessels(vessels, fake_origin)

    for v in ranked:
        print(f"{v['name']:<20} score={v['score']:.3f}  "
              f"(prox={v['proximity_score']:.2f}, "
              f"traj={v['trajectory_score']:.2f}, "
              f"anom={v['anomaly_score']:.2f})")