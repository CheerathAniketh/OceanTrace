# OceanTrace — Session Notes (post-checkpoint `c072b2c`)

Context for picking this up: SIH 2026, Problem Statement #26143 (NTRO), team Adamya.
Repo: `~/Desktop/Projects/OceanTrace` on Fedora. Backend is feature-complete;
this session was about closing the gap between "technically working" and
"actually satisfying" by replacing synthetic pieces with real data where feasible.

## Status confirmed this session

- Ran the full pipeline end-to-end for real: `uvicorn api.main:app --reload` →
  `/api/spill-result` returns `200 OK` with real (non-mock) pipeline output.
  The two `404`s in the logs (`/` and `/favicon.ico`) are expected — no routes
  defined for those, not a bug.
- Reviewed `frontend/src/components/MapView.jsx` directly: both previously
  filed bugs are fixed —
  - coordinate slicing (`p => [p[0], p[1]]`) correctly ignores the extra
    `timestamp` field real data adds that mock data lacked
  - `FitBounds` component correctly auto-fits to all spill/hindcast/forecast/
    vessel coordinates instead of a fixed zoom
- Reviewed `api/main.py`: FastAPI serves real `outputs/pipeline_result.json`
  at `/api/spill-result`, CORS scoped to the Vite dev server only, 404
  fallback if the pipeline hasn't been run, plus a `/api/health` endpoint.
  Minor unaddressed gap: no try/except around `json.load()` — a mid-write
  read could throw a raw 500 instead of a clean error. Low risk unless
  re-running the pipeline live during a demo.
- Live screenshot reviewed: spill polygon + hindcast (purple) + forecast
  (orange) rendering correctly near Mumbai; vessel ranking panel working,
  correctly flags `MV Kalindi Star` as primary suspect (81%, 100% proximity,
  100% trajectory, only 7% anomaly — genuinely interesting result, low
  anomaly but caught purely on spatiotemporal correlation).
- Noted possible issue: two vessel tracks in the screenshot render as short
  disconnected gray segments rather than continuous paths — not yet
  diagnosed. Worth checking whether those vessels' `track` arrays are
  actually short, or something is clipping them on render.

## Decision: frontend polish handed off to Karthik

Aniketh is having Karthik fork/clone and open his own PR rather than
Aniketh editing directly. Punch list to hand him via a GitHub issue:

1. Legend (color key: spill / hindcast / forecast / vessel)
2. Swap default OSM tiles for a minimal/dark basemap
3. Add labeled origin + "now" markers on the drift path
4. Link vessel list ↔ map (select/hover highlights track both ways)
5. (carried over, unconfirmed fixed) investigate the two truncated vessel tracks

## What's synthetic vs. real right now — full breakdown

Three synthetic pieces:
1. **AIS data** — all vessels/tracks in `ais/generate_synthetic.py` are
   fabricated, including the one scripted "suspect."
2. **Georeferencing** — the Kaggle SAR training images have no real-world
   coordinates; the fixed demo bounding box `(72.70, 19.05, 72.76, 19.10)`
   is an arbitrary placeholder assigned in code, not derived from the image.
3. **Ocean current vector field** — `drift/vector_field.py` uses a made-up
   constant+sinusoidal current, not real oceanographic data.

Real already: the detection model itself (trained on real Sentinel-1/PALSAR
pairs), the drift physics (Euler integration is a legitimate advection
method, just fed a fake current field), and the AIS scoring logic (haversine
distance, trajectory matching, anomaly detection — real algorithms, just
scoring fake vessels).

Reassurance found in the official problem statement text: it explicitly
says real AIS may be used "else synthetic data can be prepared for the
region of oil spill to demonstrate the functioning of the algorithm" — so
the synthetic AIS approach is explicitly sanctioned by NTRO, not a
compliance risk. It also names a Zenodo Sentinel-1 SAR dataset as the
official imagery reference.

## Real-data options investigated this session

**AIS (Indian/Arabian Sea coverage):**
- MarineCadastre/NOAA, Danish Maritime Authority, Korean KRISO — all
  regionally locked to their own coastal waters, not usable.
- **Global Fishing Watch (GFW)** — best lead. Confirmed to cover the exact
  region (high seas between Arabian Peninsula and India, notably a large
  squid fleet). Offers a Global AIS Vessel Presence dataset (one position/
  vessel/hour) via their 4Wings API, plus bulk CSV/JSON export, plus MMSI/
  IMO/name resolution across 40+ registries. Caveat: AIS usage in that
  region is only ~25% (lots of "dark" vessels not broadcasting) — this
  could make a decent demo talking point ("dark fleet = exactly what our
  anomaly scoring should flag") but may mean sparser real traffic than the
  current 4 clean synthetic ships, especially in a small coastal bounding
  box. Not yet signed up / API not yet queried.

**SAR imagery georeferencing:**
- Found the exact Zenodo dataset the problem statement points to:
  "Sentinel-1 SAR Oil spill image dataset for train/validate/test" (3
  parts, DOIs 8346860 / 8253899 / 13761290). Confirmed via the record page:
  the Sigma0 image TIFFs (VV+VH, 2048x2048x2) **are georeferenced**; the
  masks are not (irrelevant for our use — we only need the input scene
  georeferenced, not the mask).
- Blocker: images archive is 40.7GB in one `.7z`, no way to selectively
  pull 2-3 files without downloading the whole thing.
- **Decided against this path.** Better option: pull 1-2 individual real
  Sentinel-1 scenes directly from **Copernicus Data Space** or **ASF
  (Alaska Satellite Facility)** — both are raw satellite product sources
  (a few hundred MB–1GB per scene, not 40GB) and are georeferenced by
  definition. Not yet searched for a specific scene.
- Important clarification already settled: swapping to a real georeferenced
  SAR scene does **not** require retraining the U-Net. The model
  (`best_unet_spill.pth`) is already trained; this is purely an inference-
  input swap. Only new code needed: (a) preprocessing to match input
  dimensions/normalization if the new scene differs from training shape,
  (b) a small script to read real lat/lon out of the GeoTIFF metadata
  after inference (likely needs `rasterio`, not PIL, since it's GeoTIFF).

**Ocean current data:** NOAA HYCOM / Copernicus Marine Service have real
data — flagged as lowest priority since it's narratively invisible (a judge
can't visually tell real vs. fake current physics from a dashed line).

## Next steps (in order, as of this session)

1. Search Copernicus Data Space or ASF for a single real, georeferenced
   Sentinel-1 scene (ideally over open water, or a documented real spill
   event) — small enough to actually download.
2. Run that scene through the existing `detect_spill.py`, confirm the
   model still segments sensibly on it, extract real lat/lon from the
   GeoTIFF metadata, update the fixed demo bounding box to match.
3. Decide whether to pursue GFW for real AIS in that same region (their
   API access flow hasn't been checked yet — needs a free account/token).
4. File the GitHub issue for Karthik with the 5-item frontend punch list
   above.
5. Optional stretch goal, still not attempted: spill age estimation
   (explicitly called out as optional in the problem statement).
6. Eventually: polish + rehearse pitch narrative.

## Useful framing for the pitch

The "what's real vs. simulated" transparency (already in the README) is a
strength, not a weakness to hide — pre-empts the "is this actually working"
question judges will ask. If real AIS/SAR swaps land in time, the narrative
upgrades from "we simulated to demonstrate" to "we validated against real
Sentinel-1 data and real AIS traffic in the exact region," which is a
stronger claim but not a required one per the problem statement's own
wording.


OceanTrace — Session Notes (continues from checkpoint c072b2c)
What happened this session

Picked up the "make it real" thread from last session. Focus was entirely on swapping synthetic SAR georeferencing for real Sentinel-1 data — item #2 of the three synthetic pieces (AIS, georeferencing, ocean currents).

Completed
Ruled out Zenodo (confirmed from last session — 40.7GB single .7z, no selective download, dead end).
Signed up for NASA Earthdata (urs.earthdata.nasa.gov), account activated, username cheerathaniketh.
Searched ASF Vertex (search.asf.alaska.edu) for Sentinel-1 GRD scenes over the Arabian Sea near Mumbai. Dataset: Sentinel-1, Beam Mode: IW, AOI polygon roughly 72–73.5°E, 18–20°N.
Selected and downloaded a real scene: S1D_IW_GRDH_1SDV_20260626T010234_20260626T010259_003400_005FC3_48CE — GRD-HD, 841MB, mostly open water with a coastline sliver (good water:land ratio for spill detection demo). VV+VH dual-pol, descending pass, June 26 2026.
Unzipped into data/real_sar/ — standard SAFE structure confirmed: measurement/*.tiff (VV and VH GeoTIFFs), annotation/*.xml (calibration/noise/RFI), manifest.safe, preview/, support/.
Wrote detection/extract_geo.py — a georeferencing extraction script. Key technical discovery: raw Sentinel-1 GRD products are NOT simple affine-transform GeoTIFFs — src.crs returns None. They're georeferenced via GCPs (Ground Control Points), a scattered mesh of (pixel row/col) → (lat/lon) tie-points. Script was rewritten to read src.gcps instead, and uses scipy.interpolate.griddata to interpolate arbitrary pixel coordinates (e.g. a U-Net output polygon's vertices) against the GCP mesh.
Ran and validated the script — real results:
GCP CRS: EPSG:4326 (already lat/lon, no reprojection needed)
Image shape: 16733 rows × 25529 cols
Real bbox: min_lon=71.07044, min_lat=17.53204, max_lon=73.73749, max_lat=19.47383
Sanity check passed: this is ~280km × 215km, consistent with a real Sentinel-1 IW swath. The old hardcoded placeholder (72.70–72.76, 19.05–19.10) sits entirely inside this real bbox — reassuring, confirms the original placeholder was at least geographically plausible.
Git hygiene: confirmed data/ was entirely untracked (including sar_images/ training PNGs — was already gitignored via existing rules, good). Added data/real_sar/* to .gitignore to exclude the 842MB zip + large TIFFs from the repo (GitHub has a 100MB/file hard limit anyway). About to commit extract_geo.py + updated .gitignore only.
Script reference: detection/extract_geo.py

Three functions ready to use:

get_scene_bounds(tiff_path) → returns real (min_lon, min_lat, max_lon, max_lat), GCP CRS, image shape
pixel_to_latlon(tiff_path, row, col) → single pixel → real (lat, lon)
polygon_pixels_to_latlon(tiff_path, pixel_polygon) → this is the key one — takes the U-Net's output polygon (list of (row, col) pixel vertices) and returns real (lat, lon) vertices. This replaces the old hardcoded bbox-based polygon everywhere downstream.

Default SAR_TIFF_PATH in the script points to the VV band:

data/real_sar/S1D_IW_GRDH_1SDV_20260626T010234_20260626T010259_003400_005FC3_48CE.SAFE/measurement/s1d-iw-grd-vv-20260626t010234-20260626t010259-003400-005fc3-001.tiff
Not yet done / next steps (in order)
Commit extract_geo.py + .gitignore (in progress as of this message — run git add .gitignore detection/extract_geo.py, verify git status shows only those two, then commit).
Wire the real scene into detect_spill.py: run actual U-Net inference on the real VV GeoTIFF (not a PALSAR training PNG). Will likely need preprocessing adjustments in detection/preprocess.py since a real 16733×25529 scene is far larger than the training patch size — needs tiling/cropping/resizing logic, not a direct full-scene forward pass.
Decide: full scene vs. crop — the real scene is huge (~280×215km). Options: (a) run inference on the full scene and let the real spill polygon define its own location, or (b) crop a smaller sub-region near the coast first for a tighter, more controlled demo. Not yet decided.
Replace the hardcoded bbox in whatever downstream code currently consumes (72.70, 19.05, 72.76, 19.10) — likely pipeline/run_pipeline.py and/or drift/ modules — with the real bbox / real polygon from extract_geo.py.
Sanity-check the real scene visually before/after inference (e.g., quick matplotlib preview) — not yet done, was suggested but deferred in favor of committing first.
Still pending from last session, untouched this session:
File the GitHub issue for Karthik (5-item frontend punch list)
GFW AIS real-data path (signup/token not started)
Investigate the two truncated vessel track rendering bug in MapView.jsx
Optional stretch: spill age estimation
Key technical gotcha to remember

Raw Sentinel-1 GRD GeoTIFFs use GCPs, not affine transforms. If continuing this work or explaining it to Karthik/teammates: rasterio's normal src.crs / src.transform / transform_bounds() workflow does NOT work on these files — must use src.gcps and interpolate (e.g. via scipy.interpolate.griddata) instead. This cost one failed run and a rewrite this session — worth flagging so it's not re-discovered from scratch.