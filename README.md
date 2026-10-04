# OceanTrace
**Automated Marine Oil Spill Detection & Vessel Attribution**

Detect oil spills from satellite imagery, hindcast their origin, and identify responsible vessels through AIS cross-reference. Started as a Smart India Hackathon 2026 entry (National Technical Research Organisation problem statement #26143).

---

## Problem
Marine oil spills are environmental disasters. Current response is reactive—spills are spotted days after they occur. By then, the source has dispersed and responsible parties are hard to trace. Environmental agencies need rapid detection, drift forecasting, and vessel attribution to enforce accountability.

## Approach
OceanTrace automates the entire pipeline end-to-end:

1. **Detects** oil spills from Sentinel-1 SAR satellite imagery using a trained deep learning model (Dice: 0.826)
2. **Hindcasts** drift using ocean current simulation to pinpoint spill origin
3. **Attributes** responsible vessel by cross-referencing AIS (Automatic Identification System) data
4. **Visualizes** full incident on an interactive map dashboard (React + Leaflet)

All three layers work on either synthetic demo data or real Sentinel-1 satellite scenes for end-to-end validation.

---

## Results
- ✅ **Detection model** — Dice: 0.826, IoU: 0.731 (trained on 6,455 real Sentinel-1/PALSAR image-mask pairs)
- ✅ **Real-data pipeline** — run end to end on a real Sentinel-1 GRD scene from NASA ASF
- ✅ **End-to-end** — detection + drift hindcast + AIS attribution working on both synthetic and real data
- ✅ **Interactive dashboard** — map rendering, auto-fit-bounds, vessel ranking, spill visualization

---

## Tech Stack
**Detection:** PyTorch (U-Net, ResNet18 encoder) · CUDA training  
**Satellite Data:** Sentinel-1 GRD (NASA ASF) · Rasterio (georeferencing)  
**Drift Simulation:** NumPy (Euler integration, ocean current advection)  
**Backend:** FastAPI · Uvicorn  
**Frontend:** React + Vite · Leaflet.js (map visualization)  
**Geospatial:** Shapely (polygon geometry) · Rasterio (real GCP reading)

---

## Quick Start
```bash
# Backend setup
git clone https://github.com/CheerathAniketh/OceanTrace
cd OceanTrace
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Generate pipeline output (synthetic demo)
python -m pipeline.run_pipeline

# Start API
uvicorn api.main:app --reload --port 8000
# Visit http://localhost:8000/api/spill-result

# Frontend setup
cd frontend
npm install
npm run dev
# Visit http://localhost:5173
```

> **Not included in the repo:** the trained weights (`best_unet_spill.pth`) and all SAR data are gitignored because of their size. To reproduce the weights, train with `detection/train_segmentation_dl_ipynb.ipynb` on the Kaggle SAR image-mask dataset and place the file in the repo root. The detection step does not run without it.

---

## API Endpoints

### Get Latest Spill Result
```bash
curl http://localhost:8000/api/spill-result
```
**Response:**
```json
{
  "spill_id": "spill_20260915_001",
  "detection": {
    "area_sqkm": 42.3,
    "confidence": 0.94,
    "polygon": [[lat1, lon1], [lat2, lon2], ...],
    "timestamp": "2026-09-15T12:34:56Z"
  },
  "drift": {
    "origin": {"lat": 10.342, "lon": 72.156, "time_hours_ago": 18},
    "forecast": [
      {"lat": 10.350, "lon": 72.165, "time_hours_ahead": 6},
      {"lat": 10.358, "lon": 72.174, "time_hours_ahead": 12}
    ]
  },
  "attribution": {
    "suspect_vessels": [
      {
        "mmsi": 123456789,
        "vessel_name": "Oil Tanker Alpha",
        "flag": "LR",
        "rank": 1,
        "confidence": 0.87,
        "reason": "Proximity + heading alignment"
      },
      ...
    ]
  }
}
```

### Get Result by Mode
```bash
curl http://localhost:8000/api/spill-result?mode=synthetic  # Demo data
curl http://localhost:8000/api/spill-result?mode=real       # Real Sentinel-1 scene
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

---

## System Architecture
```
Sentinel-1 SAR Image (Real or Synthetic)
        ↓
┌─────────────────────────────────────┐
│  DETECTION LAYER                    │
│  PyTorch U-Net (ResNet18 encoder)   │
│  → Spill polygon + geometry          │
│  → Min area/confidence gate          │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  DRIFT LAYER                        │
│  Euler advection (ocean currents)   │
│  → Hindcast origin (when/where)     │
│  → Forecast future path              │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  AIS ATTRIBUTION LAYER              │
│  Proximity + trajectory + anomaly    │
│  scoring → ranked vessel suspects    │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  VISUALIZATION LAYER                │
│  FastAPI backend + React/Leaflet    │
│  → Interactive spill/drift/vessel    │
│  → Served over REST                  │
└─────────────────────────────────────┘
```

---

## Model Performance
Trained on 6,455 training / 1,615 validation samples of real Sentinel-1 and PALSAR SAR imagery.

| Metric | Best Value | Epoch |
|--------|-----------|-------|
| **Validation Dice** | **0.8265** | 12/15 |
| **Validation IoU** | **0.7309** | 12/15 |

Checkpoint selected by validation Dice (not final epoch). Inference validated against:
- Real Sentinel-1 GRD scenes (NASA ASF)
- Synthetic demo dataset (Kaggle SAR image-mask pairs)

---

## What's Real vs. Synthetic (Transparency)
The SIH problem statement explicitly permits synthetic AIS data to demonstrate algorithmic functionality.

| Module | Real | Simulated |
|---|---|---|
| Detection model & training | Model, real Sentinel-1/PALSAR training pairs, inference, geometry math | — |
| Detection (synthetic path) | Model, inference, minimum area/confidence gate | Georeferencing (fixed placeholder region) |
| Detection (real path) | Model, inference, gate, the input scene (Sentinel-1 GRD from NASA ASF), and georeferencing from the scene's Ground Control Points | — |
| Drift | Advection physics (Euler integration) | Current vector field (illustrative, not from a live oceanographic feed) |
| AIS | Scoring logic (haversine, trajectory, anomaly); heading/speed-based traffic scene (8 vessels) | Vessel identities and tracks (fabricated; one scripted "suspect" for demo clarity) |

**Key note:** The Sentinel-1 scene used for real-path validation contains no confirmed real spill event. Detections demonstrate end-to-end real-data pipeline correctness, not evidence of an actual spill.

---

## Key Features
### Synthetic Demo Path
Fast, reproducible. Uses Kaggle SAR image-mask pairs. Good for rapid iteration and testing.

### Real Sentinel-1 Path
Reads real geospatial data from NASA ASF, parses Ground Control Points for precise georeferencing, validates the full pipeline against production-grade satellite imagery.

### Drift Hindcasting
Rewind the ocean currents to find where the spill originated. Forecast forward to predict spread.

### Vessel Scoring
Multi-criteria ranking:
- **Proximity** — vessel distance to estimated origin
- **Trajectory** — heading alignment with spill spread direction
- **Anomaly** — unusual course/speed changes near spill time

---

## Validation
- ✅ Detection model trained and validated on real SAR data (Dice: 0.826)
- ✅ Real Sentinel-1 inference tested end-to-end (georeferencing + detection verified)
- ✅ Drift simulation implemented with Euler integration over an illustrative current field (not validated against real oceanographic data)
- ✅ AIS scoring logic tested on synthetic realistic vessel traffic (8 vessels, real heading/speed patterns)
- ✅ Frontend rendering verified against real pipeline JSON output (React + Leaflet rendering live data)

---

## Testing
```bash
# Run synthetic pipeline
python -m pipeline.run_pipeline
# Output: outputs/pipeline_result.json

# Run real Sentinel-1 pipeline (if scene downloaded)
python -m pipeline.run_pipeline --real
# Output: outputs/pipeline_result_real.json

# Check API
curl http://localhost:8000/api/health
curl http://localhost:8000/api/spill-result
curl http://localhost:8000/api/spill-result?mode=real
```

---

## Project Structure
```
OceanTrace/
├── detection/            # PyTorch U-Net model + inference
│   ├── detect_spill.py
│   ├── run_real_inference.py
│   ├── extract_geo.py
│   └── train_segmentation_dl_ipynb.ipynb
├── drift/                # Ocean current simulation
│   ├── vector_field.py
│   ├── hindcast.py
│   └── forecast.py
├── ais/                  # Vessel attribution
│   ├── generate_synthetic.py
│   └── score_vessels.py
├── pipeline/             # Orchestration
│   └── run_pipeline.py
├── api/                  # FastAPI backend
│   └── main.py
├── frontend/             # React + Leaflet
│   ├── src/App.jsx
│   └── package.json
└── data/
    ├── sar_images/       # Kaggle SAR pairs (synthetic path)
    └── real_sar/         # Real Sentinel-1 scenes (real path)
```

See [docs/contract.md](./docs/contract.md) for the JSON contract between the pipeline and the frontend.

---

## Future Scope
- Real AIS data integration (Global Fishing Watch API)
- Spill age estimation via spreading law (Fay 1971, implemented but not wired)
- Live oceanographic current data (vs. synthetic field)
- Multi-spill scenarios (simultaneous incidents)

---

## Team
**Aniketh Cheerath** — Pipeline, detection model, backend (FastAPI, drift, AIS)  
**Karthik Agarwal** — Frontend (React, Leaflet, UI/UX)

**Team Adamya** — SIH 2026 submission

---

## Links
- **GitHub:** github.com/CheerathAniketh/OceanTrace
- **SIH 2026:** Smart India Hackathon (NTRO problem statement #26143)
- **LinkedIn:** linkedin.com/in/cheerathaniketh

---

## References
- Fay, J. A. (1971). Physical processes in the spread of oil on ocean surface.
- NASA ASF — Sentinel-1 data archive
- Kaggle SAR image-mask dataset
