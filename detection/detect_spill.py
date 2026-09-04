"""
detection/detect_spill.py

Loads the trained U-Net oil spill segmentation model and runs inference
on a SAR image, returning a spill detection result (polygon + geometric
properties) in the same JSON shape used across the pipeline.
"""

import json
import numpy as np
import cv2
import torch
import segmentation_models_pytorch as smp
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Same normalization/resize used during training — must match, or the
# model will see out-of-distribution inputs and predict garbage.

INFERENCE_TRANSFORM = A.Compose([
    A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ToTensorV2(),
])



def load_model(checkpoint_path="best_unet_spill.pth", device=DEVICE):
    """Load the trained U-Net with weights from checkpoint_path."""
    model = smp.Unet(
        encoder_name="resnet18",
        encoder_weights="imagenet",
        classes=1,
        activation=None,
    )
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model = model.to(device)
    model.eval()
    return model


def predict_mask(model, image_path, transform=INFERENCE_TRANSFORM, threshold=0.5, device=DEVICE):
    """Run the model on one image, return (binary_mask, probability_map)."""
    image = np.array(Image.open(image_path).convert("RGB"))
    augmented = transform(image=image)
    input_tensor = augmented["image"].unsqueeze(0).to(device)

    model.eval()
    with torch.no_grad():
        logits = model(input_tensor)
        prob = torch.sigmoid(logits).squeeze().cpu().numpy()

    binary_mask = (prob > threshold).astype(np.uint8)
    return binary_mask, prob


def mask_to_spill_detection(binary_mask, prob, image_bounds, spill_id="spill_001",
                             source_image="", detected_at=""):
    """
    Convert a binary segmentation mask into a spill detection record:
    polygon (georeferenced), area, perimeter, elongation, fragment count,
    and confidence.

    image_bounds: (min_lon, min_lat, max_lon, max_lat) for the image.
    """
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    h, w = binary_mask.shape
    min_lon, min_lat, max_lon, max_lat = image_bounds

    def px_to_lonlat(x, y):
        lon = min_lon + (x / w) * (max_lon - min_lon)
        lat = max_lat - (y / h) * (max_lat - min_lat)
        return [lon, lat]

    contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)
    main = contours_sorted[0]
    coords = [px_to_lonlat(pt[0][0], pt[0][1]) for pt in main]
    coords.append(coords[0])

    area_px = cv2.contourArea(main)
    perimeter_px = cv2.arcLength(main, True)

    if len(main) >= 5:
        (cx, cy), (d1, d2), angle = cv2.fitEllipse(main)
        major, minor = max(d1, d2), min(d1, d2)
        elongation = major / minor if minor > 0 else 1.0
    else:
        elongation = 1.0

    lon_km = (max_lon - min_lon) * 111.0
    lat_km = (max_lat - min_lat) * 111.0
    px_area_km2 = area_px * (lon_km / w) * (lat_km / h)
    px_perim_km = perimeter_px * ((lon_km / w + lat_km / h) / 2)

    return {
        "spill_id": spill_id,
        "source_image": source_image,
        "detected_at": detected_at,
        "polygon": {"type": "Polygon", "coordinates": [coords]},
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "area_km2": round(float(px_area_km2), 2),
        "perimeter_km": round(float(px_perim_km), 2),
        "elongation": round(float(elongation), 2),
        "fragment_count": len(contours),
        "confidence": float(prob[binary_mask == 1].mean()) if binary_mask.sum() > 0 else 0.0,
    }


def detect_spill(image_path, image_bounds, checkpoint_path="best_unet_spill.pth",
                  spill_id="spill_001", detected_at=""):
    """
    One-call entry point: load model, run inference, return detection JSON.
    This is what pipeline/run_pipeline.py should import and call.
    """
    model = load_model(checkpoint_path)
    binary_mask, prob = predict_mask(model, image_path)
    source_image = image_path.split("/")[-1]
    return mask_to_spill_detection(
        binary_mask, prob, image_bounds,
        spill_id=spill_id, source_image=source_image, detected_at=detected_at,
    )


if __name__ == "__main__":
    test_bounds = (72.70, 19.05, 72.76, 19.10)  # Arabian Sea, matches frontend mock
    result = detect_spill(
        image_path="data/sar_images/images/palsar_101.png",
        image_bounds=test_bounds,
        spill_id="spill_test_001",
        detected_at="2026-09-08T14:00:00Z",
    )
    print(json.dumps(result, indent=2))