# Pipeline Output Contract

This is the JSON shape `pipeline/run_pipeline.py` must produce. The
frontend (separate repo, Karthik) builds against this shape using mock
data — this is the agreed interface between backend and frontend, don't
change it without updating both sides.

```json
{
  "spill": {
    "polygon": [[lat, lon], [lat, lon], "..."],
    "detected_at": "2026-09-08T14:00:00Z",
    "area_km2": 12.4
  },
  "drift": {
    "hindcast_path": [[lat, lon, "timestamp"], "..."],
    "estimated_origin": {
      "lat": 0.0,
      "lon": 0.0,
      "time": "2026-09-08T09:00:00Z"
    },
    "forecast_path": [[lat, lon, "timestamp"], "..."]
  },
  "vessels": [
    {
      "vessel_id": "string",
      "name": "string",
      "score": 0.0,
      "proximity_score": 0.0,
      "trajectory_score": 0.0,
      "anomaly_score": 0.0,
      "track": [[lat, lon, "timestamp"], "..."]
    }
  ]
}
```

## Notes

- Coordinates: `[lat, lon]` order, decimal degrees.
- Timestamps: ISO 8601 UTC.
- `vessels` is pre-sorted by `score` descending — highest = top suspect.
  Frontend renders top 5 by default, "show more" for the rest.
- Scores are normalized 0.0–1.0.

## Two pipeline entry points

`pipeline/run_pipeline.py` has two functions producing this same
contract shape:

- `run_pipeline()` — original synthetic-PALSAR demo path.
- `run_pipeline_real()` — runs detection on a real, windowed crop of a
  real Sentinel-1 GRD scene (see `detection/run_real_inference.py` and
  `detection/extract_geo.py`), then feeds it through identical
  drift/AIS logic. Same contract shape, real detection + real
  georeferencing instead of synthetic. AIS vessel identities/tracks are
  still synthetic in both paths — see `README.md` Section 7 for the
  full real-vs-simulated breakdown.

CLI: `python -m pipeline.run_pipeline` (synthetic, writes
`outputs/pipeline_result.json`) vs `python -m pipeline.run_pipeline
--real` (real scene, writes `outputs/pipeline_result_real.json`).
Frontend/API should treat both output files as valid contract-shaped
data — same shape either way, only the values' provenance differs.

## `[lon, lat]` vs `[lat, lon]` — RESOLVED

`detection/detect_spill.py` outputs a richer detection object (includes
`spill_id`, `source_image`, `bbox`, `perimeter_km`, `elongation`,
`fragment_count`, `confidence`, and `polygon` as a GeoJSON `Polygon`
type with `[lon, lat]` coordinate order — opposite to the contract
above, which uses `[lat, lon]`).

Resolved via **option 1**: `pipeline/run_pipeline.py`'s internal helpers
(`_lonlat_polygon_to_latlon`, `_build_pipeline_output`) convert
detection's richer `[lon, lat]` GeoJSON output down to this contract's
simpler `[lat, lon]` shape at the pipeline boundary. Detection's full
richer object (bbox, perimeter, elongation, fragment_count, confidence)
remains available internally for debugging/logging but is not currently
passed through to the frontend contract. Revisit if any of those extra
geometric properties turn out to be worth surfacing in the dashboard.