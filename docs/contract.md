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

## Current mismatch to resolve

`detection/detect_spill.py` currently outputs a richer detection object
(includes `spill_id`, `source_image`, `bbox`, `perimeter_km`, `elongation`,
`fragment_count`, `confidence`, and `polygon` as a GeoJSON `Polygon` type
with `[lon, lat]` coordinate order — note the order is opposite to the
contract above, which uses `[lat, lon]`).

Before wiring `detection/` into `pipeline/run_pipeline.py`, either:
1. Convert detection's output into the contract's simpler `spill` shape
   inside `run_pipeline.py` (recommended — keeps detection's richer output
   available internally/for debugging, only simplifies at the pipeline
   boundary), or
2. Update this contract to carry the richer fields through to the
   frontend if the extra geometric properties (elongation, confidence,
   etc.) are worth displaying in the dashboard.

Decide before writing `run_pipeline.py` and update this doc accordingly.