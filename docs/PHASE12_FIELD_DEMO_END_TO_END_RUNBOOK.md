# Phase 12 Field Demo End-to-End Runbook

Alur demo kasar:

```text
HP browser -> submit inspection -> laptop proses ETA -> CSV monitoring -> map risiko
```

Ini bukan aplikasi HP. HP hanya field capture browser.

## A. Jalankan Server

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\diagnose_field_capture_deploy.py
.\venv\Scripts\python.exe scripts\run_realtime_field_pipeline.py --mode server --host 0.0.0.0 --port 5000
```

## B. Buka dari HP

```text
http://<IP-LAPTOP>:5000/field-capture
```

Isi minimal:

- `point_id`
- `species`
- `asset_type`
- `clearance_m`
- `growth_rate_m_per_day`
- GPS bila tersedia
- foto opsional
- notes

## C. Output Laptop

- CSV: `outputs/reports/vegetation_risk_monitoring.csv`
- Map: `outputs/reports/vegetation_risk_map.html`

Spreadsheet menampilkan ETA hari/bulan, risk priority, action recommendation, environmental completeness, dan confidence status.

## D. Demo Sekali Command

```powershell
.\venv\Scripts\python.exe scripts\phase12_end_to_end_rough_demo.py
```

Status yang diharapkan: `PHASE12_END_TO_END_ROUGH_DEMO_PASS`.

## Keterbatasan

Demo ini kasar/provisional. Final presisi menunggu label YOLO, training, kalibrasi lapangan, data lingkungan nyata, dan validasi ground truth.
