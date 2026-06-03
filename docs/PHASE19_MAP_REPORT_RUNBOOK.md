# Phase 19 Map Report Runbook

Map report hanya membuat marker jika GPS valid.

```powershell
.\venv\Scripts\python.exe scripts\export_latest_risk_map.py
```

Jika GPS kosong:

```text
NO_GPS_NO_MAP_MARKER
```

Tidak boleh membuat GPS palsu.
