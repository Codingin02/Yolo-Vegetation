# Phase 4 System Integration Runbook

Phase 4 menyiapkan integrasi sistem tanpa menyentuh labeling.

## Command Aman Sekarang

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe -m compileall src scripts tests
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe scripts\phase2_system_smoke_test.py
.\venv\Scripts\python.exe scripts\phase3_readiness_gate.py
.\venv\Scripts\python.exe scripts\phase4_integration_gate.py
.\venv\Scripts\python.exe scripts\system_status_report.py --format text
.\venv\Scripts\python.exe scripts\system_status_report.py --format json
```

## Status Yang Benar Saat Label Belum Selesai

- `WAITING_FOR_LABELS`
- `BLOCKED_WAITING_FOR_MAKESENSE_EXPORT`
- `DATASET_NOT_READY`
- `MODEL_NOT_READY`

## Larangan

- Jangan import mode copy sebelum export YOLO siap.
- Jangan build dataset mode build sebelum validator PASS.
- Jangan training final sebelum dataset siap dan user memberi izin eksplisit.
- Jangan gunakan `dataset_botol` sebagai dataset utama.
