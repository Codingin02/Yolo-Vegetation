# Phase 5.4 Map And CSV Autosave Guide

Report ditulis hanya saat operator menekan `Jepret / Shutter` atau `Simpan Laporan`.

CSV lokal:

```text
outputs/reports/field_capture_autosave.csv
```

Snapshot runtime:

```text
data/runtime/field_captures/
```

Map runtime:

```text
outputs/maps/progress5_4_latest_map.html
```

Jika GPS valid, map membuat marker dan link `/field-maps/progress5_4_latest_map.html` bisa dibuka melalui domain Ngrok yang sama. Jika GPS tidak valid, status `NO_GPS_NO_MARKER` dan sistem tidak membuat koordinat palsu.

Google Sheets dan Google Maps credential tidak wajib untuk field trial. Status yang benar:

- `GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY`
- `GOOGLE_MAPS_NOT_CONFIGURED_FOLIUM_OR_BASIC_MAP_READY`
