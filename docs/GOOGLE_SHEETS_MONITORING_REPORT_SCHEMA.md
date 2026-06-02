# Google Sheets Monitoring Report Schema

Monitoring utama adalah CSV/Google Sheets dan peta, bukan aplikasi HP.

Output lokal:

- `outputs/reports/vegetation_risk_report.csv`
- `outputs/reports/latest_vegetation_risk_report.json`

Jika credential Google Sheets tidak tersedia, status harus `SHEETS_NOT_CONFIGURED` atau dry-run, bukan error.

Kolom wajib mengikuti `src/ulp_project/sheets_report_schema.py`, meliputi identitas laporan, GPS, species, aset terdekat, tinggi pohon, clearance, parameter lingkungan, ETA, risk status, rekomendasi aksi, status model, status kalibrasi, status data lingkungan, dan catatan operator.

Credential tidak boleh masuk Git.
