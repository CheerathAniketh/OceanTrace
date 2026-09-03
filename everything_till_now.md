# OceanTrace — Dev Log: Progress Summary
*Date: 2026-09-03*

## 1. Strategy & Architecture Pivot
* Scaffolding is fully set up for the `detection`, `drift`, `ais`, and `pipeline` modules.
* The backend-to-frontend JSON contract is locked, targeting an Arabian Sea mock environment (Lat 19.0, Lon 72.7).
* Investigated the `bakhtiyar2222` Deep-SAR Kaggle dataset and proved the masks were binary (with antialiasing) rather than discrete 5-class anchors. 
* Pivoted the detection strategy from classical CV / 5-class classification to binary Deep Learning segmentation.

## 2. Model Training (Colab)
* Built a custom PyTorch `Dataset` pipeline featuring Albumentations and ImageNet normalization.
* Trained a ResNet18-backed U-Net on a Tesla T4 GPU for 15 epochs.
* Achieved a strong validation Dice score of **0.8265**.
* Exported the final `best_unet_spill.pth` weights for local inference.
* Verified the model outputs valid polygon coordinates during a test inference run (currently outputting Gulf of Mexico coordinates around Lat 28.0, Lon -95.0).

## 3. Immediate Next Steps
* **Georeferencing:** Write the projection utility in `detection/detect_spill.py` to map the U-Net's raw pixel output into the specific Arabian Sea bounding box required by the React frontend.
* **Drift Simulation:** Build `drift/hindcast.py` to calculate the slick's estimated origin point and time.
* **AIS Scoring:** Build `ais/generate_synthetic.py` and `score_vessels.py` to generate fake ship tracks and score them against the hindcasted origin.