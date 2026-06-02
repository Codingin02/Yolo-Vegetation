# Spreadsheet And Report Export

Phase 5 menyediakan export report operator ke:

- CSV
- JSON
- Markdown
- XLSX opsional jika `openpyxl` sudah tersedia

Default script adalah dry-run:

```powershell
.\venv\Scripts\python.exe scripts\export_system_report.py --mode dry-run
```

Write mode hanya menulis ke:

```text
outputs/reports/
```

Tidak ada output runtime yang ditulis ke `data/metadata`, `results`, `runs`, atau folder dataset.
