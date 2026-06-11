# Plan C Field Trial Hardening Report

## Baseline

Baseline commit: `49be2e3 Implement Progress 8 Plan C snapshot processing runtime`.

Target hardening: `PROGRESS_8_1_PLAN_C_FIELD_TRIAL_HARDENING_READY`.

## Tujuan

Hardening ini menyiapkan Plan C untuk uji lapangan HP melalui HTTPS tunnel. Fokus perubahan adalah stabilitas shutter, browser camera/GPS, idempotency upload, redaction developer diagnostics, validasi route, dan smoke test lapangan.

Plan C tetap snapshot/manual capture, bukan realtime. HP hanya menjadi kamera, GPS client, dan uploader foto. Backend Flask memproses foto setelah shutter.

## File Yang Diaudit

- `src/ulp_project/flask_app.py`
- `src/ulp_project/plan_c_routes.py`
- `src/ulp_project/plan_c_session.py`
- `src/ulp_project/plan_c_storage.py`
- `src/ulp_project/plan_c_yolo.py`
- `src/ulp_project/plan_c_ai_validator.py`
- `src/ulp_project/plan_c_geometry.py`
- `src/ulp_project/plan_c_growth_model.py`
- `src/ulp_project/plan_c_processor.py`
- `src/ulp_project/plan_c_map.py`
- `src/ulp_project/templates/plan_c_*.html`
- `src/ulp_project/static/plan_c*`
- `scripts/plan_c_smoke.py`
- `docs/progress8/PLAN_C_IMPLEMENTATION_REPORT.md`
- `data/reference/pohon_sono_growth/*`

## Perubahan Backend

- Menambahkan route `GET /api/plan-c/runtime/ui-version`.
- Menambahkan idempotency persistent di `metadata.json`.
- Menambahkan duplicate response `PLAN_C_SNAPSHOT_ALREADY_PROCESSED` dan `DUPLICATE_IGNORED`.
- Memastikan duplicate dengan `idempotency_key` sama tidak append CSV/JSONL/map lagi.
- Menambahkan status GPS yang lebih eksplisit: `GPS_READY`, `GPS_NOT_READY`, `GPS_PERMISSION_DENIED`, dan `GPS_LOW_ACCURACY_EVIDENCE_ONLY`.
- Menambahkan `point_id`, `idempotency_key`, dan `gps_status` ke result.
- Result page untuk result belum siap sekarang memberi status `PLAN_C_PROCESSING`, bukan traceback.

## Perubahan Frontend

- Camera capture memakai fallback bertingkat:
  1. `facingMode ideal environment`, `width ideal 1920`, `height ideal 1080`
  2. `facingMode environment`
  3. `video true`
- Audio tidak diminta.
- Status camera menampilkan `CAMERA_API_UNAVAILABLE`, `CAMERA_PERMISSION_DENIED`, atau status controlled lain.
- GPS memakai `enableHighAccuracy: true`, `maximumAge: 0`, `timeout: 15000`.
- Snapshot tetap bisa dikirim saat GPS belum siap, tanpa koordinat palsu.
- Shutter membuat `idempotency_key` per tap dan tombol dinonaktifkan selama upload.
- Result operator diringkas dan tidak menampilkan raw JSON panjang.
- Developer page menampilkan UI version kecil.

## Perubahan Growth Loader

- JSON tetap prioritas utama.
- CSV dan sources CSV tetap tahan leading blank line.
- Excel tetap opsional; jika `openpyxl` tidak tersedia, status fallback aman.
- Output loader menandai `data_source_type = proxy`, `observed_or_proxy = proxy`, dan `not_final_accuracy_claim = true`.
- Tidak ada pencarian data web dan tidak ada angka growth baru di luar file reference.

## Perubahan YOLO Wrapper

- Jika model tidak ada: `YOLO_MODEL_NOT_READY`.
- Jika `ultralytics` tidak tersedia: `YOLO_RUNTIME_UNAVAILABLE`.
- Jika inference error: `YOLO_INFERENCE_FAILED`.
- Semua failure menghasilkan `detections = []` dan tidak membuat bbox palsu.
- Annotated image fallback hanya watermark/status aman, bukan kotak palsu.

## Perubahan Storage Append-Only

- Runtime tetap di `data/runtime/plan_c`.
- CSV, JSONL, dan marker map tidak direset saat server start.
- Duplicate idempotency tidak append row/line/marker baru.
- Marker hanya bertambah bila GPS valid.
- `.gitignore` diperkuat untuk runtime, report, media, model artifact, dan secret.

## Smoke Test

Smoke baru:
- `scripts/plan_c_field_trial_hardening_smoke.py`

Smoke ini memvalidasi:
- route page dan API Plan C,
- upload snapshot via data URL,
- upload raw base64 tanpa GPS,
- idempotency duplicate,
- append-only CSV/JSONL/map,
- route UI version,
- missing growth profile fallback,
- CSV blank-first-line loader,
- developer redaction,
- `git diff --check`.

Output sukses:
- `PROGRESS_8_1_PLAN_C_FIELD_TRIAL_HARDENING_SMOKE_PASS`

## Pytest Plan C

Ditambahkan:
- `tests/test_plan_c_growth_loader.py`
- `tests/test_plan_c_idempotency.py`
- `tests/test_plan_c_routes_no_500.py`
- `tests/test_plan_c_developer_redaction.py`

## Status Komponen

YOLO:
- Tetap post-capture.
- Tidak ada klaim akurasi final.
- Jika model candidate terdeteksi, status dapat `YOLO_MODEL_READY`.

AI validator:
- Opsional.
- Jika API key tidak tersedia, status `AI_VALIDATOR_DISABLED`.
- AI tidak menghitung clearance, bbox, atau prediction final.

Growth proxy:
- Dataset pohon_sono tetap proxy reference.
- Bukan observasi lapangan PLN.
- Bukan data biologis final.

## Limitasi Akademik

1. Data growth adalah proxy reference.
2. Hasil prediction window adalah estimasi awal kuartalan.
3. Sistem belum menggantikan pengukuran manual PLN.
4. Akurasi YOLO tidak diklaim sebelum ada ground truth dan validasi lapangan.
5. GPS HP punya keterbatasan akurasi.

## Cara Run Server

```powershell
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Buka lokal:

```text
http://127.0.0.1:5000/plan-c
```

## Cara Run Ngrok

```powershell
ngrok http 5000
```

Buka dari HP:

```text
https://<url-ngrok>/plan-c
```

Jangan commit URL tunnel.

## Cara Uji Dari HP

1. Buka `/plan-c`.
2. Klik `Get Started`.
3. Izinkan camera.
4. Izinkan GPS jika tersedia.
5. Tekan `Save Anchor` bila lokasi anchor sudah terbaca.
6. Ambil snapshot.
7. Tunggu halaman result.
8. Buka developer page hanya untuk diagnostic teknis.

## Cara Membaca Result

Operator result menampilkan:
- `session_id`
- `point_id`
- `risk_status`
- `manual_review_required`
- `prediction_window`
- estimasi geometry bila ada
- YOLO summary
- AI validator status
- GPS status
- growth proxy status
- limitations

Developer page menampilkan raw diagnostics yang sudah direduksi dari base64 panjang, secret, dan absolute project path.

## Troubleshooting

Camera denied:
- Status `CAMERA_PERMISSION_DENIED`.
- Izinkan kamera di browser atau reload halaman capture.

GPS denied:
- Status `GPS_PERMISSION_DENIED`.
- Snapshot tetap boleh dikirim, tetapi marker map tidak dibuat tanpa GPS valid.

Ngrok 404/502:
- Pastikan server Flask masih berjalan di port 5000.
- Jalankan ulang `ngrok http 5000`.

Model not ready:
- Status `YOLO_MODEL_NOT_READY`.
- Pipeline tetap membuat result dengan `DATA_TIDAK_CUKUP` dan manual review.

Growth file missing:
- Status `GROWTH_PROFILE_MISSING`.
- Prediction menjadi `data tidak cukup`.

Duplicate snapshot ignored:
- Response `PLAN_C_SNAPSHOT_ALREADY_PROCESSED` atau `DUPLICATE_IGNORED`.
- CSV/JSONL/map tidak bertambah untuk `idempotency_key` yang sama.
