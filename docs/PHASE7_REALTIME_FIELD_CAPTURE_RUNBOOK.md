# Phase 7 Realtime Field Capture Runbook

Gunakan halaman `/field-capture` untuk input HP berbasis browser. Ini bukan aplikasi mobile.

```powershell
.\venv\Scripts\python.exe scripts\run_field_capture_server.py
```

Endpoint:

- `GET /field-capture`
- `POST /api/field-capture/upload`
- `GET /api/field-capture/job/<job_id>`
- `GET /api/field-capture/result/<job_id>`
- `GET /api/field-capture/ping`
- `GET /operator`

Jika model belum ada, hasil ringkas tetap menerima upload dan mengembalikan status `MODEL_NOT_READY`.
