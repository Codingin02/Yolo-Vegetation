# Progress 8 Plan C Implementation Report

## Ringkasan

Sistem monitoring vegetasi berbasis snapshot capture dengan YOLO-assisted object detection, AI-assisted visual validation, Python geometry, dan quarterly growth-risk prediction sudah ditambahkan sebagai jalur baru Plan C.

Plan C tidak mengubah jalur lama `/field-camera` dan tidak memakai loop deteksi live. HP berperan sebagai kamera, GPS client, dan uploader snapshot. Flask backend memproses foto setelah shutter.

## Route Yang Tersedia

Page route:
- `GET /plan-c`
- `GET /plan-c/capture/<session_id>`
- `GET /plan-c/processing/<session_id>`
- `GET /plan-c/result/<session_id>`
- `GET /plan-c/map`
- `GET /plan-c/developer/<session_id>`

API route:
- `POST /api/plan-c/session/start`
- `POST /api/plan-c/session/tree-anchor`
- `POST /api/plan-c/session/snapshot`
- `GET /api/plan-c/session/<session_id>/status`
- `GET /api/plan-c/session/<session_id>/result`

Tambahan aman:
- `GET /plan-c/session/<session_id>/annotated.jpg`

## Storage

Root runtime:
- `data/runtime/plan_c`

Session file:
- `data/runtime/plan_c/sessions/<session_id>/original.jpg`
- `data/runtime/plan_c/sessions/<session_id>/annotated.jpg`
- `data/runtime/plan_c/sessions/<session_id>/result.json`
- `data/runtime/plan_c/sessions/<session_id>/developer.json`
- `data/runtime/plan_c/sessions/<session_id>/metadata.json`
- `data/runtime/plan_c/sessions/<session_id>/yolo_raw.json`
- `data/runtime/plan_c/sessions/<session_id>/ai_raw.json`
- `data/runtime/plan_c/sessions/<session_id>/geometry.json`

Append-only:
- `data/runtime/plan_c/spreadsheet/plan_c_records.csv`
- `data/runtime/plan_c/spreadsheet/plan_c_records.jsonl`
- `data/runtime/plan_c/map/plan_c_markers.json`

## Dataset Growth

Reference proxy pohon_sono ditempatkan di:
- `data/reference/pohon_sono_growth/pohon_sono_growth_reference.xlsx`
- `data/reference/pohon_sono_growth/pohon_sono_growth_reference.csv`
- `data/reference/pohon_sono_growth/plan_c_growth_profile.json`
- `data/reference/pohon_sono_growth/plan_c_growth_sources.csv`

Sumber lokal:
- `data/growth_model/pohon_sono/dataset_pohon_sono_surabaya_utara_2015_2025_lengkap_v2.xlsx`

Status dataset:
- `data_source_type = proxy`
- `observed_or_proxy = proxy`
- `growth_profile_status = GROWTH_PROFILE_READY_PROXY`
- `confidence_level = proxy_reference_moderate_requires_field_validation`

Limitasi utama: dataset adalah proxy/model-prior berbasis literatur dan data lingkungan, bukan observasi lapangan langsung.

## Status Komponen

YOLO:
- Berjalan hanya setelah snapshot diterima.
- Resolver mencari model pada path prioritas Plan C.
- Jika model tidak tersedia, status `YOLO_MODEL_NOT_READY`, `detections = []`, dan `manual_review_required = true`.
- `annotated.jpg` tetap dibuat sebagai salinan snapshot dengan label fallback bila library image tersedia.

AI validator:
- Opsional.
- Jika API key tidak tersedia, status `AI_VALIDATOR_DISABLED`.
- Tidak membuat bounding box dan tidak menghitung clearance.

Geometry:
- Python geometry menjadi sumber perhitungan.
- Jika bbox target belum cukup, status `INSUFFICIENT_GEOMETRY_DATA` dan risk `DATA_TIDAK_CUKUP`.
- Manual input operator dapat dipakai untuk clearance provisional dengan label `manual_operator_input`.

Growth prediction:
- Loader JSON prioritas utama, CSV fallback, Excel validasi tambahan jika `openpyxl` tersedia.
- CSV loader tahan terhadap leading blank line.
- Jika reference hilang, status `GROWTH_PROFILE_MISSING` dan prediction `data tidak cukup`.

Map:
- Marker ditambahkan hanya bila GPS valid.
- Jika tidak ada GPS, status `NO_GPS_NO_MARKER`; tidak ada GPS palsu.
- Map tetap terbuka saat marker kosong.

## Cara Menjalankan Server

```powershell
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Buka:
- `http://127.0.0.1:5000/plan-c`

## Cara Membuka Dari HP Via Ngrok

```powershell
ngrok http 5000
```

Lalu buka dari HP:
- `https://<url-ngrok>/plan-c`

Jangan commit URL tunnel.

## Validasi

```powershell
.\venv\Scripts\python.exe -m py_compile src\ulp_project\plan_c_session.py src\ulp_project\plan_c_storage.py src\ulp_project\plan_c_yolo.py src\ulp_project\plan_c_ai_validator.py src\ulp_project\plan_c_geometry.py src\ulp_project\plan_c_growth_model.py src\ulp_project\plan_c_processor.py src\ulp_project\plan_c_map.py src\ulp_project\plan_c_routes.py scripts\plan_c_smoke.py
.\venv\Scripts\python.exe scripts\plan_c_smoke.py
cmd /c "git diff --check"
```

## Limitasi Akademik

Sistem ini membantu dokumentasi dan screening risiko vegetasi berbasis snapshot. Output risk dan prediction adalah indikasi kuartalan, bukan klaim akurasi final PLN dan bukan pengganti pengukuran manual PLN.

## File Yang Dibuat

- `src/ulp_project/plan_c_session.py`
- `src/ulp_project/plan_c_storage.py`
- `src/ulp_project/plan_c_yolo.py`
- `src/ulp_project/plan_c_ai_validator.py`
- `src/ulp_project/plan_c_geometry.py`
- `src/ulp_project/plan_c_growth_model.py`
- `src/ulp_project/plan_c_processor.py`
- `src/ulp_project/plan_c_map.py`
- `src/ulp_project/plan_c_routes.py`
- `src/ulp_project/templates/plan_c_home.html`
- `src/ulp_project/templates/plan_c_capture.html`
- `src/ulp_project/templates/plan_c_processing.html`
- `src/ulp_project/templates/plan_c_result.html`
- `src/ulp_project/templates/plan_c_map.html`
- `src/ulp_project/templates/plan_c_developer.html`
- `src/ulp_project/static/plan_c.css`
- `src/ulp_project/static/plan_c_capture.js`
- `src/ulp_project/static/plan_c_result.js`
- `scripts/plan_c_smoke.py`
- `docs/progress8/PLAN_C_IMPLEMENTATION_REPORT.md`

## File Atau Folder Yang Tidak Disentuh

- `data/raw/`
- `data/gps/`
- `data/processed/`
- `data/exports/`
- `data/dataset_yolo/`
- `dataset_botol/`
- `results/`
- `runs/`
- `weights/`
- `models/`
- file `.pt`
- file `.onnx`
- file `.env`
- token, credential, dan URL tunnel

## Progress 8.2 Single-Class Runtime Correction

Plan C runtime dikoreksi ke mode `PLAN_C_SINGLE_CLASS_POHON_SONO`.

- Detector operator: `YOLOv8`.
- Target aktif runtime: `pohon_sono`.
- Output bbox aktif hanya untuk `pohon_sono`.
- Konduktor dan struktur penyangga tidak lagi diperlakukan sebagai class YOLO aktif pada runtime ini.
- Ketiadaan konduktor tidak lagi menghasilkan hard blocker `DATA_TIDAK_CUKUP_KONDUKTOR_TIDAK_TERVALIDASI`.
- Jika pohon_sono terdeteksi tetapi clearance belum bisa dihitung, hasil masuk review manual tanpa membuat clearance palsu.
- Runner khusus Plan C tersedia di `scripts/run_plan_c_server.py` dan `scripts/run_plan_c_system.ps1`.

Validasi yang diharapkan:

```text
PLAN_C_SINGLE_CLASS_POHON_SONO_SMOKE_PASS
```

Run command final:

```powershell
.\scripts\run_plan_c_system.ps1
```

Manual:

```powershell
.\venv\Scripts\python.exe scripts\run_plan_c_server.py --host 0.0.0.0 --port 5000
ngrok http 5000
```
