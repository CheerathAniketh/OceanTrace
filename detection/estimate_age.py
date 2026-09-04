"""
detection/estimate_age.py

Estimates elapsed time since a spill occurred, using Fay's (1971)
gravity-viscous oil-spreading law -- the same physics NOAA's own
GNOME/ADIOS oil-spill trajectory software is built on.

--- Honest scope of what this does and doesn't do ---

A single SAR snapshot gives you the slick's CURRENT area. It does not,
and cannot, tell you the spilled volume or oil type on its own -- those
have to be assumed. So this module answers a conditional question:

    "IF a spill of volume V (of a given oil type) occurred in calm
     water, how long would it take to spread to the observed area A?"

That's a legitimate, real, textbook physics estimate -- not a fabricated
number -- but it depends on assumptions (spill volume, oil density,
water viscosity) that can't be derived from the image alone. Present it
to judges as "age estimated under assumed spill parameters," not as a
precise, assumption-free measurement.

--- The physics ---

Fay (1971) divides oil spreading into three phases:
  1. Gravity-inertial   (minutes -- gravity vs. the oil's own inertia)
  2. Gravity-viscous     (hours to ~10 days for large spills -- gravity
                          vs. drag from the water boundary layer)
  3. Surface-tension-viscous (weeks-months -- very thin films)

Detected spills are almost always caught in phase 2, so that's the
regime this module models. The classic closed-form relation (used
across the oil-spill remote-sensing literature specifically for this
"estimate age from observed area" purpose) is:

    A(t) = pi * k2^2 * ( (delta_rho/rho_w) * g * V^2 )^(1/3)
                      * (nu_w)^(-1/6) * t^(1/2)

where:
    A(t)        slick area at time t                      [m^2]
    V           spilled oil volume                        [m^3]
    delta_rho   rho_water - rho_oil                        [kg/m^3]
    rho_w       water density                              [kg/m^3]
    g           gravitational acceleration                 [m/s^2]
    nu_w        kinematic viscosity of water                [m^2/s]
    k2          empirical spreading constant, literature
                values range ~1.14-1.7; Fay's original
                value (used here) is 1.7                    [-]
    t           elapsed time since spill                    [s]

Since A ~ t^(1/2), this inverts cleanly:  t = (A / C)^2
where C is everything except t^(1/2) in the equation above.

Reference: Fay, J.A. (1971), "Physical processes in the spread of oil
on a water surface", Proc. Joint Conf. on Prevention and Control of
Oil Spills. Also implemented (as FayGravityViscous) in NOAA's own
GNOME oil-spill trajectory model.
"""

import math


G = 9.81  # gravitational acceleration, m/s^2

# Reasonable default assumptions -- override these with better estimates
# if you have them (e.g. a specific oil type suspected from the incident).
DEFAULT_OIL_DENSITY_KG_M3 = 900       # medium/light crude, typical range 850-950
DEFAULT_WATER_DENSITY_KG_M3 = 1025    # typical seawater
DEFAULT_WATER_KINEMATIC_VISCOSITY = 1.0e-6  # m^2/s, seawater at ~20 degC
DEFAULT_SPILL_VOLUME_M3 = 1000        # ~1000 m^3 -- a moderate-size tanker spill
DEFAULT_K2 = 1.7                      # Fay's original gravity-viscous constant


def estimate_spill_age(
    area_km2: float,
    spill_volume_m3: float = DEFAULT_SPILL_VOLUME_M3,
    oil_density_kg_m3: float = DEFAULT_OIL_DENSITY_KG_M3,
    water_density_kg_m3: float = DEFAULT_WATER_DENSITY_KG_M3,
    water_kinematic_viscosity: float = DEFAULT_WATER_KINEMATIC_VISCOSITY,
    k2: float = DEFAULT_K2,
):
    """
    Estimates elapsed time since a spill began, given its currently
    observed area, using Fay's (1971) gravity-viscous spreading law.

    Parameters
    ----------
    area_km2 : float
        The detected slick's area, in km^2 (this is exactly what
        detect_spill.py's mask_to_spill_detection() already computes).
    spill_volume_m3, oil_density_kg_m3, water_density_kg_m3,
    water_kinematic_viscosity, k2 :
        Assumed spill/fluid parameters -- see module docstring. Defaults
        are reasonable but ARE assumptions, not measurements.

    Returns
    -------
    dict with:
        estimated_age_hours : float
        estimated_age_days  : float
        assumptions         : dict of the parameters actually used
        regime_valid        : bool -- whether this estimate falls inside
                               Fay's gravity-viscous regime's typical
                               validity window (roughly hours to ~10
                               days for spills of this size). Outside
                               this window the estimate is unreliable
                               because a different spreading phase
                               would actually be governing.
        caveat : str -- short human-readable caveat, for surfacing in
                 the API/frontend so it's never presented as a bare
                 unqualified number.
    """
    area_m2 = area_km2 * 1_000_000

    delta_rho = water_density_kg_m3 - oil_density_kg_m3
    if delta_rho <= 0:
        raise ValueError(
            "Assumed oil density must be less than water density "
            "(oil has to float) -- check oil_density_kg_m3/water_density_kg_m3."
        )

    relative_buoyancy = delta_rho / water_density_kg_m3

    # C = coefficient such that A(t) = C * t^(1/2)
    C = (
        math.pi
        * (k2 ** 2)
        * (relative_buoyancy * G * (spill_volume_m3 ** 2)) ** (1 / 3)
        * (water_kinematic_viscosity ** (-1 / 6))
    )

    # Invert: A = C * t^(1/2)  =>  t = (A / C)^2
    t_seconds = (area_m2 / C) ** 2
    t_hours = t_seconds / 3600
    t_days = t_hours / 24

    # Gravity-viscous regime is typically valid from ~minutes/hours out to
    # roughly 4-10 days for large spills (per Fay 1971 / oil-spill
    # literature). Flag if the estimate falls outside a conservative
    # window, since outside it a different phase would actually dominate
    # and this formula's assumptions break down.
    regime_valid = 0.1 <= t_days <= 10

    return {
        "estimated_age_hours": round(t_hours, 2),
        "estimated_age_days": round(t_days, 2),
        "assumptions": {
            "spill_volume_m3": spill_volume_m3,
            "oil_density_kg_m3": oil_density_kg_m3,
            "water_density_kg_m3": water_density_kg_m3,
            "water_kinematic_viscosity_m2_s": water_kinematic_viscosity,
            "k2_spreading_constant": k2,
        },
        "regime_valid": regime_valid,
        "caveat": (
            "Estimated using Fay (1971) gravity-viscous spreading law, "
            "assuming the spill parameters listed above. A single SAR "
            "image cannot determine actual spill volume or oil type; "
            "changing those assumptions changes this estimate. Treat as "
            "an order-of-magnitude estimate, not a precise measurement."
            + ("" if regime_valid else (
                " NOTE: estimated age falls outside this model's typical "
                "validity window (~2.4 hours to ~10 days) -- a different "
                "spreading phase may actually govern, so this estimate "
                "is less reliable here."
            ))
        ),
    }


if __name__ == "__main__":
    # Example using your synthetic detection's real output (5.94 km^2,
    # from detect_spill.py's test run this session).
    result = estimate_spill_age(area_km2=5.94)
    print("Example: synthetic test detection (area = 5.94 km^2)")
    for k, v in result.items():
        print(f"  {k}: {v}")

    print()

    # Example using the real Sentinel-1 crop's much smaller detection
    # (0.03 km^2, from run_real_inference.py's output this session).
    result_real = estimate_spill_age(area_km2=0.03)
    print("Example: real Sentinel-1 crop detection (area = 0.03 km^2)")
    for k, v in result_real.items():
        print(f"  {k}: {v}")