# Phase 17 Model Handoff Runbook

Jalankan:

```powershell
.\venv\Scripts\python.exe scripts\check_model_handoff_ready.py
```

Jika model belum ada, status normal:

```text
MODEL_NOT_READY
SKIPPED_NO_MODEL
```

Setelah `best.pt` tersedia, letakkan di path ignored dan ulangi check. Jangan membuat dummy `.pt`, jangan download otomatis, dan jangan klaim akurasi sebelum validasi.
