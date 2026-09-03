# OceanTrace — Data Contract

All modules communicate via JSON. Timestamps: ISO 8601 UTC. Coords: [lon, lat] (GeoJSON order, not lat/lon).

## 1. detection/ output → SpillDetection
{
  "spill_id": "spill_001",
  "source_image": "sar_20260828_0143.tif",
  "detected_at": "2026-08-28T01:43:00Z",       // image acquisition time
  "polygon": {                                  // GeoJSON Polygon
    "type": "Polygon",
    "coordinates": [[[lon, lat], [lon, lat], ...]]
  },
  "bbox": [minLon, minLat, maxLon, maxLat],
  "area_km2": 12.4,
  "perimeter_km": 18.1,
  "elongation": 3.2,          // ellipse aspect ratio
  "fragment_count": 1,
  "confidence": 0.71          // even for classical CV, report something — e.g. contrast ratio
}

## 2. drift/ output → DriftResult
{
  "spill_id": "spill_001",
  "origin_estimate": {
    "point": [lon, lat],
    "time": "2026-08-27T14:00:00Z",
    "uncertainty_radius_km": 5.0    // be honest, this matters for AIS filtering
  },
  "backward_path": [ {"time": "...", "point": [lon, lat]}, ... ],
  "forward_path":  [ {"time": "...", "point": [lon, lat]}, ... ]
}

## 3. ais/ output → VesselRanking
{
  "spill_id": "spill_001",
  "window": { "start": "...", "end": "...", "center": [lon, lat], "radius_km": 5.0 },
  "candidates": [
    {
      "mmsi": "123456789",
      "vessel_name": "MV Example",
      "vessel_type": "tanker",
      "score": 0.83,
      "score_breakdown": {
        "proximity": 0.9,
        "trajectory_match": 0.8,
        "behavioral_anomaly": 0.7   // e.g. AIS gap flag
      },
      "track": [ {"time": "...", "point": [lon, lat], "speed": 12.4, "heading": 210} ],
      "flags": ["ais_gap_before_window"]
    }
  ]
}

## 4. pipeline/run_pipeline.py final output
{
  "spill": <SpillDetection>,
  "drift": <DriftResult>,
  "ranking": <VesselRanking>,
  "generated_at": "..."
}