# GPS Map Spreadsheet Contract

Kontrak Phase 4 menyiapkan fungsi GPS, peta, dan spreadsheet tanpa memaksa data final.

## GPS

- Input kandidat nanti: GPX, KML, TXT, CSV.
- Folder sumber nyata tetap `data/gps/01_field_points`.
- Jika GPS belum tersedia atau belum bisa diparse, status wajib `GPS_DATA_NOT_READY`.
- Tidak boleh membuat koordinat palsu.

## Map

Default command adalah dry-run:

```powershell
.\venv\Scripts\python.exe scripts\build_field_map.py
```

Untuk menulis peta HTML nanti:

```powershell
.\venv\Scripts\python.exe scripts\build_field_map.py --mode write
```

Mode write belum perlu dijalankan sebelum data GPS siap.

## Spreadsheet

Default command adalah dry-run:

```powershell
.\venv\Scripts\python.exe scripts\export_project_metadata_csv.py
```

Untuk menulis CSV lokal nanti:

```powershell
.\venv\Scripts\python.exe scripts\export_project_metadata_csv.py --mode write --output docs\sample_project_points_manifest.csv
```

Google Sheets API tidak dipakai di Phase 4 dan credential tidak boleh masuk repo.
