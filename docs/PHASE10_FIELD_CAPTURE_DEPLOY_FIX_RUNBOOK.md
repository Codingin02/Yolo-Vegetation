# Phase 10 Field Capture Deploy Fix Runbook

Tujuan: HP membuka browser field capture, laptop tetap server pemrosesan Flask.

## Jalankan dari laptop

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\diagnose_field_capture_deploy.py
.\venv\Scripts\python.exe scripts\run_field_capture_server.py --host 0.0.0.0 --port 5000
```

Server akan menampilkan:

- Local URL: `http://127.0.0.1:5000/field-capture`
- LAN URL kandidat: `http://<IP-LAPTOP>:5000/field-capture`
- Health URL
- Ping latency URL

## Buka dari HP

Gunakan:

```text
http://<IP-LAPTOP>:5000/field-capture
```

Jangan pakai `localhost` dari HP karena itu menunjuk ke HP sendiri.

## Troubleshooting

- Pastikan HP dan laptop satu WiFi/hotspot.
- Pastikan Windows Firewall mengizinkan Python atau port 5000 pada Private Network.
- Jika port 5000 bentrok, ulangi dengan `--port 5001`.
- Jika IP laptop berubah, jalankan server ulang dan baca LAN URL kandidat.
- Jika browser HP tidak memberi izin kamera/GPS, gunakan upload foto dari galeri dan isi latitude/longitude manual bila tersedia.
- Jika beda jaringan, gunakan ngrok/cloudflared HTTPS secara manual tanpa menyimpan token ke Git.
- Jangan membuat APK, Flutter, React Native, atau aplikasi mobile.

## Smoke Test Tanpa HP

```powershell
.\venv\Scripts\python.exe scripts\phase10_lan_deploy_smoke.py
```

Status yang diharapkan: `PHASE10_ROUGH_FIELD_CAPTURE_DEPLOY_PASS`.
