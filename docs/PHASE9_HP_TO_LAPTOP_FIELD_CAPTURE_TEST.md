# Phase 9 HP to Laptop Field Capture Test

## Di Laptop

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_field_capture_server.py --host 0.0.0.0 --port 5000
```

## Di HP

Buka:

```text
http://<IP-LAPTOP>:5000/field-capture
```

Isi manual demo:

- `point_id`: `V001_pohon_sono`
- `species`: `pohon_sono`
- `asset_type`: `span`
- `clearance_m`: `0.3`
- `growth_rate_m_per_day`: `0.01`

Expected rough result:

- `eta_days`: `30.0`
- `eta_months`: sekitar `0.99`
- `risk_priority`: `CRITICAL`
- `mode`: `PROVISIONAL_MANUAL_DEMO`

Jika GPS tidak diberikan, map marker tidak dibuat dan reason `NO_GPS_NO_MAP_MARKER`.

ETA manual/provisional ini bukan klaim akurasi final.
