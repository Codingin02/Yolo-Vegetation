# Progress 5.4 Realtime YOLO Camera Geometry

Status target:

`PROGRESS_5_4_REALTIME_CAMERA_GEOMETRY_READY_MODEL_NOT_READY_SAFE_MODE`

Progress 5.4 mengubah `/field-capture` menjadi workflow kamera HP browser dengan overlay, GPS background, shutter capture, geometri pixel-to-meter, smoothing, dan autosave CSV saat tombol jepret ditekan.

## Run

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\operator_command_center.py --camera-ui-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --geometry-math-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --shutter-report-smoke
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

## Safe Mode

Jika model custom belum tersedia:

- `MODEL_NOT_READY`
- `detections=[]`
- no fake detection
- shutter tetap menyimpan snapshot/metadata dengan status jujur
- CSV tetap lokal dan spreadsheet-ready

Debug COCO hanya opt-in untuk uji overlay:

`DEBUG_COCO_YOLO_NOT_FIELD_MODEL`
