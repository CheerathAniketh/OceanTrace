"""
pipeline/run_pipeline.py

Orchestrates detection -> drift -> AIS into a single JSON output matching
docs/contract.md's shape. This is the one file that turns three separate,
independently-tested modules into the actual end-to-end demo.

Run with: python -m pipeline.run_pipeline
"""

import json
from datetime import datetime

from shapely.geometry import Polygon

from detection.detect_spill import detect_spill
from drift.hindcast import hindcast_drift
from drift.forecast import forecast_drift
from ais.generate_synthetic import generate_synthetic_vessels
from ais.score_vessels import score_vessels


# Fixed demo region — must match detection's test bounds and the
# frontend's mock data. See docs/NOTES.md.
REGION_BOUNDS = (72.70, 19.05, 72.76, 19.10)  # (min_lon, min_lat, max_lon, max_lat)


def _lonlat_polygon_to_latlon(geojson_polygon):
    """
    detect_spill.py outputs a GeoJSON Polygon with [lon, lat] coordinate
    order (the GeoJSON standard). The pipeline contract uses [lat, lon]
    instead (matches what Leaflet/the frontend expects). Convert here,
    at the pipeline boundary, so this is the only place the swap happens.
    """
    coords = geojson_polygon["coordinates"][0]  # outer ring
    return [[lat, lon] for lon, lat in coords]


def _polygon_centroid_latlon(geojson_polygon):
    """
    Compute the centroid of the detection polygon, in [lat, lon] order,
    to use as the drift simulation's starting point.
    """
    coords = geojson_polygon["coordinates"][0]  # [lon, lat] pairs
    poly = Polygon(coords)  # shapely expects (x, y) = (lon, lat)
    centroid = poly.centroid
    return centroid.y, centroid.x  # (lat, lon)


def run_pipeline(image_path, spill_id="spill_001", detected_at=None):
    """
    Runs the full detection -> drift -> AIS pipeline on one SAR image
    and returns a single JSON object matching docs/contract.md.
    """
    if detected_at is None:
        detected_at = datetime.utcnow().isoformat() + "Z"

    # ---- 1. Detection ----
    detection = detect_spill(
        image_path=image_path,
        image_bounds=REGION_BOUNDS,
        spill_id=spill_id,
        detected_at=detected_at,
    )
    if detection is None:
        raise RuntimeError(f"No spill detected in {image_path}")

    spill_polygon_latlon = _lonlat_polygon_to_latlon(detection["polygon"])
    centroid_lat, centroid_lon = _polygon_centroid_latlon(detection["polygon"])

    spill = {
        "polygon": spill_polygon_latlon,
        "detected_at": detection["detected_at"],
        "area_km2": detection["area_km2"],
    }

    # ---- 2. Drift (hindcast + forecast) ----
    hindcast_path, estimated_origin = hindcast_drift(
        centroid_lat, centroid_lon, detected_at
    )
    forecast_path = forecast_drift(centroid_lat, centroid_lon, detected_at)

    drift = {
        "hindcast_path": hindcast_path,
        "estimated_origin": estimated_origin,
        "forecast_path": forecast_path,
    }

    # ---- 3. AIS (synthetic generation + scoring) ----
    vessels_raw = generate_synthetic_vessels(estimated_origin, REGION_BOUNDS, n_vessels=4)
    vessels_ranked = score_vessels(vessels_raw, estimated_origin)

    # ---- 4. Assemble final contract-shaped output ----
    return {
        "spill": spill,
        "drift": drift,
        "vessels": vessels_ranked,
    }


if __name__ == "__main__":
    result = run_pipeline(
        image_path="data/sar_images/images/palsar_101.png",
        spill_id="spill_demo_001",
        detected_at="2026-09-08T14:00:00Z",
    )
    print(json.dumps(result, indent=2))

    # also write to outputs/ so the frontend can load a real file if needed
    with open("outputs/pipeline_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved to outputs/pipeline_result.json")