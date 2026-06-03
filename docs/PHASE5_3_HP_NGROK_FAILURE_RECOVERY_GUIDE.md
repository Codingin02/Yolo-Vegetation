# Phase 5.3 HP Ngrok Failure Recovery Guide

Gunakan command:

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --ngrok-probe
.\venv\Scripts\python.exe scripts\operator_command_center.py --failure-recovery-smoke
```

Endpoint bantu:

```text
GET  /api/runtime/tunnel-status
POST /api/operator/failure-recovery
```

## Decision Tree

HP membuka `localhost`:

- Cause: localhost di HP berarti HP sendiri, bukan laptop.
- Action: buka `https://<ngrok-public-url>/field-capture`.
- Command: `ngrok http 5000`.

HP tidak bisa buka LAN IP:

- Cause: beda jaringan atau Windows Firewall.
- Action: pakai ngrok HTTPS untuk paket data, atau izinkan Python di Private Network.
- Command: `.\venv\Scripts\python.exe scripts\operator_command_center.py --ngrok-probe`.

Ngrok mati atau expired:

- Status: `PUBLIC_TUNNEL_NOT_RUNNING` atau `NGROK_CLI_FOUND_BUT_TUNNEL_NOT_RUNNING`.
- Action: jalankan ulang `ngrok http 5000`, pakai URL HTTPS baru.

Kamera tidak muncul:

- Cause: insecure context atau permission denied.
- Action: buka HTTPS ngrok URL, izinkan kamera, reload halaman.
- Fallback: upload image manual; jangan buat fake detection.

GPS permission denied atau timeout:

- Cause: permission lokasi browser/HP belum aktif atau sinyal belum siap.
- Action: aktifkan Location permission, ulangi Ambil GPS.
- Tanpa GPS: status map `NO_GPS_NO_MARKER`.

WebSocket gagal:

- Cause: proxy/tunnel/koneksi tidak stabil.
- Action: lanjut fallback HTTP 1 FPS.
- Catatan: report tetap hanya snapshot/manual submit, bukan setiap frame.

Report tidak tertulis:

- Cause: folder output tidak writable atau payload snapshot invalid.
- Action:

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --actual-runtime-smoke
```

Model belum tersedia:

- Status: `MODEL_NOT_READY`.
- Action: lanjut manual/provisional mode.
- Larangan: jangan klaim real model dan jangan buat deteksi palsu.

Kalibrasi belum tersedia:

- Status: `CALIBRATION_NOT_READY`.
- Action: hasil tetap provisional sampai profil kalibrasi lapangan dibuat.
