# Phase 5.3 Windows Firewall And Port Troubleshooting

Script Progress 5.3 hanya diagnostic. Script tidak membuat firewall rule, tidak meminta admin otomatis, dan tidak menjalankan service permanen.

## Cek Port Dan Runtime

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\operator_command_center.py --actual-runtime-smoke
.\venv\Scripts\python.exe scripts\operator_command_center.py --ngrok-probe
```

Endpoint:

```text
GET /api/runtime/tunnel-status
GET /api/network/health
GET /api/latency/ping
```

## Jika Port 5000 Bentrok

Gejala:

- server gagal start
- browser tidak bisa membuka `/field-capture`
- diagnostic menampilkan port sudah listening oleh proses lain

Action:

1. Tutup server lama bila masih berjalan.
2. Jalankan lagi:

```powershell
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

3. Jika tetap bentrok, gunakan port lain untuk field trial lokal dan sesuaikan command ngrok.

## Jika LAN IP Tidak Bisa Dibuka HP

Kemungkinan:

- HP dan laptop beda jaringan.
- Laptop memakai hotspot/VPN yang memblokir LAN.
- Windows Firewall memblokir Python.

Action manual:

1. Buka Windows Security.
2. Firewall & network protection.
3. Allow an app through firewall.
4. Pastikan Python diizinkan untuk Private network.
5. Untuk HP paket data, lebih realistis pakai:

```powershell
ngrok http 5000
```

## Catatan Flask

Command field trial:

```powershell
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Ini hanya field-trial/dev runtime agar HP dapat mengakses laptop. Ini bukan production deployment permanen.
