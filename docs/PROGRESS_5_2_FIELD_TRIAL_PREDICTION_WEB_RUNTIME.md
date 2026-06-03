# Progress 5.2 Field Trial Prediction Web Runtime

Status target:

```text
PROGRESS_5_2_FIELD_TRIAL_PREDICTION_WEB_RUNTIME_READY_WITH_MODEL_NOT_READY_SAFE_MODE
```

## Scope

Progress 5.2 adalah Kelompok 2: runtime, prediksi, tampilan HP browser, report, map, operator workflow, diagnostics, dan field trial readiness.

Di luar scope:

- labeling makesense.ai
- dataset final
- raw data
- export makesense
- model weight
- training final

## Runtime

HP hanya browser field client. Laptop menjalankan Flask server dan melakukan processing.

Endpoint utama:

```text
GET  /field-capture
GET  /api/runtime/status
GET  /api/runtime/public-links
GET  /api/model/status
GET  /api/calibration/status
POST /api/realtime/frame
POST /api/field/manual-prediction
POST /api/field/snapshot-report
WS   /ws/realtime-detect
```

## Prediksi Manual/Provisional

Formula Progress 5.2:

```text
threshold = 3.0 m
eta_days = (clearance_m - threshold) / adjusted_growth_rate_m_per_day
```

Jika `clearance_m <= 3.0`, ETA menjadi `0` dan status risiko adalah `ALREADY_WITHIN_UNSAFE_ZONE`.

Contoh:

```text
clearance_m = 5.0
growth_rate_m_per_day = 0.01
eta_days = 200
```

Jika model custom belum tersedia:

```text
model_status = MODEL_NOT_READY
detections = []
inference_source = MANUAL_PROVISIONAL_NO_MODEL
```

Tidak ada fake detection.

## Output

Output resmi field trial:

- CSV lokal spreadsheet-ready
- map report jika GPS valid

Jika Google credential belum tersedia:

```text
GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY
```

Runtime output berada di folder ignored, terutama:

```text
outputs/reports
data/runtime
```

## Validasi

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\phase5_2_field_trial_prediction_gate.py
.\venv\Scripts\python.exe scripts\operator_command_center.py --phase5-2-gate
```

## Safety

Progress ini belum klaim akurasi final. Hasil manual/provisional adalah research/field-trial aid sampai label, training, model custom, kalibrasi, dan validasi lapangan selesai.
