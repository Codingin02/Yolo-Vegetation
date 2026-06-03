# Phase 5.2 Ngrok / Cloudflared Field Trial Runbook

## Jalankan Server

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Local check:

```text
http://127.0.0.1:5000/field-capture
http://127.0.0.1:5000/api/network/health
http://127.0.0.1:5000/api/latency/ping
http://127.0.0.1:5000/api/runtime/public-links
```

## Ngrok Manual

```powershell
ngrok http 5000
```

Buka dari HP:

```text
https://<ngrok-url>/field-capture
```

## Cloudflared Manual

```powershell
cloudflared tunnel --url http://localhost:5000
```

Buka dari HP:

```text
https://<cloudflared-url>/field-capture
```

## Optional Runtime Public URL

Jika ingin runner mencetak public link:

```powershell
$env:TUNNEL_PUBLIC_URL="https://<public-tunnel-url>"
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Jangan tulis token atau URL runtime ini ke file tracked.

## Secure Context

Browser HP dapat menolak kamera/GPS pada HTTP LAN. Status yang mungkin muncul:

```text
LOCAL_DEV_CONTEXT
INSECURE_CONTEXT_CAMERA_GPS_MAY_FAIL
SECURE_CONTEXT_EXPECTED
CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT
GPS_PERMISSION_DENIED
GPS_TIMEOUT
```

Gunakan HTTPS tunnel untuk field trial beda jaringan atau jika permission kamera/GPS bermasalah.
