# Spreadsheet Monitoring Schema

Monitoring utama Phase 8 adalah spreadsheet dan peta.

Output:

- `outputs/reports/vegetation_risk_report.csv`
- `outputs/reports/vegetation_risk_report.xlsx`

Schema wajib berada di `src/ulp_project/spreadsheet_schema.py` dan `configs/spreadsheet_schema.yaml`.

Kolom utama meliputi:

- identitas inspeksi,
- GPS,
- species,
- aset listrik terdekat,
- tinggi pohon/aset,
- clearance minimum,
- parameter lingkungan,
- growth rate,
- ETA hari/bulan,
- priority,
- rekomendasi aksi,
- status model/kalibrasi/data lingkungan.

Google Sheets live auth tidak wajib. Jika credential tidak tersedia, gunakan CSV/XLSX-ready output lokal.
