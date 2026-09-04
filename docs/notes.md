# OceanTrace — Project State

Satellite-based oil spill detection with AIS-based vessel attribution.
Built for Smart India Hackathon 2026 by team **Adamya**.

This doc is the single source of truth for architecture, decisions, and
current status. If you're an AI agent picking this up, read this file
fully before writing any code.

## Problem statement

ID 26143, National Technical Research Organisation (NTRO), theme Disaster
Management. Build a pipeline that:
(a) detects oil spills from satellite imagery (SAR/EO) and calculates
    geometric properties (and age, if feasible)
(b) hindcasts the slick's origin point/time and forecasts its future drift,
    using oceanographic/meteorological data
(c) attributes the spill to a vessel using historic AIS data — filters
    irrelevant traffic, scores suspect vessels on proximity, trajectory,
    and behavioral anomalies
A visual interface is required.

## Event context

- College internal hackathon, Sept 10–11. Top 50 teams (from the whole
  college) announced 3 PM Sept 10, judged on a PPT + a basic working demo.
  Top 50 stay for a 36hr hackathon.
- Team: Aniketh Cheerath (lead, backend/ML), Karthik Agarwal (frontend,
  separate repo), Rishikesh Vonteru, Uddavalu Thranoop, Akanksha Boga Ja,
  Arathi Jatoth (non-technical: data curation, PPT narrative, demo
  testing, hackathon-day logistics).

## Architecture

```
SAR image → detection/ → spill polygon (+ geometric properties)
                              ↓
                          drift/ → origin window + forecast path
                              ↓
                          ais/ → ranked suspect vessels
                              ↓
                     pipeline/run_pipeline.py → single JSON
                              ↓
                        frontend/ (separate repo, dashboard)
```

## What's real vs. simulated (by design, for demo purposes)

- **Detection** — REAL. Trained U-Net on actual Sentinel-1/PALSAR SAR
  imagery. See "Detection — status" below.
- **Drift (hindcast/forecast)** — SIMULATED. Simplified vector field, not
  live oceanographic/meteorological data.
- **AIS attribution** — SIMULATED. Synthetic vessel tracks, since no real
  AIS is matched to a real spill event.

Be upfront about this split in the pitch — it's a deliberate scoping
decision given the timeline, not a shortcut to hide.

## Fixed demo region (important — keep consistent across all modules)

All modules must use this same bounding box so the map, drift path, and
vessel tracks visually line up:

```
min_lon, min_lat, max_lon, max_lat = 72.70, 19.05, 72.76, 19.10
```
(Arabian Sea, near Mumbai — arbitrary choice, just needs to stay fixed.)

## Detection — status: DONE

- Dataset: `bakhtiyar2222/deep-sar-oil-spill-segmentation-refined` on
  Kaggle — 6455 train / 1615 val image-mask pairs, 256×256, sentinel +
  palsar sources.
- Masks aren't clean binary (antialiasing noise at edges) — remapped to
  binary at threshold 128.
- Model: U-Net (`segmentation_models_pytorch`), ResNet18 encoder
  (ImageNet pretrained), Dice loss, Adam @ lr=1e-4. Trained on Colab T4.
- Result: val_dice ~0.79–0.80 after 2 epochs (was still improving).
  Checkpoint: `best_unet_spill.pth`.
- Wrapped into `detection/detect_spill.py` — runs standalone locally
  (no Colab needed), confirmed working end to end: loads model, runs
  inference on a local SAR image, outputs valid GeoJSON-shaped detection
  with area, perimeter, elongation, fragment count, confidence.
- Sample local test images live in `data/sar_images/images/` (+ matching
  ground truth in `data/sar_images/masks/`), pulled manually from the
  Kaggle dataset's web file browser (not via API).
- Known fix applied: `cv2.fitEllipse` doesn't guarantee (major, minor)
  order — always do `major, minor = max(d1,d2), min(d1,d2)` before
  computing elongation, or you'll get elongation < 1 which is invalid.

## Drift — status: NOT STARTED

Needs: `drift/vector_field.py` (simplified wind/current vector field for
the fixed demo region), `drift/hindcast.py` (backward-advect the spill
polygon to estimate origin point/time), `drift/forecast.py` (forward-
advect to predict future spread). Simulated data is fine — doesn't need
to be scientifically rigorous, just plausible for a demo.

## AIS — status: NOT STARTED

Needs: `ais/generate_synthetic.py` (fake vessel tracks around the
estimated origin window — include a few "innocent" vessels and one clear
"suspect" so the demo has an obvious answer), `ais/filter_traffic.py`
(drop vessels outside the relevant space/time window), `ais/score_vessels.py`
(rank by combined proximity + trajectory + anomaly score).

## Pipeline — status: NOT STARTED

`pipeline/run_pipeline.py` should import and call detection → drift → ais
in sequence, and output one JSON matching the shape in `contract.md`.

## Frontend — status: in progress, separate repo

Karthik is building this independently against `contract.md`'s mock data,
using a standalone `FRONTEND_BRIEF.md` handed to him earlier (not
duplicated here — that doc is self-contained). Stack: React + Leaflet.
Components: `MapView.jsx`, `VesselRanking.jsx`, `Timeline.jsx` (stretch).

## Repo structure

```
ais/            filter_traffic.py, generate_synthetic.py, score_vessels.py
data/           sar_images/{images,masks}/, ais_samples/, synthetic_ais/
                (gitignored)
detection/      detect_spill.py (done), preprocess.py, train_segmentation_dl.ipynb
                test_detection.ipynb (classical CV fallback, likely unused now)
docs/           NOTES.md (this file), contract.md
drift/          forecast.py, hindcast.py, vector_field.py (all empty/unstarted)
frontend/       separate repo — not in this tree
outputs/        gitignored, generated demo outputs
pipeline/       run_pipeline.py (empty/unstarted)
best_unet_spill.pth   trained model checkpoint (should be gitignored — add
                       *.pth to .gitignore if not already)
README.md, requirements.txt, .gitignore
```

## Environment

- Local dev: Fedora, Python venv at repo root (`venv/`)
- `requirements.txt` includes: numpy, opencv-python, Pillow, matplotlib,
  scikit-image, geopandas, shapely, folium, pandas, rasterio, torch,
  torchvision, segmentation-models-pytorch, albumentations, tqdm
- No GPU locally — inference runs on CPU via `detect_spill.py`'s automatic
  `torch.cuda.is_available()` fallback. Training happened on Colab (T4 GPU).

## Phases

- **Phase 0** (done): planning, repo scaffold, dataset sourcing, detection
  model trained and validated
- **Phase 1** (in progress): drift + AIS modules
- **Phase 2**: pipeline orchestration + frontend integration
- **Phase 3**: polish, PPT, rehearse pitch

## Decisions log

- Chose real trained model (U-Net) over classical CV once a clean,
  pre-paired Kaggle dataset was found — classical CV was the original
  fallback plan but abandoned since training converged fast and well.
- Fixed Arabian Sea bounds chosen to keep detection/drift/AIS/frontend
  visually consistent in the demo, since none of the underlying data is
  real anyway