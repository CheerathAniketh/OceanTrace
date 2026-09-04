"""
drift/forecast.py

Forward-advects a detected spill's position to predict where it's
heading over the next several hours.
"""

from datetime import datetime, timedelta
from drift.vector_field import step_position


def forecast_drift(centroid_lat, centroid_lon, detected_at, hours_forward=12, step_minutes=60):
    """
    Walk forward from the spill's detected position/time, using the
    vector field, to build a predicted forward drift path.

    detected_at: ISO 8601 string, e.g. "2026-09-08T14:00:00Z"
    Returns: forecast_path — list of [lat, lon, timestamp] from
             detection -> predicted future position
    """
    detected_dt = datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
    step = timedelta(minutes=step_minutes)
    n_steps = int((hours_forward * 60) / step_minutes)

    lat, lon = centroid_lat, centroid_lon
    current_time = detected_dt

    path = [[lat, lon, current_time.isoformat().replace("+00:00", "Z")]]

    for _ in range(n_steps):
        lat, lon = step_position(lat, lon, dt_hours=(step_minutes / 60), timestamp=current_time)
        current_time = current_time + step
        path.append([lat, lon, current_time.isoformat().replace("+00:00", "Z")])

    return path