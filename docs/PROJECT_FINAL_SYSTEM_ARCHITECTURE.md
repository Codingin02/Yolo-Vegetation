# Project Final System Architecture

## Input

- Field point images/video/GPS dari user.
- Label YOLO dari makesense.ai.
- Manual environmental CSV.
- Field point registry CSV.

## Pipeline

1. Import label dry-run/copy setelah export siap.
2. Validate YOLO labels.
3. Build `field_multiclass_v1`.
4. Generate `data.yaml`.
5. Training YOLOv8 dengan approval operator.
6. Inference runtime.
7. Calibration/distance estimation.
8. Vegetation growth risk skeleton.
9. Flask dashboard/API.
10. Map runtime.
11. Report export.

## Batas Saat Ini

Pipeline final tetap blocked oleh label makesense.ai. Sistem runtime bisa berjalan sebagai dry-run dan dashboard status tanpa model final.

## Environmental Data

Data lingkungan akan diisi dari CSV manual dan registry sumber:

- BPS
- BMKG
- KLHK
- BIG
- city open data
- manual survey

Tidak ada nilai lingkungan yang dibuat dari asumsi.
