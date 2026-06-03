# Report and Map Output Guide

CSV lokal adalah output utama sebelum Google Sheets live.

```powershell
.\venv\Scripts\python.exe scripts\export_google_sheets_ready_csv.py --mode local
```

Map:

```powershell
.\venv\Scripts\python.exe scripts\export_latest_risk_map.py
```

Report tidak ditulis setiap frame realtime. Trigger yang valid:

- `MANUAL_SNAPSHOT`
- `STABLE_RESULT_COOLDOWN`
- `FIELD_REVIEW`

Map marker hanya dibuat jika GPS valid. Jika GPS kosong, status `NO_GPS_NO_MAP_MARKER`.
