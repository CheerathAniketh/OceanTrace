"""
pipeline/run_pipeline.py

Orchestrates detection -> drift -> AIS into a single JSON output matching
docs/contract.md's shape. This is the one file that turns three separate,
independently-tested modules into the actual end-to-end demo.

Two entry points:
  - run_pipeline()       : original synthetic-PALSAR path (unchanged behavior)
  - run_pipeline_real()  : real Sentinel-1 scene path (new)

Both funnel into _build_pipeline_output(), so drift/AIS logic is identical
either way -- only the detection stage and its region bounds differ.

Run with:
    python -m pipeline.run_pipeline            # synthetic (default, unchanged)
    python -m pipeline.run_pipeline --real      # real Sentinel-1 scene
"""

import json
import sys
from datetime import datetime

from shapely.geometry import Polygon

from detection.detect_spill import detect_spill
from detection.run_real_inference import run_real_inference, REAL_TIFF_PATH
from drift.hindcast import hindcast_drift
from drift.forecast import forecast_drift
from ais.generate_synthetic import generate_synthetic_vessels
from ais.score_vessels import score_vessels


# Fixed demo region — used only by the synthetic path. Must match
# detection's test bounds and the frontend's mock data. See docs/NOTES.md.
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


def _build_pipeline_output(detection, region_bounds):
    """
    Shared back-half of the pipeline: takes a detection record (from
    either the synthetic or real path, same JSON shape either way) and
    a region bbox (used to scope synthetic AIS vessel generation), and
    runs drift + AIS + assembles the final contract-shaped output.
    """
    spill_polygon_latlon = _lonlat_polygon_to_latlon(detection["polygon"])
    centroid_lat, centroid_lon = _polygon_centroid_latlon(detection["polygon"])

    spill = {
        "polygon": spill_polygon_latlon,
        "detected_at": detection["detected_at"],
        "area_km2": detection["area_km2"],
    }

    # ---- Drift (hindcast + forecast) ----
    hindcast_path, estimated_origin = hindcast_drift(
        centroid_lat, centroid_lon, detection["detected_at"]
    )
    forecast_path = forecast_drift(centroid_lat, centroid_lon, detection["detected_at"])

    drift = {
        "hindcast_path": hindcast_path,
        "estimated_origin": estimated_origin,
        "forecast_path": forecast_path,
    }

    # ---- AIS (synthetic generation + scoring) ----
    # NOTE: vessel traffic itself is still synthetic either way (real AIS
    # is a separate, not-yet-done piece -- see session notes / GFW).
    # region_bounds here just scopes WHERE synthetic vessels get placed,
    # so they cluster near the real spill location when using real detection.
    vessels_raw = generate_synthetic_vessels(estimated_origin, region_bounds, n_vessels=4)
    vessels_ranked = score_vessels(vessels_raw, estimated_origin)

    return {
        "spill": spill,
        "drift": drift,
        "vessels": vessels_ranked,
    }


def run_pipeline(image_path, spill_id="spill_001", detected_at=None):
    """
    Original synthetic-PALSAR path. Unchanged behavior.
    """
    if detected_at is None:
        detected_at = datetime.utcnow().isoformat() + "Z"

    detection = detect_spill(
        image_path=image_path,
        image_bounds=REGION_BOUNDS,
        spill_id=spill_id,
        detected_at=detected_at,
    )
    if detection is None:
        raise RuntimeError(f"No spill detected in {image_path}")

    return _build_pipeline_output(detection, REGION_BOUNDS)


def run_pipeline_real(tiff_path=REAL_TIFF_PATH, checkpoint_path="best_unet_spill.pth",
                       row_off=None, col_off=None, spill_id="spill_real_001",
                       detected_at=None):
    """
    Real Sentinel-1 scene path. Runs detection on a real windowed crop
    (see detection/run_real_inference.py), then feeds the result through
    the same drift/AIS logic as the synthetic path.

    NOTE: as discussed, this real crop is open ocean with no confirmed
    real spill -- if run_real_inference returns None (no contours found),
    this will raise, same as the synthetic path does. That's expected
    behavior, not a bug -- it means "no spill-like feature in this crop."
    """
    if detected_at is None:
        detected_at = datetime.utcnow().isoformat() + "Z"

    detection = run_real_inference(
        tiff_path=tiff_path,
        checkpoint_path=checkpoint_path,
        row_off=row_off,
        col_off=col_off,
        spill_id=spill_id,
        detected_at=detected_at,
    )
    if detection is None:
        raise RuntimeError(
            "No spill-like feature detected in this real window. "
            "This is expected for most real open-water crops -- try a "
            "different row_off/col_off, or fall back to the synthetic "
            "path for the live demo."
        )

    # Use the detection's own real bbox (from the window) to scope AIS
    # vessel placement, instead of the fixed synthetic demo region.
    region_bounds = tuple(detection["bbox"])
    return _build_pipeline_output(detection, region_bounds)


if __name__ == "__main__":
    use_real = "--real" in sys.argv

    if use_real:
        result = run_pipeline_real(detected_at="2026-09-08T14:00:00Z")
        out_path = "outputs/pipeline_result_real.json"
    else:
        result = run_pipeline(
            image_path="data/sar_images/images/palsar_101.png",
            spill_id="spill_demo_001",
            detected_at="2026-09-08T14:00:00Z",
        )
        out_path = "outputs/pipeline_result.json"

    print(json.dumps(result, indent=2))

    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {out_path}")