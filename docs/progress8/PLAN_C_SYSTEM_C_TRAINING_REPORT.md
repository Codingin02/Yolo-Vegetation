# Plan C System C Detector Training Report

## Status

- training_status: `PLAN_C_SYSTEM_C_TRAINING_COMPLETE`
- registry_status: `PLAN_C_SYSTEM_C_DETECTOR_READY`
- frontend_changed: `No`
- final_detector: `YOLOv8`
- provider_consensus: `Gemini + Groq Console/GroqCloud + OpenRouter`
- note: Cloud AI provider dipakai untuk consensus validation, bukan training lokal.

## Dataset Audit

- source_audit_report: `data/metadata/plan_c_training_dataset_audit_20260615_082645.json`
- image_count: `905`
- label_file_count: `939`
- valid_label_lines: `1564`
- invalid_label_lines: `0`
- struktur_penyangga: `659`
- konduktor: `592`
- pohon_sono: `313`
- ready_for_training: `true`

## Dataset Final

- dataset_path: `data/dataset_yolo/plan_c_system_c_detector_v2`
- image_count: `910`
- label_file_count: `910`
- split_train: `726`
- split_val: `141`
- split_test: `43`
- class_mapping: `0 struktur_penyangga`, `1 konduktor`, `2 pohon_sono`
- source_data_modified: `false`

Dataset final dibuat dari label yang sudah ada. Tidak ada scraping internet dan tidak
ada labeling ulang dari nol.

## Training

- base_model: `yolov8n.pt`
- epochs: `100`
- imgsz: `640`
- final_run: `runs/detect/plan_c_system_c_detector_v2_20260615_022850`
- best_pt: `models/plan_c_system_c_detector/best.pt`
- last_pt: `models/plan_c_system_c_detector/last.pt`
- registry: `models/plan_c_system_c_detector/registry.json`

Training pertama dengan CUDA AutoBatch gagal karena error CUDA `resource already
mapped`. Training dilanjutkan dengan GPU batch kecil dan `workers=0`, lalu selesai
100 epoch. File model tidak distage ke Git.

## Metrics

Metrics dari `runs/detect/plan_c_system_c_detector_v2_20260615_022850/results.csv`
epoch 100:

- precision: `0.74723`
- recall: `0.59932`
- mAP50: `0.58888`
- mAP50-95: `0.54877`

Per-class metrics tidak tersedia di `results.csv` registry. Angka di atas adalah
metrics aggregate validasi training, bukan klaim akurasi final PLN.

## Runtime Integration

Backend Plan C memprioritaskan:

1. `models/plan_c_system_c_detector/best.pt`
2. `models/plan_c_ai_detector/best.pt`
3. `runs/detect/plan_c_system_c_detector_v2*/weights/best.pt`
4. fallback lama jika ada

Jika model System C aktif:

- `runtime_mode = PLAN_C_SYSTEM_C`
- `model_policy = system_c_detector`
- `detector = YOLOv8`
- `zone_overlay_status = ZONE_OVERLAY_RENDERED`

## Smoke

- `scripts/plan_c_smoke.py`: `PLAN_C_SYSTEM_C_BACKEND_SMOKE_PASS`
- `scripts/plan_c_ai_backend_smoke.py`: `PLAN_C_AI_BACKEND_SYSTEM_C_SMOKE_PASS`
- annotated smoke image: `data/runtime/plan_c/sessions/PC_20260615_082720_e20c5e48/annotated.jpg`
- smoke risk_status: `ZONA_TEBANG`
- smoke final_detection_source: `AI_CONSENSUS`

## Cara Menjalankan

```powershell
Set-Location E:\Projects\ULP_Project
.\scripts\run_plan_c_system.ps1
```

Local:

```text
http://127.0.0.1:5000/plan-c
```

HP:

```text
https://<ngrok-url>/plan-c
```
