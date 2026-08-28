# OceanTrace — Architecture Notes

## What's real vs. simulated
- **Detection**: REAL — classical CV (Otsu thresholding + morphological ops)
  on actual Sentinel-1 SAR images from Zenodo. No trained model (out of scope
  for this timeline).
- **Drift (hindcast/forecast)**: SIMULATED — simplified vector field, not
  live oceanographic/meteorological data. Good enough to show a plausible
  backward/forward path.
- **AIS attribution**: SIMULATED — synthetic vessel tracks generated around
  the estimated origin window, since we don't have real AIS data matched to
  a real spill event.

## Module boundaries
- `detection/` → outputs a spill polygon (lat/lon coords) + geo-bounds from
  one SAR image.
- `drift/` → takes the spill polygon + timestamp, outputs a backward path
  (estimated origin point/time) and forward path (predicted spread).
- `ais/` → takes the origin point/time window, outputs a ranked list of
  vessels with scores (proximity, trajectory match, behavioral anomaly).
- `pipeline/run_pipeline.py` → orchestrates all three, outputs one JSON
  (see contract.md) for the frontend.

## Decisions log
- Aug 28: chose classical thresholding over training a model — faster,
  lower risk, works on real images today.
- Aug 28: repo name OceanTrace, team name Adamya.