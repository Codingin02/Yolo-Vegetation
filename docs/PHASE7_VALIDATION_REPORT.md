# Phase 7 Validation Report

Report ini dibuat sebagai checklist operator. Hasil aktual dicatat pada output final Codex setelah validasi dijalankan.

## Expected Status

- Field capture route: ready.
- `/mobile`: alias kompatibilitas ke `/field-capture`.
- Model: `MODEL_NOT_READY`.
- ETA: `NOT_AVAILABLE` jika growth/clearance/env belum cukup.
- Sheets: dry-run/local CSV ready; live push menunggu credential.
- Labeling folder: tidak disentuh.
- Dataset botol: tidak digunakan sebagai dataset utama.

## Commands

```powershell
.\venv\Scripts\python.exe -m compileall src scripts tests
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe scripts\phase7_realtime_field_gate.py
.\venv\Scripts\python.exe scripts\run_manual_risk_estimate.py --sample pohon_sono --mode dry-run
git diff --check
```
