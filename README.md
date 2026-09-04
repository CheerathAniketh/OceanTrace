# OceanTrace

**AI-assisted marine oil spill detection and vessel attribution pipeline**
Built for SIH 2026 — Problem Statement #26143 (National Technical Research Organisation, NTRO)
Team Adamya

## 1. Project Overview & Purpose

OceanTrace is an automated pipeline that detects oil spills from SAR satellite imagery, reconstructs the spill's drift path backward (origin) and forward (forecast), and cross-references vessel AIS data to rank potential responsible vessels by spatio-temporal correlation. A web dashboard visualizes the full result on an interactive map.

## 2. High-Level Architecture

The system is structured into four sequential stages, chained by a single orchestrator:

- **Detection Layer** (`detection/`) — U-Net (ResNet18 encoder) trained on real Sentinel-1/PALSAR SAR image-mask pairs. Segments spill boundary from a SAR scene, outputs a GeoJSON-shaped polygon + geometric properties (area, perimeter, elongation). Val Dice ≈ 0.80.
- **Drift Layer** (`drift/`) — Simulates ocean current advection (Euler integration) to hindcast the spill's origin point/time and forecast its future path.
- **AIS Attribution Layer** (`ais/`) — Reconstructs vessel traffic around the origin window, scores vessels by proximity, trajectory match, and behavioral anomaly, and ranks suspects.
- **Pipeline Orchestrator** (`pipeline/run_pipeline.py`) — Chains all three stages into one contract-shaped JSON output.
- **Backend API** (`api/`, FastAPI) — Serves the latest pipeline result over REST for the frontend.
- **Frontend Dashboard** (`frontend/`, React + Vite + react-leaflet) — Renders the spill polygon, drift paths, and ranked vessel tracks on an interactive map.

## 3. Project Folder Structure
OceanTrace/
│
├── detection/
│ ├── detect_spill.py # Standalone inference: SAR image → spill polygon
│ ├── preprocess.py
│ └── train_segmentation_dl.ipynb
│
├── drift/
│ ├── vector_field.py # Synthetic ocean current field
│ ├── hindcast.py # Backward advection → origin point/time
│ └── forecast.py # Forward advection → future path
│
├── ais/
│ ├── generate_synthetic.py # Synthetic vessel traffic generator
│ ├── filter_traffic.py
│ └── score_vessels.py # Proximity/trajectory/anomaly scoring
│
├── pipeline/
│ └── run_pipeline.py # Orchestrates detection → drift → AIS → contract JSON
│
├── api/
│ ├── init.py
│ └── main.py # FastAPI app, serves /api/spill-result
│
├── frontend/
│ ├── src/
│ │ ├── App.jsx
│ │ └── components/
│ │ ├── MapView.jsx
│ │ └── VesselRanking.jsx
│ ├── package.json
│ └── vite.config.js
│
├── data/
│ ├── sar_images/ # Kaggle SAR dataset (images + masks)
│ └── synthetic_ais/
│
├── outputs/
│ └── pipeline_result.json # Latest pipeline run output
│
├── docs/
│ ├── contract.md # JSON contract shared with frontend
│ └── notes.md
│
├── best_unet_spill.pth # Trained detection model weights
├── requirements.txt
└── README.md


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
- ~2GB free disk for the SAR dataset + model weights

### Step 1: Backend Setup

```bash
cd OceanTrace
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the pipeline once to generate output (if `outputs/pipeline_result.json` doesn't already exist):

```bash
python pipeline/run_pipeline.py
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
| Demo region (fixed, all modules) | Arabian Sea, `(72.70, 19.05, 72.76, 19.10)` | Bounding box used across detection/drift/AIS for the demo scenario |

## 7. What's Real vs. Simulated

Transparency on data sources, since judges will ask:

| Module | Real | Simulated |
|---|---|---|
| Detection | Model, training data (real Sentinel-1/PALSAR pairs), inference, geometry math | Georeferencing (source images have no real-world coordinates; demo location is a placeholder) |
| Drift | Advection physics (Euler integration) | Current vector field (illustrative, not sourced from real oceanographic data) |
| AIS | Scoring logic (haversine distance, trajectory matching, anomaly detection) | Vessel identities and tracks (fabricated; one scripted "suspect" for demo clarity) |

The problem statement explicitly permits synthetic AIS data "to demonstrate the functioning of the algorithm."

## 8. Current Implementation Status

**Backend: feature-complete.** Detection, drift, AIS, and pipeline orchestration are all implemented and tested end to end. FastAPI serves live pipeline output.

**Frontend: integrated and functional.** Map rendering, auto-fit-bounds, spill/drift/vessel visualization, and vessel selection/highlighting all confirmed working against real pipeline output.

**Not yet attempted:** spill age estimation (optional stretch goal per the problem statement).