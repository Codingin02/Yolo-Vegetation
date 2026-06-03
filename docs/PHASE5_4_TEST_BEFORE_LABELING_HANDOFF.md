# Phase 5.4 Test Before Labeling Handoff

Jalankan:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\phase5_2_field_trial_prediction_gate.py
.\venv\Scripts\python.exe scripts\progress5_3_field_trial_execution_gate.py
.\venv\Scripts\python.exe scripts\progress5_4_geometry_math_smoke.py
.\venv\Scripts\python.exe scripts\progress5_4_camera_ui_smoke.py
.\venv\Scripts\python.exe scripts\progress5_4_shutter_report_smoke.py
.\venv\Scripts\python.exe scripts\progress5_4_realtime_yolo_geometry_gate.py
```

Jika Codex belum memegang HP fisik, status tetap:

`HP_PHYSICAL_DISPLAY_TEST_PENDING`

Yang perlu user buktikan lewat HP:

1. Public ngrok URL membuka `/field-capture`.
2. Preview kamera tampil.
3. GPS background aktif atau gagal dengan alasan jelas.
4. `Mulai Deteksi` tidak membuat fake detection saat model belum ada.
5. `Jepret / Shutter` menulis CSV.
6. Map membuat marker hanya jika GPS valid.

User boleh lanjut ke obrolan labeling setelah Progress 5.4 gate PASS dan workflow HP/shutter sudah dipahami. Labeling tetap Kelompok 1 dan harus dilakukan terpisah dari runtime Progress 5.4.
