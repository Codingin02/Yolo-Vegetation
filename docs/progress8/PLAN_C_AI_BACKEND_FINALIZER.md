# Plan C AI Backend Finalizer

## Tujuan

Patch backend Plan C menyelesaikan alur System C tanpa mengubah frontend operator.
Halaman utama tetap `/plan-c`, runner final tetap `scripts/run_plan_c_system.ps1`,
dan UI operator tetap memakai tampilan lama.

## Arsitektur

Pipeline final:

1. Snapshot/manual capture dari operator.
2. YOLOv8 lokal sebagai detector objek hasil training dataset label lokal.
3. Gemini, Groq Console/GroqCloud, dan OpenRouter sebagai consensus validation.
4. Python geometry/risk engine.
5. Growth prediction proxy dari data lokal.
6. Renderer backend untuk `annotated.jpg` dengan zona aman, pantau, dan tebang.
7. Append-only CSV, JSONL, dan map marker.

Cloud AI provider tidak dilatih dengan dataset lokal. Dataset label lapangan/review
dipakai untuk training model lokal YOLOv8. Provider cloud hanya validator visual,
second opinion, rekomendasi review/retake, dan tidak membuat klaim final PLN.

## Provider Final

Provider aktif:

1. Gemini via `GEMINI_API_KEY`
2. Groq Console/GroqCloud via `GROQ_API_KEY`
3. OpenRouter via `OPENROUTER_API_KEY`

`OPENAI_API_KEY` tidak dipakai pada jalur ini. `XAI_API_KEY` bukan provider aktif
dan hanya dicatat sebagai legacy key jika ada. Pipeline tidak memakai endpoint
`api.x.ai`.

Jika provider gagal, timeout, rate-limit, atau tidak memiliki key, pipeline tetap
berjalan dengan status terkontrol dan tanpa mencetak secret.

## Detector Lokal

Backend sekarang memprioritaskan model:

1. `models/plan_c_system_c_detector/best.pt`
2. `models/plan_c_ai_detector/best.pt`
3. `runs/detect/plan_c_system_c_detector_v2*/weights/best.pt`
4. fallback lama jika ada

Jika model System C ada, status runtime:

- `PLAN_C_SYSTEM_C_DETECTOR_READY`
- `model_policy = system_c_detector`
- class policy: `0 struktur_penyangga`, `1 konduktor`, `2 pohon_sono`

Jika hanya model lama ada, backend tetap bisa fallback ke `single_class_pohon_sono`.
Ketiadaan konduktor tidak menjadi hard blocker. Jika konduktor terdeteksi, posisinya
dipakai untuk zona yang lebih baik; jika tidak, sistem memakai heuristic bands dan
manual review.

## Zona Backend

`annotated.jpg` selalu dirender backend dengan:

- `ZONA TEBANG`
- `ZONA PANTAU`
- `ZONA AMAN`
- bbox `pohon_sono`
- bbox `konduktor` jika terdeteksi model
- bbox `struktur_penyangga` jika terdeteksi model
- risk status, prediction window, dan growth rate

Metode zona:

- `conductor_based` jika bbox konduktor tersedia
- `manual_clearance` jika operator memberi clearance manual
- `heuristic_band_without_manual_clearance` jika konduktor/manual clearance tidak ada

Backend tidak membuat fake conductor, fake clearance, atau fake pengukuran PLN.

## Validasi

Status smoke final:

```text
PLAN_C_SYSTEM_C_BACKEND_SMOKE_PASS
PLAN_C_AI_BACKEND_SYSTEM_C_SMOKE_PASS
```

Run command:

```powershell
Set-Location E:\Projects\ULP_Project
.\scripts\run_plan_c_system.ps1
```

Laptop:

```text
http://127.0.0.1:5000/plan-c
```

HP:

```text
https://<ngrok-url>/plan-c
```

## Limitasi

Plan C adalah alat bantu estimasi dan review lapangan. Hasil zona, risk, dan
prediction bukan keputusan final PLN dan harus divalidasi dengan pengukuran manual.
