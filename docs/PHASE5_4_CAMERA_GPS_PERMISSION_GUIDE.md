# Phase 5.4 Camera GPS Permission Guide

Kamera dan GPS browser HP membutuhkan secure context. Jalur field trial adalah public HTTPS tunnel.

## Jika Kamera/GPS Tidak Muncul

- Address bar masih `http://192.168.x.x`: buka `https://<ngrok-public-url>/field-capture`.
- Status `INSECURE_CONTEXT_CAMERA_GPS_BLOCKED`: halaman sedang dibuka dari LAN HTTP.
- Status `GPS_PERMISSION_DENIED`: aktifkan izin lokasi di browser/Android lalu ulangi.
- Status `GPS_TIMEOUT`: pindah ke area terbuka dan ulangi `Izinkan GPS`.
- Status `LOW_ACCURACY`: GPS aktif tetapi akurasi lebih dari 20 meter.

GPS dipakai untuk metadata lokasi, evidence, grouping titik, peta, dan riwayat inspeksi. GPS tidak mengganti pixel-to-meter scaling kamera.
