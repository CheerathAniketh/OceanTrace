# OceanTrace — Dev Log: 2026-08-28

## Summary
First real work session. Repo scaffolding already existed (folders + a few
docs). Today: locked the inter-module data contract, decided on the DL vs.
classical detection strategy, and started the segmentation training
pipeline in Colab. No training run completed yet — still in dataset
inspection phase.

## Decisions made
- **Detection strategy**: keep classical CV (Otsu thresholding + morph ops)
  as the reliable fallback/baseline. Build a DL segmentation model
  alongside it, not instead of it. Pipeline can flag-switch between them.
- **DL detection is multiclass**, not binary — matches the 5-class framing
  (sea surface, oil spill, look-alike, ship, land) and is more defensible
  to judges than collapsing to binary.
- **DL/ML ownership**: solo-owned (me). Rest of team (AIS, drift, frontend)
  stays unblocked by working against the JSON contract + stub/synthetic
  data, not waiting on the trained model.
- **Compute**: training on Google Colab (free T4), not the teammate's
  4050 laptop — more VRAM, zero local setup, easier to co-view.
- **Data contract locked** (see `docs/contract.md`): SpillDetection,
  DriftResult, VesselRanking, and the final pipeline JSON shape. Fixed on
  GeoJSON `[lon, lat]` coordinate order everywhere. Flagged
  `uncertainty_radius_km` in DriftResult as the field AIS filtering depends
  on — must not get dropped.

## Dataset search (detection training data)
- Tried `sudhanshu2198/oil-spill-detection` (Kaggle) → wrong dataset,
  it's binary **classification** (Class_0/Class_1 folders, plain jpgs, no
  masks). Not usable for segmentation.
- Tried `harikrishnacs/sentinel-1-sar-oil-spill-detection-dataset` → same
  problem, also binary classification only, no masks.
- **Landed on `bakhtiyar2222/deep-sar-oil-spill-segmentation-refined`**
  (~1.1GB) → this is the right one. Clean structure:
  `images/images/{train,val}/` and `masks/masks/{train,val}/` with matching
  filenames (`palsar_291.png` etc). PALSAR + Sentinel-1A images, confirms
  this is the Deep-SAR (SOS) dataset. **6,455 train masks** found.

## Current blocker
Mask format turned out to be messier than expected:
- Masks are `RGB` mode but R=G=B (so really grayscale info stored in 3
  channels).
- Single-file check showed 115 unique values, not a clean 5 — looks like
  anti-aliasing/compression noise around a small number of true class
  anchor values, with `0` dominant and other values roughly spaced near
  multiples of ~51 (i.e. ~255/5).
- Started aggregating value counts across 200 masks to find the real
  recurring anchor values before writing the class-index remapping.
- **Hit a bug mid-check**: assumed all mask files are RGB `(H,W,3)` and
  indexed `[:,:,0]` — some masks in the sample are actually 2D grayscale
  `(H,W)` already (no channel dim), so indexing failed with
  `IndexError: too many indices for array: array is 2-dimensional`.
  **Not yet fixed.** Need to branch on `arr.ndim` before indexing.

## Next session — pick up here
1. Fix the `os.walk`/aggregation script to handle both 2D and 3D masks
   (check `arr.ndim`, only index `[:,:,0]` if `ndim == 3`).
2. Re-run the 200-mask aggregation to find true class anchor values.
3. Write the snap-to-nearest-anchor remap function → clean 0–4 class index
   masks.
4. Write the `Dataset` class (`detection/train_segmentation_dl.ipynb`,
   Colab) using `segmentation_models_pytorch`, U-Net + resnet18 encoder,
   pretrained ImageNet weights, multiclass (5-class) output.
5. Train, validate, export weights + inference function producing
   `SpillDetection` JSON matching `docs/contract.md`.

## Housekeeping
- Kaggle API key was pasted in plaintext during setup — **should be
  rotated/regenerated** on the Kaggle settings page before continuing, and
  never hardcoded into a notebook cell that gets committed to the repo.
- Notebook naming convention: `detection/test_detection.ipynb` = classical
  CV baseline. `detection/train_segmentation_dl.ipynb` = DL training
  (Colab). Keep both, don't merge.


  # OceanTrace — Dev Log: 2026-09-03

## Summary
Picked up from last session's blocker (ndim bug in mask aggregation, fixed).
Spent the session fully resolving the mask-format question before writing
any training code — turned out the 5-class assumption from last session was
wrong. Ended with T4 runtime confirmed, dataset paired and loaded, model
architecture initialized. No training run started yet.

## Investigation: mask format (resolved)
- Fixed the `ndim` bug: some masks are 2D grayscale, some are 3D RGB with
  R=G=B — now branches correctly.
- Re-ran the 200-mask value aggregation. Top values didn't cluster into 5
  clean anchors as expected from the 5-class hypothesis (sea, oil spill,
  look-alike, ship, land).
- **Key diagnostic**: every non-endpoint value in the histogram paired up
  to sum to 255 (9+246, 19+236, 29+226, 1+254, 39+216, 101+154, ...). That's
  the signature of a binary mask (0/255) blended by antialiasing, not real
  discrete class anchors.
- Confirmed on a single file: `binary_equivalent` (pixels that are exactly
  0 or 255) = **100%** of that mask.
- Ran binary/mid-band check across 200 masks: binary-only fraction mean
  ~98.9%, mid-band (40–215) fraction mean ~0.6%, with 34/200 masks showing
  >1% mid-band pixels — so not *pure* antialiasing everywhere, worth
  checking if that remainder was a real sparse class.
- **Erosion test** on the 5 worst-offending masks (highest mid-band
  fraction): 2px binary erosion left only 0.7–3.6% of mid-band pixels
  surviving. A real class (ship, land) would leave a solid core; this
  didn't — confirms it's just messier antialiasing on jagged spill
  boundaries, not a hidden third class.
- Checked for a PALSAR/Sentinel-1A polarity flip (spill-fraction gap in a
  5-file sample looked suspicious) — per-source breakdown over 200 masks
  showed PALSAR mean 0.213–0.222 vs. Sentinel mean 0.264–0.294, similar
  medians and proportional >0.5 counts. Not a flip, just natural variance
  in spill size across patches. No source-aware fix needed.
- **Conclusion: this dataset (`bakhtiyar2222/deep-sar-oil-spill-segmentation-refined`,
  Deep-SAR SOS) is binary (sea vs. spill), not 5-class.** The "refined"
  Kaggle mirror doesn't carry ship/land/look-alike labels regardless of
  what the original Krestenitis-style framing promised.

## Decision: switched to binary segmentation
- Model output changes from planned multiclass (5-class softmax) to binary
  (single-channel logit + Dice loss). `docs/contract.md` doesn't need to
  change — `SpillDetection` only ever needed one polygon per spill.
- Pitch/narrative implication: dropping any claim about the DL model
  distinguishing "look-alike" from real spills — that distinction isn't
  in this dataset's labels. If it's needed for the pitch, the classical CV
  module is the fallback, or swap to a genuinely multiclass source later
  (a 2024 paper — Trujillo-Acatitla et al. — mirrors Krestenitis-style
  labeled patches openly on Zenodo, no author request needed like the
  original OSD dataset requires; not yet pulled, just flagged as a fallback).
- Final remap: `arr >= 128` → binary (0 = sea, 1 = spill). Verified clean
  `[0, 1]` output on sample files.

## Setup completed (Colab)
- Switched runtime to T4 GPU, confirmed `torch.cuda.is_available()` → True,
  `Tesla T4`.
- Re-downloaded dataset via kagglehub into fresh runtime — confirmed real
  paths: `images/images/{train,val}/`, `masks/masks/{train,val}/`, already
  split by the dataset itself (no manual split needed).
- Wrote `SpillSegDataset` (torch Dataset) — loads image+mask pairs, applies
  `remap_to_binary` on the fly, uses albumentations for augmentation
  (h-flip, v-flip, random 90° rotation) + ImageNet normalization.
- Wrote filename-based pairing function (`get_paired_files`) — matches
  images↔masks by basename, warns on any unmatched files. Confirmed clean
  pairing: **6455 train, 1615 val**, nothing dropped.
- Initialized `DataLoader`s (batch size 16, 2 workers) for train/val.
- Installed `segmentation_models_pytorch`, initialized U-Net with resnet18
  encoder, ImageNet-pretrained weights, `classes=1` (binary), moved to
  `cuda`. Loss: `DiceLoss(mode="binary")`. Optimizer: Adam, lr=1e-4.

## Housekeeping
- Kaggle API key pasted in plaintext during earlier setup — **still needs
  rotating** on the Kaggle settings page, and should never get hardcoded
  into a notebook cell that's committed to the repo. Not yet done.

## Next session — pick up here
1. Write the training loop (forward pass, loss, backward, optimizer step,
   per-epoch train/val loss + a segmentation metric like IoU or Dice score).
2. Pick epoch count / early stopping given Colab free-tier T4 time limits.
3. Run first training pass, sanity-check loss is decreasing and predicted
   masks look plausible (visualize a few val predictions).
4. Export trained weights + write the inference function that turns a
   model prediction into the `SpillDetection` JSON shape from
   `docs/contract.md` (polygon extraction from binary mask — likely
   `cv2.findContours` on the thresholded prediction, plus area/perimeter/
   elongation/fragment_count calc).
5. Rotate the exposed Kaggle API key.


# OceanTrace — Project Context (SIH 2026)

## Problem statement

ID 26143, NTRO, theme Disaster Management: detect oil spills from satellite
imagery (SAR), hindcast/forecast the slick's drift, and attribute the spill
to a vessel using historic AIS data (score suspect vessels by proximity,
trajectory, behavioral anomalies). Needs a visual interface.

## Team & event

- Team name: **Adamya** | Product name: **OceanTrace**
- Team: Aniketh Cheerath (lead, backend/ML), Karthik Agarwal (frontend),
  Rishikesh Vonteru, Uddavalu Thranoop, Akanksha Boga Ja, Arathi Jatoth
  (non-technical: data curation, PPT narrative, demo testing, logistics)
- College internal hackathon, Sept 10–11. Top 50 teams (out of the whole
  college) announced 3 PM Sept 10, judged on both a PPT and a basic working
  demo, then stay for a 36hr hackathon.
- Real prep window: Sept 7 evening – Sept 10 morning (exams Aug 31–Sept 7,
  with Sept 4 & 6 as holidays for planning/prep only).

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

## What's real vs. simulated (by design, for demo purposes)

- **Detection**: real — trained on actual Sentinel-1 SAR imagery (see below)
- **Drift (hindcast/forecast)**: simulated — simplified vector field, not
  live oceanographic/meteorological data
- **AIS attribution**: simulated — synthetic vessel tracks, since no real
  AIS is matched to a real spill event

## Detection model — status

- Originally planned classical CV (Otsu thresholding) as a safe fallback,
  but pivoted to a real trained model once a clean dataset was found.
- Dataset: `bakhtiyar2222/deep-sar-oil-spill-segmentation-refined` on
  Kaggle — 6455 train / 1615 val image-mask pairs, 256×256, sentinel +
  palsar sources.
- Found masks aren't clean binary (antialiasing noise at edges) —
  remapped to binary at threshold 128.
- Built PyTorch `SpillSegDataset` with albumentations augmentation.
- Model: U-Net via `segmentation_models_pytorch`, ResNet18 encoder
  (ImageNet pretrained), Dice loss, Adam @ lr=1e-4, training on Colab T4 GPU.
- Training in progress as of last check: ~80s/epoch, 15 epochs planned
  (~20 min total). Epoch 1 val_dice = 0.7825, epoch 2 val_dice = 0.7941,
  both improving — good result, well above the 0.5 concern threshold.
- Checkpoint saved as `best_unet_spill.pth` whenever val_dice improves.

## Repo structure (OceanTrace)

```
ais/            filter_traffic.py, generate_synthetic.py, score_vessels.py
data/           ais_samples/, sar_images/, synthetic_ais/ (gitignored)
detection/      detect_spill.py, preprocess.py, train_segmentation_dl.ipynb,
                test_detection.ipynb (classical CV, likely superseded now)
docs/           architecture.md, contract.md, NOTES.md, pitch-narrative.md
drift/          forecast.py, hindcast.py, vector_field.py
frontend/       App.jsx, MapView.jsx, Timeline.jsx, VesselRanking.jsx
outputs/        (gitignored, generated demo outputs)
pipeline/       run_pipeline.py (orchestrates detection → drift → ais → JSON)
README.md, requirements.txt
```

Files already written: `.gitignore`, `requirements.txt`, `README.md`,
`docs/NOTES.md`, `docs/contract.md`.

## Pipeline output contract (shared between backend and frontend)

```json
{
  "spill": {
    "polygon": [[lat, lon], "..."],
    "detected_at": "ISO8601",
    "area_km2": 0.0
  },
  "drift": {
    "hindcast_path": [[lat, lon, "timestamp"], "..."],
    "estimated_origin": {"lat": 0.0, "lon": 0.0, "time": "ISO8601"},
    "forecast_path": [[lat, lon, "timestamp"], "..."]
  },
  "vessels": [
    {
      "vessel_id": "string", "name": "string", "score": 0.0,
      "proximity_score": 0.0, "trajectory_score": 0.0,
      "anomaly_score": 0.0, "track": [[lat, lon, "timestamp"], "..."]
    }
  ]
}
```

Coordinates: `[lat, lon]`, decimal degrees. Timestamps: ISO 8601 UTC.
`vessels` pre-sorted by `score` descending.

## Ownership

- Aniketh: detection, drift, AIS scoring (backend/ML core)
- Karthik: frontend dashboard (separate repo, building against the
  contract above with mock data, given a standalone `FRONTEND_BRIEF.md`)
- Non-technical team: dataset/incident research, PPT narrative, demo
  stress-testing, hackathon-day logistics

## Phases

- **Phase 0** (now–Sept 6): planning/prep, no coding pressure
- **Phase 1** (Sept 7 eve–8): core detection pipeline, vertical slice
  (image → polygon → map)
- **Phase 2** (Sept 8 night–9): drift simulation + AIS scoring +
  frontend integration
- **Phase 3** (Sept 9 night–10 morning): polish, PPT, rehearse pitch

## Not yet started

- Drift simulation (`drift/` module — vector field, hindcast, forecast)
- AIS synthetic data generation + vessel scoring (`ais/` module)
- Inference script to go from trained model → spill polygon (contour
  extraction from predicted mask)
- `pipeline/run_pipeline.py` orchestration logic
- PPT / pitch narrative content