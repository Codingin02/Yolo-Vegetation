# Project Progress Split Labeling And System

## Kelompok A - Labeling

Status: `WAITING_FOR_MAKESENSE_EXPORT`

User sedang mengerjakan labeling manual untuk:

```text
data/dataset_yolo/00_review_candidates/V001_pohon_sono/images_selected
```

Codex tidak menyentuh folder ini.

## Kelompok B - Sistem

Status modul:

| Modul | Status |
|---|---|
| `.gitignore` aman | READY |
| Class order config | READY |
| Import makesense | DRY_RUN_READY |
| Validator YOLO | READY |
| Dataset builder | WAITING_FOR_LABELS |
| Data YAML generator | DRY_RUN_READY |
| Training launcher | DRY_RUN_READY |
| Flask scaffold | READY_WITH_MODEL_NOT_AVAILABLE_STATE |
| Folium map scaffold | READY_OR_GPS_PARTIAL |
| CSV metadata export | READY_LOCAL_CSV |
| Environmental risk skeleton | SCHEMA_READY_WAITING_DEEP_RESEARCH |
| Tests minimal | READY |

## Yang Masih Menunggu

- Export YOLO dari makesense.ai.
- Validator label PASS.
- Build dataset final.
- Training YOLOv8.
- Evaluasi model dan metrik nyata.
- Data lingkungan resmi untuk scoring risiko.
