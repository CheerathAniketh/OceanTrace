"""
drift/hindcast.py

Backward-advects a detected spill's position to estimate where and when
it likely originated.
"""

from datetime import datetime, timedelta
from drift.vector_field import step_position


def hindcast_drift(centroid_lat, centroid_lon, detected_at, hours_back=6, step_minutes=30):
    """
    Walk backward from the spill's detected position/time, using the
    vector field in reverse, to build a hindcast path and estimate the
    origin point/time.

    detected_at: ISO 8601 string, e.g. "2026-09-08T14:00:00Z"
    Returns: (hindcast_path, estimated_origin)
      hindcast_path: list of [lat, lon, timestamp] from origin -> detection
      estimated_origin: {"lat": ..., "lon": ..., "time": "..."}
    """
    detected_dt = datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
    step = timedelta(minutes=step_minutes)
    n_steps = int((hours_back * 60) / step_minutes)

    lat, lon = centroid_lat, centroid_lon
    current_time = detected_dt

    path = [[lat, lon, current_time.isoformat().replace("+00:00", "Z")]]

    for _ in range(n_steps):
        # step backward: negative dt_hours moves the point against the
        # current, and we move time backward to match
        lat, lon = step_position(lat, lon, dt_hours=-(step_minutes / 60), timestamp=current_time)
        current_time = current_time - step
        path.append([lat, lon, current_time.isoformat().replace("+00:00", "Z")])

    # path was built detection -> origin; reverse so it reads origin -> detection
    path.reverse()

    estimated_origin = {
        "lat": path[0][0],
        "lon": path[0][1],
        "time": path[0][2],
    }

    return path, estimated_origin