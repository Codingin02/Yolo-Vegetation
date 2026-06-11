# Plan C Free Vision YOLO-Compatible Report

## Baseline

Baseline sebelum tahap ini: `ef02f45 Harden Progress 8 Plan C field trial runtime`.

Target tahap: `PROGRESS_8_2_PLAN_C_FREE_VISION_YOLO_COMPATIBLE_READY`.

## Tujuan

Tahap ini menambahkan adapter deteksi visual free-only yang optional untuk jalur snapshot `/plan-c`. Output yang masuk ke operator dinormalisasi menjadi format YOLO-compatible: `Detection`, `YOLO Format`, `Bounding Box`, `Confidence`, `Prediction`, dan `Review`.

## Perubahan Backend

- Menambahkan config loader free-only tanpa mewajibkan key.
- Menambahkan schema normalisasi bbox YOLO-compatible untuk tiga class final: `struktur_penyangga`, `konduktor`, `pohon_sono`.
- Menambahkan adapter optional untuk Gemini, Groq, dan OpenRouter free model dengan timeout dan fallback controlled.
- Menambahkan consensus sederhana dengan NMS per class.
- Menambahkan renderer YOLO-compatible untuk `annotated.jpg`.
- Menambahkan endpoint `GET /api/plan-c/free-vision/status` yang tidak menampilkan secret.
- Mengintegrasikan hasil final detection ke `plan_c_processor.py` sebelum Python geometry dan growth prediction.

## Perubahan Frontend

- Result operator menampilkan ringkasan ringkas tanpa nama engine eksternal.
- Result operator menampilkan `detection_status`, `detection_count`, `operator_output_format`, `review_status`, geometry, growth proxy, GPS, map link, dan developer link.
- Developer page tetap menjadi tempat raw diagnostics yang sudah diredaksi.

## Konfigurasi

`.env.example` berisi nama variabel berikut tanpa value rahasia:

- `PLAN_C_VISION_MODE=free_only`
- `PLAN_C_OPERATOR_HIDE_PROVIDER=true`
- `PLAN_C_FREE_VISION_PRIMARY=gemini`
- `PLAN_C_FREE_VISION_SECONDARY=groq`
- `PLAN_C_FREE_VISION_TERTIARY=openrouter`
- `GEMINI_API_KEY=`
- `GROQ_API_KEY=`
- `OPENROUTER_API_KEY=`

File `.env` lokal tetap tidak boleh di-commit.

## Prediction

Prediction tetap dihitung oleh Python geometry dan growth dataset proxy lokal. Adapter deteksi hanya membantu menghasilkan bbox YOLO-compatible jika tersedia. Data growth tetap `data_source_type = proxy` dan `observed_or_proxy = proxy`.

## Limitasi

1. Image detection bersifat provisional.
2. Hasil tetap perlu review lapangan.
3. Jika layanan gratis rate limited atau tidak dikonfigurasi, sistem fallback ke `DATA_TIDAK_CUKUP`.
4. Jika key tidak ada, sistem tetap berjalan tanpa crash.
5. Prediction window tetap estimasi awal berbasis geometry dan growth proxy, bukan klaim akurasi final.

## Cara Menjalankan Server

```powershell
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Buka lokal:

```text
http://127.0.0.1:5000/plan-c
```

## Cara Menjalankan Ngrok

```powershell
ngrok http 5000
```

Buka dari HP:

```text
https://<url-ngrok>/plan-c
```

Gunakan URL dari terminal ngrok. Jangan menyimpan public tunnel URL ke Git.

## Cara Uji

```powershell
.\venv\Scripts\python.exe scripts\plan_c_free_vision_smoke.py
.\venv\Scripts\python.exe -m pytest tests\test_plan_c_free_vision_schema.py tests\test_plan_c_free_vision_no_key.py tests\test_plan_c_free_vision_operator_ui_redaction.py
```

## Cara Mengisi Env Lokal

Salin variabel dari `.env.example` ke `.env` lokal dan isi key hanya di mesin sendiri. `.env` sudah diabaikan oleh Git.
