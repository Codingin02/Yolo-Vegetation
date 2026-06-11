# Plan C Upload Mode Operator Guide

## Jalankan Server

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Buka laptop:

```text
http://127.0.0.1:5000/plan-c/upload
```

Jika memakai HP:

```powershell
ngrok http 5000
```

Buka:

```text
https://<ngrok-url>/plan-c/upload
```

## Alur Operator

1. Buka `/plan-c/upload`.
2. Pilih foto yang memuat pohon, konduktor, dan struktur penyangga jika tersedia.
3. Izinkan GPS jika browser meminta izin.
4. Isi `point_id`, nama operator, dan catatan jika perlu.
5. Klik `Upload Foto`.
6. Di halaman review, cek thumbnail dan status GPS/model.
7. Klik `Jalankan Deteksi dan Prediksi`.
8. Buka result page.
9. Gunakan developer page hanya untuk diagnostics teknis.

## Interpretasi Result

- `ZONA_AMAN`: clearance lebih dari 3 m dan data cukup.
- `ZONA_PANTAU`: clearance berada di rentang pantau atau mendekati threshold.
- `ZONA_TEBANG`: clearance kritis atau ada indikasi visual serius yang tetap perlu review.
- `DATA_TIDAK_CUKUP`: objek, GPS, atau geometry belum cukup untuk menghitung clearance.

Jika muncul warning `CONDUCTOR_CLASS_WEAK_OR_NOT_DETECTED`, hasil konduktor belum cukup kuat dan perlu validasi manual.

## Batasan

- Sistem tidak menggantikan pengukuran manual.
- GPS HP dapat memiliki akurasi terbatas.
- AI Vision Detector adalah alat bantu field trial.
- AI provider validator optional tidak membuat bounding box final.
- Jangan memakai result sebagai klaim akurasi final PLN.
