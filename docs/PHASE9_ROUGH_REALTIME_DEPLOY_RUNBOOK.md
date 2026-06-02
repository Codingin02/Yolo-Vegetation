# Phase 9 Rough Realtime Deploy Runbook

Phase 9 membuat jalur percobaan kasar hidup:

HP browser input -> laptop Flask processing server -> ETA manual/provisional -> CSV monitoring -> map jika GPS ada.

Ini bukan aplikasi mobile, bukan APK, bukan Flutter, bukan React Native, dan bukan PWA. HP hanya membuka halaman browser.

## Jalankan Diagnostic

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\diagnose_field_capture_deploy.py
```

Output diagnostic:

- `outputs/runtime/phase9_deploy_diagnostic.json`
- `outputs/runtime/phase9_deploy_diagnostic.txt`

## Jalankan Server

```powershell
.\venv\Scripts\python.exe scripts\run_field_capture_server.py --host 0.0.0.0 --port 5000
```

Server akan menampilkan URL localhost dan URL LAN IP laptop.

Jika HP tidak bisa akses:

- pastikan HP dan laptop satu WiFi/hotspot,
- cek Windows Firewall untuk Python/port 5000,
- buka `/api/latency/ping`,
- jika kamera browser tidak aktif karena HTTP/LAN, gunakan upload file/foto dari galeri,
- jika beda jaringan, gunakan ngrok/cloudflared HTTPS manual tanpa menyimpan token.

## Output

- CSV: `outputs/reports/vegetation_risk_monitoring.csv`
- Map: `outputs/reports/vegetation_risk_map.html` bila GPS tersedia.
