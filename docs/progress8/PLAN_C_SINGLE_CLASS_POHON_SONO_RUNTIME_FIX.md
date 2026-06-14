# Plan C Single-Class Pohon Sono Runtime Fix

## Alasan Koreksi

Runtime Plan C dikoreksi dari eksperimen multi-class menjadi mode aktif single-class untuk `pohon_sono`. Model YOLOv8 tetap boleh berasal dari registry yang sudah ada, tetapi output operator hanya memakai target aktif `pohon_sono`.

## Kebijakan Runtime

- Detector operator: `YOLOv8`.
- Runtime mode: `PLAN_C_SINGLE_CLASS_POHON_SONO`.
- Target aktif: `pohon_sono`.
- Bounding box aktif hanya untuk `pohon_sono`.
- `konduktor` dan `struktur_penyangga` tidak menjadi class YOLO runtime aktif.
- Jika model tidak tersedia, status menjadi `YOLO_MODEL_NOT_READY` dan detections kosong.

## Geometri dan Zona

Ketiadaan konduktor dari model tidak lagi menjadi hard blocker utama karena konduktor bukan class aktif runtime single-class. Jika YOLOv8 mendeteksi pohon_sono tetapi tidak ada referensi clearance/manual, hasil menjadi review manual:

- `geometry_status = INSUFFICIENT_GEOMETRY_DATA`
- `risk_status = POHON_SONO_DETECTED_REVIEW_REQUIRED` atau `ZONA_TEBANG_MANUAL_REVIEW`
- `manual_review_required = true`

Sistem tidak membuat clearance, konduktor, tiang, atau bbox palsu.

## UI Operator

Tampilan operator dikembalikan ke gaya sederhana:

- foto anotasi mempertahankan rasio asli,
- card result mengalir portrait,
- istilah operator memakai `YOLOv8`,
- detail teknis tetap di Developer page,
- tidak ada dump JSON di halaman operator.

## Runner Plan C

Runner khusus dibuat:

```powershell
.\scripts\run_plan_c_system.ps1
```

Runner ini menjalankan compile, smoke, server Plan C, memastikan `/plan-c` HTTP 200, lalu baru menjalankan ngrok bila tersedia.

Manual:

```powershell
.\venv\Scripts\python.exe scripts\run_plan_c_server.py --host 0.0.0.0 --port 5000
ngrok http 5000
```

Laptop:

```text
http://127.0.0.1:5000/plan-c
```

HP:

```text
https://<ngrok-url>/plan-c
```

## Validasi

Smoke wajib berakhir dengan:

```text
PLAN_C_SINGLE_CLASS_POHON_SONO_SMOKE_PASS
```

## Limitasi

Runtime ini adalah alat bantu estimasi field trial. Zona tebang/review bukan keputusan final PLN dan tetap memerlukan pengukuran manual.
