# OceanTrace

**AI-assisted marine oil spill detection and vessel attribution pipeline**
Built for SIH 2026 — Problem Statement #26143 (National Technical Research Organisation, NTRO)
Team Adamya

Frontend built by [Karthik](https://github.com/karthikagarwal2075-hub), integrated into this repo.

## 1. Project Overview & Purpose

OceanTrace is an automated pipeline that detects oil spills from SAR satellite imagery, reconstructs the spill's drift path backward (origin) and forward (forecast), and cross-references vessel AIS data to rank potential responsible vessels by spatio-temporal correlation. A web dashboard visualizes the full result on an interactive map.

The pipeline can run on either a synthetic demo image or a **real, real georeferenced Sentinel-1 satellite scene** — see Section 7.

## 2. High-Level Architecture

The system is structured into four sequential stages, chained by a single orchestrator:

- **Detection Layer** (`detection/`) — U-Net (ResNet18 encoder) trained on real Sentinel-1/PALSAR SAR image-mask pairs. Segments spill boundary from a SAR scene, outputs a GeoJSON-shaped polygon + geometric properties (area, perimeter, elongation). Val Dice ≈ 0.80. Can run on the synthetic demo image or on a real windowed crop of a real Sentinel-1 GRD scene, with real coordinates extracted from the scene's Ground Control Points (GCPs).
- **Drift Layer** (`drift/`) — Simulates ocean current advection (Euler integration) to hindcast the spill's origin point/time and forecast its future path.
- **AIS Attribution Layer** (`ais/`) — Reconstructs vessel traffic around the origin window, scores vessels by proximity, trajectory match, and behavioral anomaly, and ranks suspects.
- **Pipeline Orchestrator** (`pipeline/run_pipeline.py`) — Chains all three stages into one contract-shaped JSON output. Supports both the synthetic path (`run_pipeline()`) and the real-scene path (`run_pipeline_real()`), sharing identical drift/AIS logic either way.
- **Backend API** (`api/`, FastAPI) — Serves the latest pipeline result over REST for the frontend.
- **Frontend Dashboard** (`frontend/`, React + Vite + react-leaflet) — Renders the spill polygon, drift paths, and ranked vessel tracks on an interactive map.

## 3. Project Folder Structure

```
OceanTrace/
│
├── detection/
│   ├── detect_spill.py          # Standalone inference: SAR image → spill polygon (synthetic path)
│   ├── run_real_inference.py    # Windowed real-scene read + preprocessing + inference (real path)
│   ├── extract_geo.py           # Reads real lat/lon from Sentinel-1 GCPs (no affine transform on raw GRD products)
│   ├── preprocess.py
│   └── train_segmentation_dl.ipynb
│
├── drift/
│   ├── vector_field.py          # Synthetic ocean current field
│   ├── hindcast.py              # Backward advection → origin point/time
│   └── forecast.py              # Forward advection → future path
│
├── ais/
│   ├── generate_synthetic.py    # Synthetic vessel traffic generator
│   ├── filter_traffic.py
│   └── score_vessels.py         # Proximity/trajectory/anomaly scoring
│
├── pipeline/
│   └── run_pipeline.py          # Orchestrates detection → drift → AIS → contract JSON (synthetic + real entry points)
│
├── api/
│   ├── __init__.py
│   └── main.py                  # FastAPI app, serves /api/spill-result
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── MapView.jsx
│   │       └── VesselRanking.jsx
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── sar_images/              # Kaggle SAR dataset (images + masks) — used for synthetic path
│   ├── real_sar/                # Real Sentinel-1 GRD scenes downloaded from ASF (gitignored — large files)
│   └── synthetic_ais/
│
├── outputs/
│   ├── pipeline_result.json       # Latest synthetic pipeline run output
│   └── pipeline_result_real.json  # Latest real-scene pipeline run output
│
├── docs/
│   ├── contract.md              # JSON contract shared with frontend
│   └── notes.md
│
├── best_unet_spill.pth          # Trained detection model weights
├── requirements.txt
└── README.md
```

## 4. Quick Start (TL;DR)

Open two terminal windows:

**Terminal 1: Backend (FastAPI)**
```bash
cd OceanTrace
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

**Terminal 2: Frontend (React + Vite)**
```bash
cd OceanTrace/frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## 5. Detailed Setup & Execution Guide

### Prerequisites
- Python 3.12 (3.14 not recommended — known multiprocessing/reload incompatibility with uvicorn)
- Node.js 22.x + npm
- ~2GB free disk for the SAR dataset + model weights (add ~1GB more if downloading a real Sentinel-1 scene, see Section 7)

### Step 1: Backend Setup

```bash
cd OceanTrace
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the pipeline once to generate output (if `outputs/pipeline_result.json` doesn't already exist):

```bash
python -m pipeline.run_pipeline            # synthetic demo path
python -m pipeline.run_pipeline --real     # real Sentinel-1 scene path (requires a downloaded scene, see Section 7)
```

Start the API:

```bash
uvicorn api.main:app --reload --port 8000
```

Verify: open `http://127.0.0.1:8000/api/spill-result` — should return the pipeline's JSON output.

### Step 2: Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## 6. Environment / Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `API_URL` (frontend, `App.jsx`) | `http://localhost:8000/api/spill-result` | Backend endpoint the frontend fetches from |
| Synthetic demo region (fixed) | Arabian Sea, `(72.70, 19.05, 72.76, 19.10)` | Bounding box used by the synthetic path across detection/drift/AIS |
| Real scene region (derived, not fixed) | Arabian Sea, ~`(71.07–73.74 lon, 17.53–19.47 lat)` | Full real Sentinel-1 scene bounds — the real path derives its actual bbox per-run from the scene's GCPs, not a hardcoded value |

## 7. What's Real vs. Simulated

Transparency on data sources, since judges will ask:

| Module | Real | Simulated |
|---|---|---|
| Detection (synthetic path) | Model, training data (real Sentinel-1/PALSAR pairs), inference, geometry math | Georeferencing (source images have no real-world coordinates; demo location is a placeholder) |
| Detection (real path) | Model, training data, inference, geometry math, **and** the input scene itself (a real Sentinel-1 GRD scene downloaded from NASA's Alaska Satellite Facility) **and** the georeferencing (real coordinates read from the scene's Ground Control Points, not a placeholder) | — |
| Drift | Advection physics (Euler integration) | Current vector field (illustrative, not sourced from real oceanographic data) |
| AIS | Scoring logic (haversine distance, trajectory matching, anomaly detection) | Vessel identities and tracks (fabricated; one scripted "suspect" for demo clarity) — true for both the synthetic and real detection paths |

The problem statement explicitly permits synthetic AIS data "to demonstrate the functioning of the algorithm."

**Note on the real path:** the real Sentinel-1 scene used for validation is open ocean water with no confirmed real spill event. Detections produced on it demonstrate that the real-data pipeline (real scene → real preprocessing → real inference → real georeferencing) runs correctly end-to-end — they should not be presented as evidence of an actual real-world spill.

## 8. Current Implementation Status

**Backend: feature-complete.** Detection, drift, AIS, and pipeline orchestration are all implemented and tested end to end, on both the synthetic demo path and a real Sentinel-1 scene. FastAPI serves live pipeline output.

**Frontend: integrated and functional.** Map rendering, auto-fit-bounds, spill/drift/vessel visualization, and vessel selection/highlighting all confirmed working against real pipeline output.

**Not yet attempted:** spill age estimation (optional stretch goal per the problem statement); real AIS data integration (Global Fishing Watch identified as the best lead, not yet implemented).