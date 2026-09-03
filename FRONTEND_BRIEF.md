# OceanTrace — Frontend Brief

## What this project is

OceanTrace detects oil spills from satellite (SAR) imagery, simulates where
the spill drifted from (and where it's heading), then cross-references
vessel (AIS) data to rank which ship is most likely responsible.

This is for Smart India Hackathon 2026, team **Adamya**. You're building the
dashboard that visualizes all of this. The backend (Python) produces one
JSON object — you build entirely against that JSON shape. You don't need to
know or care how the JSON is generated.

## What to build

A single-page dashboard with three main pieces:

1. **Map view** — shows the detected spill as a polygon overlay, the
   backward drift path (where it likely came from), the forward drift path
   (where it's predicted to spread), and vessel tracks on top of the map.
2. **Vessel ranking panel** — a ranked list of suspect vessels (highest
   suspicion score first), each showing name, score, and a score breakdown
   (proximity / trajectory / anomaly).
3. **Timeline** (stretch goal, do this last if time allows) — a slider that
   scrubs through time so the user can watch the drift path unfold and see
   which vessels were near the origin point at that moment.

Clicking a vessel in the ranking panel should highlight its track on the map.

## Suggested stack

- React
- A map library: **Leaflet** (via `react-leaflet`) is simplest to get
  running fast. Mapbox GL is nicer visually if you want to invest more time.
- Any charting lib you like for the score breakdown (recharts, chart.js,
  or just styled bars — doesn't need to be fancy)

## The data contract

This is the exact JSON shape the backend will eventually hand you. Build
your components against this shape now, using the mock data below — when
the real pipeline is ready, you just swap the mock JSON for a real fetch
call. Nothing else should need to change.

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

Notes:
- All coordinates are `[lat, lon]`, decimal degrees.
- All timestamps are ISO 8601 UTC strings.
- `vessels` is pre-sorted by `score` descending — highest score is the top
  suspect. Show the top 5 by default with a "show more" for the rest.
- Scores are all normalized 0.0–1.0.

## Mock data to build against right now

Use this directly — it's realistic, fake data for a spill somewhere in the
Arabian Sea with 4 vessels of varying suspicion.

```json
{
  "spill": {
    "polygon": [
      [19.082, 72.710],
      [19.091, 72.734],
      [19.076, 72.751],
      [19.058, 72.739],
      [19.061, 72.715]
    ],
    "detected_at": "2026-09-08T14:00:00Z",
    "area_km2": 12.4
  },
  "drift": {
    "hindcast_path": [
      [19.070, 72.725, "2026-09-08T09:00:00Z"],
      [19.065, 72.718, "2026-09-08T10:30:00Z"],
      [19.060, 72.710, "2026-09-08T12:00:00Z"],
      [19.070, 72.725, "2026-09-08T14:00:00Z"]
    ],
    "estimated_origin": {
      "lat": 19.070,
      "lon": 72.725,
      "time": "2026-09-08T09:00:00Z"
    },
    "forecast_path": [
      [19.070, 72.725, "2026-09-08T14:00:00Z"],
      [19.080, 72.745, "2026-09-08T18:00:00Z"],
      [19.095, 72.770, "2026-09-08T22:00:00Z"],
      [19.110, 72.795, "2026-09-09T02:00:00Z"]
    ]
  },
  "vessels": [
    {
      "vessel_id": "IMO9812345",
      "name": "MV Kalindi Star",
      "score": 0.91,
      "proximity_score": 0.95,
      "trajectory_score": 0.88,
      "anomaly_score": 0.90,
      "track": [
        [19.055, 72.700, "2026-09-08T08:00:00Z"],
        [19.062, 72.712, "2026-09-08T08:45:00Z"],
        [19.070, 72.724, "2026-09-08T09:15:00Z"],
        [19.078, 72.740, "2026-09-08T10:00:00Z"]
      ]
    },
    {
      "vessel_id": "IMO9754321",
      "name": "MT Ocean Pearl",
      "score": 0.54,
      "proximity_score": 0.60,
      "trajectory_score": 0.45,
      "anomaly_score": 0.55,
      "track": [
        [19.040, 72.690, "2026-09-08T07:30:00Z"],
        [19.050, 72.705, "2026-09-08T08:30:00Z"],
        [19.058, 72.718, "2026-09-08T09:30:00Z"],
        [19.065, 72.730, "2026-09-08T10:15:00Z"]
      ]
    },
    {
      "vessel_id": "IMO9698765",
      "name": "SS Coral Voyager",
      "score": 0.32,
      "proximity_score": 0.40,
      "trajectory_score": 0.25,
      "anomaly_score": 0.30,
      "track": [
        [19.100, 72.780, "2026-09-08T09:00:00Z"],
        [19.095, 72.765, "2026-09-08T10:00:00Z"],
        [19.088, 72.750, "2026-09-08T11:00:00Z"],
        [19.080, 72.738, "2026-09-08T12:00:00Z"]
      ]
    },
    {
      "vessel_id": "IMO9631234",
      "name": "MV Sagar Ratna",
      "score": 0.12,
      "proximity_score": 0.15,
      "trajectory_score": 0.10,
      "anomaly_score": 0.10,
      "track": [
        [18.990, 72.650, "2026-09-08T06:00:00Z"],
        [19.005, 72.665, "2026-09-08T07:30:00Z"],
        [19.020, 72.680, "2026-09-08T09:00:00Z"]
      ]
    }
  ]
}
```

## Component structure (suggested, adjust as you like)

```
App.jsx                    top-level layout: map + side panel
components/
  MapView.jsx               renders spill polygon, hindcast/forecast
                             paths, and vessel tracks
  VesselRanking.jsx          ranked list, click-to-highlight on map
  Timeline.jsx               time slider (stretch goal, do last)
```

## What "done" looks like for the hackathon demo

- Map loads centered on the spill polygon
- Spill polygon is visibly shaded/outlined
- Hindcast path (dashed, one color) and forecast path (dashed, different
  color) both render
- Vessel tracks render on the map, color-coded or sized by score
- Ranking panel lists vessels sorted by score, top vessel visually
  distinguished (e.g. flagged/highlighted as "primary suspect")
- Clicking a vessel in the list highlights its track on the map

Polish (animations, the timeline slider, transitions) only after the above
works end to end with the mock data.

## When the real backend is ready

The backend team will hand you either:
- a static JSON file matching the shape above, or
- an API endpoint returning the same shape

Either way, you're just replacing the mock JSON import with a `fetch()` —
no component logic should need to change if you built against the contract
correctly.
