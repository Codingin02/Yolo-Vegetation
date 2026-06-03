# Phase 16 Remote Realtime Streaming Runbook

Mode ini menyiapkan field capture browser HP ke laptop processing server untuk uji realtime kasar. Ini bukan aplikasi mobile, bukan APK, bukan Flutter, bukan React Native, dan bukan PWA standalone.

## Peran Sistem

- HP: browser field capture untuk kamera/frame, GPS, dan metadata.
- Laptop: Flask processing server, YOLO/auto measurement nanti, ETA risk, report CSV/Sheets-ready, dan peta.
- Spreadsheet/map: report dan tracking snapshot/stable, bukan realtime video monitor.

## Jalankan Server Laptop

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Server menampilkan URL lokal, LAN, dan instruksi tunnel.

## LAN Debug Mode

Gunakan hanya untuk debug satu jaringan:

```text
http://<IP-LAPTOP>:5000/field-capture
```

Pada HTTP LAN, kamera/GPS otomatis dapat diblokir browser HP. Gunakan file upload fallback bila perlu.

## Remote HTTPS Tunnel Mode

Target field trial beda jaringan memakai HTTPS public tunnel:

```powershell
ngrok http 5000
```

atau:

```powershell
cloudflared tunnel --url http://localhost:5000
```

Jangan simpan token/authtoken tunnel di Git. Setelah tunnel aktif, buka dari HP:

```text
https://<public-tunnel-url>/field-capture
```

Kamera/GPS otomatis lebih mungkin aktif pada secure context HTTPS.

## Cara Pakai di HP

1. Buka URL `/field-capture`.
2. Tekan `Mulai Deteksi Pohon`.
3. Izinkan kamera dan GPS bila browser meminta izin.
4. Sistem mengirim maksimal 1 frame/detik ke laptop.
5. Laptop memproses frame latest-only.
6. Jika latensi lebih dari 3 detik, frame lama di-drop.
7. Tekan `Kirim Snapshot Report` untuk menulis CSV/map.

## Status Jika Model Belum Ada

Jika custom YOLO model belum tersedia, UI tetap berjalan tetapi menampilkan:

```text
MODEL_NOT_READY
NO_FAKE_DETECTION_MODEL_NOT_READY
```

Tidak ada bounding box palsu, model palsu, klaim akurasi, atau GPS palsu.

## Policy Clearance 3 Meter

Parameter prototype:

- `CONTACT_OR_OVERLAP`: clearance <= 0.
- `UNSAFE_WITHIN_3M`: 0 < clearance < 3.
- `WARNING_APPROACHING_3M`: 3 <= clearance < 4.
- `SAFE`: clearance >= 4.

Display HP memakai integer meter floor agar tidak terlihat lebih aman dari kondisi sebenarnya. Contoh 2.75 m tampil sebagai 2 m.

## Report

Realtime frame tidak menulis report per frame. CSV/map ditulis hanya saat:

- operator klik `Kirim Snapshot Report`,
- hasil stabil dan cooldown report dipenuhi,
- atau auto-report mode nanti diaktifkan eksplisit.

Map marker hanya dibuat jika GPS valid.

## Troubleshooting

- HP tidak bisa akses: cek URL tunnel/LAN, firewall, dan port 5000.
- Kamera/GPS tidak aktif: gunakan HTTPS tunnel, cek permission browser, atau pakai upload file fallback.
- Latensi tinggi: sistem akan drop frame lama dan mempertahankan latest-only.
- Tunnel putus: server tidak crash; buka ulang URL tunnel baru.
- Jangan menjalankan import label copy, build dataset final, atau training aktual dari mode ini.
