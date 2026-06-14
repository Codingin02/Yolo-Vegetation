# Plan C AI Backend Finalizer

## Tujuan

Patch ini menyelesaikan backend Plan C tanpa mengubah frontend operator. Runtime tetap
single-class `pohon_sono`, tetapi backend sekarang menjalankan alur System C yang lebih
lengkap:

1. YOLOv8 lokal sebagai detector utama `pohon_sono`.
2. Gemini, Grok/xAI, dan OpenRouter sebagai validator visual opsional.
3. Geometry dan growth model Python sebagai sumber risk/prediction.
4. Renderer backend untuk annotated image dengan zona aman, pantau, dan tebang.
5. Append-only CSV, JSONL, dan map marker tetap dipertahankan.

## Kebijakan Detector

Runtime aktif bukan multi-class. Class aktif hanya:

- `pohon_sono`

Konduktor dan struktur penyangga tidak menjadi class YOLO runtime. Keduanya hanya boleh
menjadi konteks visual, referensi manual, atau bahan review lapangan. Ketiadaan
konduktor tidak boleh lagi menjadi hard blocker utama seperti
`DATA_TIDAK_CUKUP_KONDUKTOR_TIDAK_TERVALIDASI`.

Output backend utama:

- `runtime_mode = PLAN_C_SYSTEM_C_SINGLE_CLASS_POHON_SONO`
- `detector = YOLOv8`
- `ai_core_mode = THREE_PROVIDER_CONSENSUS`
- `multi_class_runtime = false`
- `conductor_required_for_detection = false`

## AI Core 3 Provider

Provider yang dipakai hanya sebagai validator visual:

1. Gemini (`GEMINI_API_KEY`)
2. Grok/xAI (`GROK_API_KEY` atau `XAI_API_KEY`)
3. OpenRouter (`OPENROUTER_API_KEY`)

`OPENAI_API_KEY` tidak dipakai pada jalur ini. Jika provider tidak memiliki key,
rate-limit, timeout, atau gagal parse, pipeline tetap berjalan dengan status terkontrol.
Provider tidak boleh membuat class konduktor/struktur sebagai bbox aktif dan tidak
menghitung clearance final.

## Bbox Final

Urutan pemilihan bbox pohon:

1. YOLOv8 lokal jika bbox `pohon_sono` valid.
2. AI consensus bbox hanya jika YOLOv8 tidak menghasilkan bbox dan bbox provider valid.
3. `NONE` jika tidak ada bbox valid.

AI bbox yang dipakai tetap berstatus review dan tidak dianggap ground truth final.

## Zona Backend

Annotated image sekarang selalu dirender backend dengan tiga band deterministik:

- Top band: `ZONA TEBANG`
- Middle band: `ZONA PANTAU`
- Lower band: `ZONA AMAN`

Jika conductor/manual geometry tidak tersedia, method adalah
`heuristic_band_without_manual_clearance`. Ini adalah visual risk guidance, bukan
pengukuran PLN final.

Jika manual clearance tersedia:

- `<= 3.0 m`: `ZONA_TEBANG`, window `0-3 bulan`
- `> 3.0 m` dan `<= 4.5 m`: `ZONA_PANTAU`, window `3-6 bulan`
- `> 4.5 m`: `ZONA_AMAN`, window `>12 bulan`

Jika tidak ada bbox pohon:

- `risk_status = DATA_TIDAK_CUKUP`
- `prediction_window = data tidak cukup`
- `clearance_estimate_m = null`

Backend tidak membuat clearance palsu.

## Growth Model

Growth tetap membaca data lokal:

- `data/reference/pohon_sono_growth/plan_c_growth_profile.json`
- `data/reference/pohon_sono_growth/pohon_sono_growth_reference.csv`
- `data/reference/pohon_sono_growth/plan_c_growth_sources.csv`
- `data/reference/pohon_sono_growth/pohon_sono_growth_reference.xlsx`

Status hasil memakai proxy:

- `growth_profile_status`
- `growth_rate_m_per_quarter`
- `data_source_type = proxy`
- `confidence_level`
- `limitations`

## Validasi

Validasi utama:

```powershell
.\venv\Scripts\python.exe -m py_compile src\ulp_project\plan_c_ai_core_consensus.py src\ulp_project\plan_c_processor.py src\ulp_project\plan_c_yolo.py src\ulp_project\plan_c_geometry.py src\ulp_project\plan_c_yolo_compatible_renderer.py scripts\plan_c_smoke.py scripts\plan_c_ai_backend_smoke.py scripts\run_plan_c_server.py
.\venv\Scripts\python.exe scripts\plan_c_smoke.py
.\venv\Scripts\python.exe scripts\plan_c_ai_backend_smoke.py
cmd /c "git diff --check"
```

Expected status:

- `PLAN_C_SINGLE_CLASS_POHON_SONO_SMOKE_PASS`
- `PLAN_C_AI_BACKEND_SYSTEM_C_SMOKE_PASS`

## Cara Menjalankan

```powershell
Set-Location E:\Projects\ULP_Project
.\scripts\run_plan_c_system.ps1
```

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

## Limitasi

Plan C adalah alat bantu estimasi dan review lapangan. Hasil zona, risk, dan
prediction bukan keputusan final PLN dan harus divalidasi dengan pengukuran manual.
