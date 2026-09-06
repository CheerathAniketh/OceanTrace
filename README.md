# 🌊 OceanTrace

### AI-Assisted Marine Oil Spill Detection & Vessel Attribution Pipeline

**Built for SIH 2026 — Problem Statement #26143 (National Technical Research Organisation, NTRO)**
**Team Adamya**

`Python` `PyTorch` `FastAPI` `React` `Leaflet` `Sentinel-1 SAR`

Frontend built by [Karthik](https://github.com/karthikagarwal2075-hub), integrated into this repo.

---

## 1. Problem Statement

Detecting a marine oil spill after the fact isn't enough — investigators also need to know **where it came from** and **who's responsible**. Manually reconstructing a spill's drift path and cross-referencing vessel traffic is slow, while oil spreads and evidence degrades in the meantime.

## 2. Our Solution

OceanTrace is an automated pipeline that:

1. **Detects** oil spills directly from SAR (Synthetic Aperture Radar) satellite imagery using a trained deep learning model
2. **Reconstructs drift** — simulates ocean current advection to hindcast the spill's origin and forecast its future spread
3. **Attributes vessels** — cross-references AIS (ship-tracking) data near the estimated origin and ranks the most likely responsible vessel
4. **Visualizes** the full result — spill outline, drift paths, and ranked suspects — on an interactive map dashboard

The pipeline runs on either a **synthetic demo image** or a **real, georeferenced Sentinel-1 satellite scene** — see [Section 7](#7-whats-real-vs-simulated).

## 3. System Architecture

```
SAR Satellite Image
        ↓
┌───────────────────┐
│  DETECTION LAYER   │  U-Net (ResNet18 encoder) → spill polygon + geometry
└───────────────────┘
        ↓
┌───────────────────┐
│   DRIFT LAYER      │  Euler advection → origin (hindcast) + forecast
└───────────────────┘
        ↓
┌───────────────────┐
│ AIS ATTRIBUTION    │  Proximity / trajectory / anomaly scoring → ranked vessels
└───────────────────┘
        ↓
┌───────────────────┐
│  PIPELINE ORCHESTRATOR │  Assembles contract-shaped JSON
└───────────────────┘
        ↓
┌───────────────────┐
│  BACKEND API (FastAPI) │  Serves latest result over REST
└───────────────────┘
        ↓
┌───────────────────┐
│ FRONTEND DASHBOARD │  React + Leaflet map visualization
└───────────────────┘
```

## 4. Tech Stack

| Category | Technology | Usage & Purpose |
|---|---|---|
| Detection Model | PyTorch (U-Net, ResNet18 encoder) | Segments spill boundary from SAR imagery |
| Backend Framework | FastAPI | Serves pipeline output over REST |
| ASGI Server | Uvicorn | Async server runtime with hot reload |
| Geospatial | Shapely, Rasterio | Polygon geometry, real Sentinel-1 GCP reading |
| Drift Simulation | NumPy | Euler integration for current advection |
| Frontend Framework | React + Vite | Dashboard UI |
| Map Rendering | react-leaflet (Leaflet.js) | Interactive spill/drift/vessel map |
| Satellite Data | Sentinel-1 GRD (via NASA ASF) | Real SAR scene for real-path validation |
| Training Data | Kaggle SAR/PALSAR image-mask pairs | Model training + synthetic demo path |

## 5. Project Structure

```
OceanTrace/
│
├── detection/
│   ├── detect_spill.py              # Standalone inference: SAR image → spill polygon (synthetic path)
│   ├── run_real_inference.py        # Windowed real-scene read + preprocessing + inference (real path)
│   ├── extract_geo.py               # Reads real lat/lon from Sentinel-1 GCPs
│   ├── estimate_age.py              # Fay (1971) spreading-law age estimator — implemented, not yet wired into the pipeline (future scope)
│   ├── train_segmentation_dl_ipynb.ipynb   # Model training notebook
│   └── test_detection.ipynb
│
├── drift/
│   ├── vector_field.py              # Synthetic ocean current field
│   ├── hindcast.py                  # Backward advection → origin point/time
│   └── forecast.py                  # Forward advection → future path
│
├── ais/
│   ├── generate_synthetic.py        # Synthetic vessel traffic generator
│   └── score_vessels.py             # Proximity/trajectory/anomaly scoring
│
├── pipeline/
│   └── run_pipeline.py              # Orchestrates detection → drift → AIS → contract JSON
│
├── api/
│   ├── __init__.py
│   └── main.py                      # FastAPI app, serves /api/spill-result (synthetic + real modes)
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
│   ├── sar_images/                  # Kaggle SAR dataset (images + masks) — synthetic path
│   ├── real_sar/                    # Real Sentinel-1 GRD scenes from ASF (gitignored — large files)
│   └── synthetic_ais/
│
├── outputs/
│   ├── pipeline_result.json         # Latest synthetic pipeline run output (gitignored, regenerable)
│   └── pipeline_result_real.json    # Latest real-scene pipeline run output (gitignored, regenerable)
│
├── docs/
│   ├── contract.md                  # JSON contract shared with frontend
│   └── notes.md
│
├── best_unet_spill.pth              # Trained detection model weights (gitignored — large file)
├── requirements.txt
└── README.md
```

## 6. Quickstart & Execution Guide

### Prerequisites
- Python 3.12 (3.14 not recommended — known multiprocessing/reload incompatibility with uvicorn)
- Node.js 22.x + npm
- ~2GB free disk for the SAR dataset + model weights (add ~1GB more for a real Sentinel-1 scene)

### 1. Backend Setup

```bash
cd OceanTrace
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Generate pipeline output (dynamically timestamped to the current time on every run):

```bash
python -m pipeline.run_pipeline            # synthetic demo path
python -m pipeline.run_pipeline --real     # real Sentinel-1 scene path (requires a downloaded scene)
```

Start the API:

```bash
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

## 7. Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/spill-result` | Latest pipeline result (synthetic by default) |
| GET | `/api/spill-result?mode=real` | Latest result from the real Sentinel-1 path |
| GET | `/api/spill-result?mode=synthetic` | Latest result from the synthetic demo path |
| GET | `/api/health` | Health check — reports which result files are available |

## 8. What's Real vs. Simulated

Transparency on data sources, since judges will ask:

| Module | Real | Simulated |
|---|---|---|
| Detection model & training | Model, real Sentinel-1/PALSAR training pairs, inference, geometry math | — |
| Detection (synthetic path) | Model, inference | Georeferencing (fixed placeholder region) |
| Detection (real path) | Model, inference, **the input scene itself** (real Sentinel-1 GRD scene from NASA's ASF), **and georeferencing** (coordinates read from the scene's Ground Control Points) | — |
| Drift | Advection physics (Euler integration) | Current vector field (illustrative, not from a live oceanographic feed) |
| AIS | Scoring logic (haversine distance, trajectory matching, anomaly detection) | Vessel identities and tracks (fabricated; one scripted "suspect" for demo clarity) |

The problem statement explicitly permits synthetic AIS data **"to demonstrate the functioning of the algorithm."**

> **Note on the real path:** the real Sentinel-1 scene used for validation is open ocean water with no confirmed real spill event. Detections on it demonstrate that the real-data pipeline (real scene → real preprocessing → real inference → real georeferencing) runs correctly end-to-end — they should not be presented as evidence of an actual real-world spill.

## 9. Model Performance

Trained on 6,455 train / 1,615 validation samples (real Sentinel-1/PALSAR SAR image-mask pairs) for 15 epochs (~21 min on GPU).

| Metric | Best Value | Epoch |
|---|---|---|
| Validation Dice | **0.8265** | 12/15 |
| Validation IoU | 0.7309 | 12/15 |

Best checkpoint (by validation Dice, not final epoch) saved as `best_unet_spill.pth`.

## 10. Current Implementation Status

**Backend:** feature-complete. Detection, drift, AIS, and pipeline orchestration are implemented and tested end to end, on both the synthetic demo path and a real Sentinel-1 scene. The API supports serving either result via a `mode` query parameter, and returns clean structured errors (not raw crashes) when a result file is unavailable.

**Frontend:** integrated and functional. Map rendering, auto-fit-bounds, spill/drift/vessel visualization, and vessel selection/highlighting confirmed working against real pipeline output.

**Not yet wired into the live demo (future scope):**
- Spill age estimation — implemented (`detection/estimate_age.py`, Fay 1971 gravity-viscous spreading law) but not connected to the pipeline/contract/UI
- Real AIS data integration — Global Fishing Watch identified as the best lead, not yet implemented