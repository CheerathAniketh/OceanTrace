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
    "area_km2": 12.4,
    "estimated_age": {
      "estimated_age_hours": 105.5,
      "estimated_age_days": 4.4,
      "assumptions": {
        "spill_volume_m3": 1000,
        "oil_density_kg_m3": 900,
        "water_density_kg_m3": 1025,
        "water_kinematic_viscosity_m2_s": 1e-6,
        "k2_spreading_constant": 1.7
      },
      "regime_valid": true,
      "caveat": "string"
    }
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

## `spill.estimated_age` (new)

Optional stretch-goal field per the problem statement ("age if feasible").
Computed by `detection/estimate_age.py` using Fay's (1971) gravity-viscous
oil-spreading law, inverted to estimate elapsed time from the detected
slick's observed `area_km2`.

**Important — this is an assumption-dependent estimate, not a measurement.**
A single SAR image cannot determine actual spill volume or oil type;
those are assumed (see `assumptions` block) rather than derived. Frontend
should NOT present `estimated_age_days`/`estimated_age_hours` as a bare,
confident fact — always show it alongside (or with a tooltip/info icon
linking to) the `caveat` string, which is written to be directly
user-facing.

Field reference:
- `estimated_age_hours` / `estimated_age_days` — the estimate itself.
- `assumptions` — the spill/fluid parameters the estimate depends on.
  Useful to show in an expandable "how was this calculated" section,
  not required in the main UI.
- `regime_valid` (bool) — **check this before styling the estimate as a
  confident result.** `false` means the estimated age falls outside Fay's
  gravity-viscous phase's typical validity window (~2.4 hours–10 days),
  meaning a different spreading phase would actually govern and the
  estimate is unreliable. Suggest rendering `regime_valid: false` cases
  visually de-emphasized (greyed out / smaller / with a warning icon)
  rather than in the same style as a normal confident value.
- `caveat` — pre-written, user-facing explanation string. Already
  includes the regime-validity warning text when `regime_valid` is
  `false`, so it can be displayed as-is without the frontend needing to
  construct its own caveat copy.

## Two pipeline entry points (new)

`pipeline/run_pipeline.py` now has two functions producing this same
contract shape:

- `run_pipeline()` — original synthetic-PALSAR demo path. Unchanged
  output shape/values from before this update, aside from the new
  `estimated_age` field.
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

## ~~Current mismatch to resolve~~ — RESOLVED

~~`detection/detect_spill.py` currently outputs a richer detection object
(includes `spill_id`, `source_image`, `bbox`, `perimeter_km`, `elongation`,
`fragment_count`, `confidence`, and `polygon` as a GeoJSON `Polygon` type
with `[lon, lat]` coordinate order — note the order is opposite to the
contract above, which uses `[lat, lon]`).~~

Resolved via **option 1**: `pipeline/run_pipeline.py`'s internal helpers
(`_lonlat_polygon_to_latlon`, `_build_pipeline_output`) convert
detection's richer `[lon, lat]` GeoJSON output down to this contract's
simpler `[lat, lon]` shape at the pipeline boundary. Detection's full
richer object (bbox, perimeter, elongation, fragment_count, confidence)
remains available internally for debugging/logging but is not currently
passed through to the frontend contract. Revisit if any of those extra
geometric properties turn out to be worth surfacing in the dashboard.