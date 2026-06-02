# Phase 6 Operator Test Plan

## Validasi Aman

```powershell
.\venv\Scripts\python.exe -m compileall src scripts tests
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe scripts\phase6_mobile_environmental_gate.py
```

## Jalankan Dashboard

```powershell
.\venv\Scripts\python.exe scripts\run_flask_dev.py
```

Buka:

```text
http://127.0.0.1:5000/mobile
```

Untuk HP pada jaringan yang sama, pakai IP laptop:

```text
http://<laptop-ip>:5000/mobile
```

## Uji Endpoint Manual

- `GET /health`
- `GET /api/status`
- `GET /api/mobile/network/status`
- `GET /api/latency/ping`
- `POST /api/mobile/upload-inspection`

## Setelah Export YOLO Makesense Selesai

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_gate.py
.\venv\Scripts\python.exe scripts\phase4_integration_gate.py
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy
.\venv\Scripts\python.exe scripts\validate_yolo_labels.py --point V001_pohon_sono
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
```

`--mode build` dan training aktual hanya setelah validator PASS dan operator memberi izin.
