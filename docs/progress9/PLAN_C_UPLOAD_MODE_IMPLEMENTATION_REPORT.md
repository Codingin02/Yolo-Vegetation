# Progress 9 - Plan C Upload Mode Implementation Report

Tanggal: 2026-06-12

## Tujuan

Progress 9 menambahkan jalur upload image untuk Plan C tanpa menghapus shutter/capture lama. Operator dapat memilih foto, mengambil GPS saat upload, membuat session, lalu menjalankan proses deteksi dan prediksi secara manual dari halaman review.

## Model Lokal

Status model:

- `models/plan_c_ai_detector/best.pt`: digunakan sebagai AI Vision Detector lokal.
- `models/plan_c_ai_detector/registry.json`: digunakan sebagai registry model.
- `runs/detect/plan_c_ai_detector_v1/results.csv`: tersedia sebagai hasil training.

Nama operator: `AI Vision Detector`.

Detail internal developer:

- `internal_engine = Ultralytics YOLO object detection`
- `model_path = models/plan_c_ai_detector/best.pt`

Catatan: hasil training boleh dipakai untuk uji sistem upload image, tetapi bukan klaim akurasi final PLN. Class `konduktor` masih lemah sehingga sistem memberi warning `CONDUCTOR_CLASS_WEAK_OR_NOT_DETECTED` jika konduktor tidak terdeteksi kuat.

## Route Baru

Halaman:

- `GET /plan-c/upload`
- `GET /plan-c/upload/review/<session_id>`
- `GET /plan-c/upload/result/<session_id>`
- `GET /plan-c/upload/developer/<session_id>`

API:

- `POST /api/plan-c/upload/start`
- `POST /api/plan-c/upload/process/<session_id>`
- `GET /api/plan-c/upload/status/<session_id>`
- `GET /api/plan-c/upload/result/<session_id>`

## Storage

Session upload tetap memakai root Plan C:

- `data/runtime/plan_c/sessions/<session_id>/original.jpg`
- `metadata.json`
- `ai_model_raw.json`
- `yolo_raw.json`
- `ai_raw.json`
- `geometry.json`
- `growth.json`
- `result.json`
- `developer.json`
- `annotated.jpg`

CSV/JSONL/map tetap append-only:

- `data/runtime/plan_c/spreadsheet/plan_c_records.csv`
- `data/runtime/plan_c/spreadsheet/plan_c_records.jsonl`
- `data/runtime/plan_c/map/plan_c_markers.json`

Jika session diproses ulang, append duplikat ditahan dengan status `DUPLICATE_IGNORED`.

## Pipeline

1. Operator upload image dan GPS.
2. Backend menyimpan `original.jpg` dan `metadata.json`.
3. Operator membuka review page.
4. Operator klik `Jalankan Deteksi dan Prediksi`.
5. Backend menjalankan AI Vision Detector lokal.
6. AI provider validator optional hanya memberi validasi visual, bukan bbox final.
7. Python geometry menghitung clearance jika objek cukup.
8. Zone engine mengklasifikasi `ZONA_AMAN`, `ZONA_PANTAU`, `ZONA_TEBANG`, atau `DATA_TIDAK_CUKUP`.
9. Growth model memberi prediction window jika clearance dan growth rate cukup.
10. Backend membuat result, developer diagnostics, annotated image, CSV/JSONL, dan marker jika GPS valid.

## Limitasi

- Tidak ada training ulang pada tahap ini.
- Tidak ada fake detection, fake GPS, fake mAP, atau fake accuracy.
- Jika konduktor tidak terdeteksi kuat, risk menjadi `DATA_TIDAK_CUKUP`.
- Clearance `0.0 m` tidak ditulis ketika data tidak cukup; nilai clearance menjadi `null`.
- Hasil adalah field trial dan perlu validasi manual.
