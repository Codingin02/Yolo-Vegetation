# Final Operator Command Sequence

Semua command dijalankan dari:

```powershell
Set-Location E:\Projects\ULP_Project
```

## Diagnose

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --diagnose
```

## Print Links

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --print-links
```

## Progress 5.2 Field Trial Smoke

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --check-model
.\venv\Scripts\python.exe scripts\operator_command_center.py --field-trial-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --phase5-2-gate
```

## Run Remote Server

```powershell
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

## Tunnel Manual

```powershell
ngrok http 5000
# atau
cloudflared tunnel --url http://localhost:5000
```

HP membuka:

```text
https://<public-tunnel-url>/field-capture
```

## Field Trial Dry Run

```powershell
.\venv\Scripts\python.exe scripts\run_field_trial_operator.py --mode dry-run
```

## Export Report

```powershell
.\venv\Scripts\python.exe scripts\export_google_sheets_ready_csv.py --mode local
```

## Export Map

```powershell
.\venv\Scripts\python.exe scripts\export_latest_risk_map.py
```

## Setelah Labeling dan Training Selesai

Masukkan `best.pt` ke salah satu path kandidat yang di-ignore, misalnya:

```text
models/field/best.pt
```

Lalu jalankan:

```powershell
.\venv\Scripts\python.exe scripts\check_model_handoff_ready.py --dry-load
```

Jangan training aktual, import label copy, atau build dataset final tanpa aba-aba operator.
# Progress 5.3 Field Trial Execution

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\operator_command_center.py --diagnose
.\venv\Scripts\python.exe scripts\operator_command_center.py --print-links
.\venv\Scripts\python.exe scripts\operator_command_center.py --ngrok-probe
.\venv\Scripts\python.exe scripts\operator_command_center.py --actual-runtime-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --evidence-pack
.\venv\Scripts\python.exe scripts\operator_command_center.py --progress5-3-gate
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Tunnel manual:

```powershell
ngrok http 5000
```

HP:

```text
https://<ngrok-public-url>/field-capture
https://<ngrok-public-url>/field-trial-checklist
```

Status HP fisik tidak boleh diklaim berhasil sebelum operator mengisi checklist:

```text
HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION
```

# Progress 5.4 Realtime Camera Geometry

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\operator_command_center.py --public-tunnel-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --camera-ui-contract-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --geometry-math-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --shutter-autosave-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --runtime-tunnel-sync-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --favicon-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --map-public-link-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --progress5-4-gate
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Tunnel:

```powershell
ngrok http 5000
```

HP:

```text
https://<ngrok-public-url>/field-capture
```

LAN `http://192.168.x.x:5000/field-capture` hanya debug. Workflow final field trial beda jaringan wajib public HTTPS tunnel.

Urutan HP:

1. Izinkan Kamera.
2. Izinkan GPS.
3. Mulai Deteksi.
4. Jepret / Shutter.
5. Buka Spreadsheet/CSV.
6. Buka Map.
