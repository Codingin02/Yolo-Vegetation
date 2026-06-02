# Phase 7 Realtime Vegetation Risk System

Phase 7 mengoreksi arah Phase 6: sistem ini bukan aplikasi mobile. HP hanya menjadi browser input lapangan. Laptop tetap server pemrosesan untuk Flask, inference, estimasi jarak, risk engine, CSV/Google Sheets, dan peta.

## Status Saat Ini

- Labeling: `WAITING_FOR_LABELS`
- Model: `MODEL_NOT_READY`
- Dataset final: `DATASET_NOT_READY`
- Kalibrasi jarak: `CALIBRATION_NOT_READY`
- Data lingkungan: `ENVIRONMENTAL_DATA_NOT_READY` atau `PARTIAL`
- Risk engine: siap untuk estimasi provisional berbasis input manual/nyata.

## Komponen Siap

- `/field-capture` untuk input HP via browser.
- `/operator` untuk dashboard operator laptop.
- Risk engine kabel/span/trafo.
- ETA menuju kontak aset listrik, jika clearance dan growth rate sudah tersedia.
- CSV/Google Sheets schema sebagai monitoring utama.
- Peta risiko ke `outputs/reports/`.

## Batas Klaim

Jangan menyebut akurat sebelum model YOLO dilatih, kalibrasi lapangan selesai, data lingkungan tersedia, dan ground truth tervalidasi.
