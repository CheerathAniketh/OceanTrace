"""
drift/vector_field.py

A simplified, synthetic wind/current vector field for the fixed demo
region (Arabian Sea, lat 19.05-19.10, lon 72.70-72.76). Not real
oceanographic/meteorological data — just smooth and directionally
consistent enough to produce a plausible drift path for the demo.

Velocities are in km/h. u = eastward component, v = northward component.
"""

import math

# Base current direction/speed — loosely "monsoon-like" southwest drift.
# Tune these two numbers if you want the drift to visibly point a
# different direction on the map.
BASE_U_KMH = -1.8   # negative = westward component
BASE_V_KMH = 0.9    # positive = northward component


def get_velocity(lat, lon, timestamp=None):
    """
    Return (u, v) velocity in km/h at a given lat/lon (and optionally a
    datetime for slight time-variation). Synthetic field: a constant
    base current plus a small smooth spatial oscillation, so nearby
    points don't have identical velocity (looks more natural on a map).
    """
    # small spatial perturbation so the field isn't perfectly uniform
    perturb_u = 0.3 * math.sin(lat * 40)
    perturb_v = 0.3 * math.cos(lon * 40)

    u = BASE_U_KMH + perturb_u
    v = BASE_V_KMH + perturb_v
    return u, v


def step_position(lat, lon, dt_hours, timestamp=None):
    """
    Advect a single point forward by dt_hours using the velocity field
    at its current position (simple Euler integration — fine at this
    scale/timestep, no need for anything fancier).

    Positive dt_hours moves forward in time, negative moves backward.
    """
    u, v = get_velocity(lat, lon, timestamp)

    # km -> degrees conversion
    # 1 degree latitude ~= 111 km everywhere
    # 1 degree longitude ~= 111 km * cos(latitude)
    dlat = (v * dt_hours) / 111.0
    dlon = (u * dt_hours) / (111.0 * math.cos(math.radians(lat)))

    return lat + dlat, lon + dlon