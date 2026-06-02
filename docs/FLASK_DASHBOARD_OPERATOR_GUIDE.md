# Flask Dashboard Operator Guide

Dashboard Flask Phase 5 bisa dijalankan tanpa label final dan tanpa model final.

## Run Lokal

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_flask_dev.py
```

Default:

- host: `127.0.0.1`
- port: `5000`

## Route Utama

- `GET /`
- `GET /health`
- `GET /api/status`
- `GET /api/classes`
- `GET /api/points`
- `GET /api/risk/sample`
- `GET /api/map/status`
- `POST /api/infer/image`

## Perilaku Aman

- `/api/infer/image` mengembalikan `MODEL_NOT_READY` jika bobot model final belum ada.
- Dashboard tidak menulis file upload ke `data/raw`.
- Dashboard tidak membuat deteksi palsu.
- Dashboard tidak membutuhkan label selesai untuk menampilkan status.

## Status Yang Diharapkan Saat Ini

- Labeling: `WAITING_FOR_LABELS`
- Dataset: `DATASET_NOT_READY`
- Model: `MODEL_NOT_READY`
- Environmental data: `ENVIRONMENTAL_DATA_NOT_READY`
