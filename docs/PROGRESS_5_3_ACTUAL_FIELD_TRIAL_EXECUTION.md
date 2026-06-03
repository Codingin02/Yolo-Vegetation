# Progress 5.3 Actual Field Trial Execution

Status target:

`PROGRESS_5_3_FIELD_TRIAL_EXECUTION_RECOVERY_READY_HP_PHYSICAL_TEST_PENDING`

Progress 5.3 tidak mengulang endpoint, UI, ETA, report, map, atau gate Progress 5.2. Fokusnya adalah eksekusi uji lapangan, recovery saat HP/ngrok/browser gagal, dan evidence pack operator.

## Urutan Lapangan

Terminal laptop 1:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\operator_command_center.py --diagnose
.\venv\Scripts\python.exe scripts\operator_command_center.py --print-links
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Terminal laptop 2:

```powershell
ngrok http 5000
```

Terminal laptop 3:

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --ngrok-probe
```

HP:

```text
https://<ngrok-public-url>/field-capture
https://<ngrok-public-url>/field-trial-checklist
```

Langkah HP:

1. Tekan Test koneksi laptop/server.
2. Tekan Ambil GPS HP.
3. Tekan Start kamera.
4. Isi clearance dan growth rate manual, contoh 5.0 dan 0.01.
5. Jalankan Prediksi Manual/Provisional.
6. Kirim Snapshot Report.
7. Buka Field Trial Checklist dan simpan hasil uji HP.

Setelah HP selesai:

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --evidence-pack
.\venv\Scripts\python.exe scripts\operator_command_center.py --progress5-3-gate
```

## Status Jujur

- Jika ngrok belum aktif: `PUBLIC_TUNNEL_NOT_RUNNING`.
- Jika Codex belum menerima hasil HP fisik: `HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION`.
- Jika model custom belum ada: `MODEL_NOT_READY`, `detections=[]`.
- Jika kalibrasi belum ada: `CALIBRATION_NOT_READY`.
- Jika GPS tidak valid: map marker tidak dibuat dan status `NO_GPS_NO_MARKER`.

## Output Runtime

Evidence pack ditulis ke:

```text
data\runtime\field_trial_evidence\
```

Folder ini di-ignore Git. Jangan stage output runtime, screenshot, CSV hasil runtime, map runtime, token, credential, atau foto/video.
