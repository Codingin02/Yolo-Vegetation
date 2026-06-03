# Phase 5.2 HP Field Capture Operator Guide

## Audit Awal

```powershell
Set-Location E:\Projects\ULP_Project
git status --short --untracked-files=all
git branch --show-current
git rev-parse --short HEAD
```

Branch harus:

```text
system-finalization-no-label-touch
```

## Run Server

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Server akan mencetak:

- Local URL
- LAN URL kandidat
- Health URL
- Ping URL
- instruksi ngrok/cloudflared jika public tunnel belum diset

## Buka HP

Jika satu WiFi/hotspot:

```text
http://<IP-LAPTOP>:5000/field-capture
```

Jika beda jaringan atau kamera/GPS ditolak di HTTP LAN, gunakan HTTPS tunnel:

```text
https://<public-tunnel-url>/field-capture
```

## Urutan Uji

1. Klik `Test koneksi laptop/server`.
2. Klik `Ambil GPS HP`.
3. Klik `Cek izin kamera`.
4. Klik `Start kamera`.
5. Isi form field trial.
6. Untuk test manual, isi:

```text
point_id = V001_pohon_sono
species = pohon_sono
asset_type = span
clearance_m = 5.0
growth_rate_m_per_day = 0.01
```

7. Klik `Jalankan Prediksi Manual/Provisional`.
8. Pastikan output `eta_days = 200`.
9. Klik `Kirim Snapshot Report`.
10. Klik `Salin link report CSV` atau `Buka map report jika tersedia`.

## Output yang Benar Saat Model Belum Ada

```text
model_status = MODEL_NOT_READY
detections = []
confidence_status = MANUAL_PROVISIONAL
```

Jika GPS kosong:

```text
map_marker_status = NO_GPS_NO_MARKER
```

## Catatan

HP bukan aplikasi mobile. Tidak ada APK, Flutter, React Native, atau PWA standalone. HP hanya browser input-output untuk field trial.
