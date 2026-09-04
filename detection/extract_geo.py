"""
detection/extract_geo.py

Extracts real georeferencing info (bounding box, CRS, transform) from a
real Sentinel-1 GRD GeoTIFF, and provides a pixel(row, col) -> (lat, lon)
converter. This replaces the old hardcoded demo bbox
(72.70, 19.05, 72.76, 19.10) with real coordinates read from the scene.

Usage (standalone check):
    python detection/extract_geo.py

Usage (as a module, from run_pipeline.py or detect_spill.py):
    from detection.extract_geo import get_scene_bounds, pixel_to_latlon

    bounds, crs, transform = get_scene_bounds(SAR_TIFF_PATH)
    lat, lon = pixel_to_latlon(transform, row, col)
"""

import numpy as np
import rasterio
from scipy.interpolate import griddata

# Path to the real VV-polarization GeoTIFF (VV is standard for spill detection).
SAR_TIFF_PATH = (
    "data/real_sar/"
    "S1D_IW_GRDH_1SDV_20260626T010234_20260626T010259_003400_005FC3_48CE.SAFE/"
    "measurement/"
    "s1d-iw-grd-vv-20260626t010234-20260626t010259-003400-005fc3-001.tiff"
)


def _load_gcps(tiff_path: str):
    """
    Raw Sentinel-1 GRD products are georeferenced via a scattered set of
    Ground Control Points (GCPs) -- (pixel_row, pixel_col) -> (lat, lon)
    tie-points -- rather than a single affine transform. src.crs is None
    for these files; src.gcps is where the real geo-info lives.
    """
    with rasterio.open(tiff_path) as src:
        gcps, gcp_crs = src.gcps
        if not gcps:
            raise RuntimeError(
                f"No GCPs found in {tiff_path} -- this file may not be "
                "georeferenced, or uses a different scheme."
            )
        shape = (src.height, src.width)

    # Each gcp has .row, .col (pixel space) and .x, .y (lon, lat -- GCP CRS is
    # typically EPSG:4326 already for Sentinel-1, but we keep gcp_crs to be safe)
    rows = np.array([g.row for g in gcps])
    cols = np.array([g.col for g in gcps])
    lons = np.array([g.x for g in gcps])
    lats = np.array([g.y for g in gcps])

    return rows, cols, lons, lats, gcp_crs, shape


def get_scene_bounds(tiff_path: str = SAR_TIFF_PATH):
    """
    Returns the scene's real bounding box in (min_lon, min_lat, max_lon, max_lat),
    derived from the scene's GCPs (Ground Control Points), plus the GCP CRS
    and image shape.
    """
    rows, cols, lons, lats, gcp_crs, shape = _load_gcps(tiff_path)

    bounds_wgs84 = (lons.min(), lats.min(), lons.max(), lats.max())
    return bounds_wgs84, gcp_crs, shape


def pixel_to_latlon(tiff_path: str, row: int, col: int):
    """
    Converts a single pixel (row, col) from the detection model's output
    mask into real (lat, lon), by interpolating between the scene's GCPs.

    Uses linear interpolation (griddata) over the scattered GCP mesh --
    accurate enough for a spill polygon's vertices, which are far sparser
    than the underlying GCP grid.
    """
    rows, cols, lons, lats, _, _ = _load_gcps(tiff_path)
    points = np.column_stack([rows, cols])

    lon = griddata(points, lons, (row, col), method="linear")
    lat = griddata(points, lats, (row, col), method="linear")

    return float(lat), float(lon)


def polygon_pixels_to_latlon(tiff_path: str, pixel_polygon: list):
    """
    Converts a full polygon (list of (row, col) pixel vertices, as produced
    by the U-Net's contour/mask-to-polygon step) into a list of (lat, lon)
    vertices, interpolated from the scene's real GCPs. This replaces the
    old hardcoded bbox-based polygon with real coordinates.

    pixel_polygon: list of (row, col) tuples
    returns: list of (lat, lon) tuples
    """
    rows, cols, lons, lats, _, _ = _load_gcps(tiff_path)
    points = np.column_stack([rows, cols])

    query_points = np.array(pixel_polygon)  # shape (N, 2) of (row, col)
    interp_lons = griddata(points, lons, query_points, method="linear")
    interp_lats = griddata(points, lats, query_points, method="linear")

    return list(zip(interp_lats.tolist(), interp_lons.tolist()))


if __name__ == "__main__":
    bounds, gcp_crs, shape = get_scene_bounds()
    min_lon, min_lat, max_lon, max_lat = bounds

    print("=== Real Sentinel-1 Scene Georeferencing (via GCPs) ===")
    print(f"GCP CRS:         {gcp_crs}")
    print(f"Image shape:     {shape[0]} rows x {shape[1]} cols")
    print(f"Real bbox (WGS84 lat/lon):")
    print(f"  min_lon={min_lon:.5f}, min_lat={min_lat:.5f}")
    print(f"  max_lon={max_lon:.5f}, max_lat={max_lat:.5f}")
    print()
    print("Old hardcoded placeholder was:")
    print("  (72.70, 19.05, 72.76, 19.10)")
    print()
    print("Compare the two above -- the real scene almost certainly covers")
    print("a MUCH larger area (Sentinel-1 IW swaths are ~250km wide), so")
    print("downstream code (drift/AIS) will need this real, larger bbox")
    print("rather than the old tiny placeholder.")