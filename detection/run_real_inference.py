"""
detection/run_real_inference.py

Runs the trained U-Net on a real windowed crop of the real Sentinel-1 GRD
scene, instead of a training PALSAR PNG. Handles the two real-vs-synthetic
gaps:

  1. Real scene is 16733x25529 -- far too large for one forward pass.
     We read a small window (default 256x256, matching training patch
     size) directly off disk via rasterio, so we never load the full
     scene into memory.

  2. Real scene is uint16 single-channel SAR amplitude, not 8-bit RGB
     like the training PNGs. We apply a standard SAR preprocessing step
     (log/dB scaling + percentile clipping + normalize to 0-255), then
     replicate to 3 channels so the model (trained expecting RGB input)
     sees a compatible tensor.

Usage:
    python detection/run_real_inference.py
"""

import json
import numpy as np
import rasterio
from rasterio.windows import Window
from PIL import Image

from detection.detect_spill import load_model, predict_mask, mask_to_spill_detection
from detection.extract_geo import get_window_bounds_latlon


REAL_TIFF_PATH = (
    "data/real_sar/"
    "S1D_IW_GRDH_1SDV_20260626T010234_20260626T010259_003400_005FC3_48CE.SAFE/"
    "measurement/"
    "s1d-iw-grd-vv-20260626t010234-20260626t010259-003400-005fc3-001.tiff"
)

# Must match the training patch size (confirmed: PALSAR PNGs are 256x256).
PATCH_SIZE = 256


def read_and_preprocess_window(tiff_path: str, row_off: int, col_off: int,
                                patch_size: int = PATCH_SIZE) -> np.ndarray:
    """
    Reads a (patch_size x patch_size) window from the real GeoTIFF and
    converts it from raw uint16 SAR amplitude into an 8-bit 3-channel
    RGB-like array the model can consume.

    Steps:
      1. Windowed read (only pulls this crop off disk, not the whole scene)
      2. dB scaling: SAR amplitude is heavy-tailed; convert to log scale
         so bright/dark features are visually comparable to how PALSAR
         training images (already visually normalized) look.
      3. Percentile clip (2nd-98th) to avoid a few extreme outlier pixels
         crushing the normalization range.
      4. Rescale to 0-255 uint8.
      5. Replicate the single channel to 3 channels (RGB), since the
         model's encoder (resnet18, imagenet weights) expects 3-channel
         input and was fine-tuned on 3-channel PALSAR PNGs.
    """
    window = Window(col_off, row_off, patch_size, patch_size)

    with rasterio.open(tiff_path) as src:
        raw = src.read(1, window=window).astype(np.float32)

    # Avoid log(0)
    raw = np.clip(raw, 1e-6, None)
    db = 10 * np.log10(raw)

    p2, p98 = np.percentile(db, (2, 98))
    db_clipped = np.clip(db, p2, p98)

    normalized = (db_clipped - p2) / (p98 - p2 + 1e-6)
    img_8bit = (normalized * 255).astype(np.uint8)

    rgb = np.stack([img_8bit, img_8bit, img_8bit], axis=-1)  # (H, W, 3)
    return rgb


def find_ocean_window(tiff_path: str, patch_size: int = PATCH_SIZE,
                       n_candidates: int = 20, seed: int = 42):
    """
    Scans a handful of candidate windows and picks one with low variance
    in raw amplitude (a rough, cheap proxy for "calm open water" --
    land/coastline tends to have much higher backscatter variance than
    open sea). Not scientifically rigorous, just good enough to avoid
    accidentally cropping onto land for a demo.

    Returns (row_off, col_off) of the chosen window.
    """
    rng = np.random.default_rng(seed)

    with rasterio.open(tiff_path) as src:
        h, w = src.height, src.width

        best_var = None
        best_offset = None

        for _ in range(n_candidates):
            row_off = int(rng.integers(0, h - patch_size))
            col_off = int(rng.integers(0, w - patch_size))
            window = Window(col_off, row_off, patch_size, patch_size)
            sample = src.read(1, window=window).astype(np.float32)

            var = np.var(sample)
            if best_var is None or var < best_var:
                best_var = var
                best_offset = (row_off, col_off)

    return best_offset


def run_real_inference(tiff_path: str = REAL_TIFF_PATH,
                        checkpoint_path: str = "best_unet_spill.pth",
                        row_off: int = None, col_off: int = None,
                        spill_id: str = "spill_real_001",
                        detected_at: str = ""):
    """
    Full pipeline: pick/accept a window, preprocess it, run the model,
    convert the output mask into a real-lat/lon-georeferenced detection
    record -- the same JSON shape as the synthetic pipeline produces.
    """
    if row_off is None or col_off is None:
        row_off, col_off = find_ocean_window(tiff_path)
        print(f"Auto-selected window at row_off={row_off}, col_off={col_off}")

    rgb_array = read_and_preprocess_window(tiff_path, row_off, col_off)

    # Save the preprocessed crop to disk so predict_mask() (which expects
    # an image_path, per the existing detect_spill.py interface) can load it.
    tmp_path = "outputs/_real_crop_tmp.png"
    Image.fromarray(rgb_array).save(tmp_path)

    real_bounds = get_window_bounds_latlon(
        tiff_path, row_off, col_off, PATCH_SIZE, PATCH_SIZE
    )
    print(f"Real window bounds (lon/lat): {real_bounds}")

    model = load_model(checkpoint_path)
    binary_mask, prob = predict_mask(model, tmp_path)

    result = mask_to_spill_detection(
        binary_mask, prob, real_bounds,
        spill_id=spill_id,
        source_image=f"{tiff_path} [window row={row_off},col={col_off}]",
        detected_at=detected_at,
    )

    if result is None:
        print(
            "No spill detected in this window (expected -- it's real open "
            "water with no actual spill). This still proves the real-data "
            "pipeline runs end-to-end: real crop -> real preprocessing -> "
            "model inference -> real georeferenced output shape."
        )
    return result


if __name__ == "__main__":
    result = run_real_inference(detected_at="2026-09-08T14:00:00Z")
    if result:
        print(json.dumps(result, indent=2))