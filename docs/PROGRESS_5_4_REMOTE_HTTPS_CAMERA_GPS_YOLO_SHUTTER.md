# Progress 5.4 Remote HTTPS Camera GPS YOLO Shutter

Status target:

`PROGRESS_5_4_REMOTE_HTTPS_CAMERA_GPS_YOLO_SHUTTER_READY_MODEL_NOT_READY_SAFE_MODE`

Arsitektur final field trial:

`HP browser -> public HTTPS tunnel Ngrok/Cloudflare -> Flask backend laptop -> YOLO/runtime/report/map`

Laptop tetap menyala sebagai server. HP boleh memakai paket data atau Wi-Fi lain. LAN URL `http://192.168.x.x:5000/field-capture` hanya debug lokal, bukan workflow final.

## Run

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Terminal kedua:

```powershell
ngrok http 5000
```

HP buka:

```text
https://<public-tunnel-url>/field-capture
```

## Status Penting

- `HTTPS_PUBLIC_READY`: benar untuk field trial beda jaringan.
- `LAN_HTTP_DEBUG_ONLY`: hanya debug; kamera/GPS HP bisa diblokir.
- `MODEL_NOT_READY`: model custom belum tersedia, bukan error fatal.
- `DEBUG_COCO_YOLO_NOT_FIELD_MODEL`: uji overlay eksplisit, bukan hasil final PLN.
- `GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY`: CSV lokal tetap siap.

YOLO final tetap menunggu labeling, training, model custom valid, dan kalibrasi lapangan. Sistem tidak membuat deteksi palsu.
