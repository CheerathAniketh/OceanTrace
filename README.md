# OceanTrace

Satellite-based oil spill detection with AIS-based vessel attribution.

Built for Smart India Hackathon 2026 by team **Adamya**.

## Problem Statement

**ID 26143** — Leveraging satellite imagery to determine oil spills at sea,
along with AIS data correlations to identify the vessel responsible for the spill.

**Organization:** National Technical Research Organisation (NTRO)
**Theme:** Disaster Management

Marine oil spills damage ecosystems and are often never attributed to the
responsible vessel. This project detects spills from satellite imagery,
traces the slick back to its origin in space and time, and cross-references
historic AIS vessel traffic to rank potential culprit vessels.

## What it does

1. **Detects** oil spills from Sentinel-1 SAR satellite imagery
2. **Hindcasts** the slick backward to estimate origin point and time, and
   **forecasts** its future drift
3. **Attributes** the spill by scoring nearby vessels from AIS data on
   proximity, trajectory match, and behavioral anomalies
4. **Visualizes** the whole pipeline — spill polygon, drift path, and ranked
   suspect vessels — on an interactive map dashboard

## What's real vs. simulated

- **Detection** — real, using classical CV (Otsu thresholding + morphological
  ops) on actual Sentinel-1 SAR images
- **Drift simulation** — simplified vector field, not live oceanographic data
- **AIS attribution** — synthetic vessel tracks, since no real AIS is matched
  to a real spill event

Full breakdown in [`docs/NOTES.md`](docs/NOTES.md).

## Architecture

```
SAR image → detection/ → spill polygon
                              ↓
                          drift/ → origin window + forecast path
                              ↓
                          ais/ → ranked suspect vessels
                              ↓
                     pipeline/run_pipeline.py → JSON
                              ↓
                        frontend/ (dashboard)
```

See [`docs/contract.md`](docs/contract.md) for the exact JSON output shape
shared between backend and frontend.

## Repo structure

```
detection/    spill detection from SAR imagery
drift/        backward/forward drift simulation
ais/          synthetic AIS generation + vessel scoring
pipeline/     orchestrates the three modules into one output
frontend/     dashboard (map, vessel ranking, timeline)
docs/         architecture notes and pipeline contract
data/         gitignored — raw SAR images and AIS samples
outputs/      gitignored — generated demo outputs
```

## Setup

```bash
# backend
pip install -r requirements.txt

# frontend
cd frontend
npm install
npm run dev
```

## Team — Adamya

- Aniketh Cheerath — lead, detection / drift / AIS pipeline
- Karthik Agarwal — frontend dashboard
- Rishikesh Vonteru
- Uddavalu Thranoop
- Akanksha Boga
- Arathi Jatoth

## Data sources

- [Sentinel-1 SAR Oil Spill Dataset (Zenodo)](https://zenodo.org)
- [AIS sample data (marinecadastre.gov)](https://marinecadastre.gov/accessais/)