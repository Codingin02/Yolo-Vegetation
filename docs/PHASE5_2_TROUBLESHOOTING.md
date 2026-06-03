# Phase 5.2 Troubleshooting

## HP Tidak Bisa Buka Localhost

`localhost` di HP berarti HP itu sendiri, bukan laptop.

Gunakan:

```text
http://<IP-LAPTOP>:5000/field-capture
```

Cari IP laptop:

```powershell
ipconfig
```

## Kamera Tidak Muncul

Kemungkinan:

- halaman dibuka lewat HTTP LAN
- permission browser ditolak
- browser tidak menyediakan camera API pada context tersebut

Status yang benar:

```text
CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT
CAMERA_PERMISSION_DENIED
```

Solusi:

- pakai HTTPS ngrok/cloudflared
- cek permission browser
- gunakan fallback upload image

## GPS Ditolak atau Timeout

Status yang benar:

```text
GPS_PERMISSION_DENIED
GPS_TIMEOUT
GPS_SOURCE_MANUAL
```

Jika latitude/longitude diisi manual, sistem menandai manual source. Jika GPS kosong, map marker tidak dibuat.

## Ngrok Tunnel Expired

Jalankan ulang:

```powershell
ngrok http 5000
```

Buka URL HTTPS baru dari HP.

## Port 5000 Bentrok

Gunakan port lain:

```powershell
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5001
```

Tunnel:

```powershell
ngrok http 5001
```

## Firewall Windows

Jika HP satu WiFi tidak bisa akses laptop:

- pastikan server bind `0.0.0.0`
- izinkan Python pada Windows Firewall private network
- coba endpoint `/api/latency/ping`

## Model Belum Tersedia

Status normal:

```text
MODEL_NOT_READY
detections = []
```

Prediksi manual/provisional tetap bisa diuji. Jangan membuat model palsu.

## Calibration Belum Tersedia

Status normal:

```text
CALIBRATION_NOT_READY
MANUAL_PROVISIONAL
```

Hasil masih field trial prototype sampai kalibrasi lapangan valid.

## CSV atau Map Tidak Muncul

CSV hanya ditulis saat klik `Kirim Snapshot Report`.

Map hanya dibuat jika GPS valid. Tanpa GPS:

```text
NO_GPS_NO_MARKER
```

Output berada di folder ignored:

```text
outputs/reports
```
