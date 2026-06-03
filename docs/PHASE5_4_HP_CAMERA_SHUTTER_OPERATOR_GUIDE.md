# Phase 5.4 HP Camera Shutter Operator Guide

## Urutan HP

1. Buka `https://<ngrok-public-url>/field-capture`.
2. Tekan `Izinkan Kamera`.
3. Tekan `Izinkan GPS`.
4. Pastikan status GPS `GPS_ACTIVE` atau `LOW_ACCURACY`.
5. Tekan `Mulai Deteksi`.
6. Lihat preview kamera dan overlay canvas.
7. Tekan `Jepret / Shutter`.
8. Tekan `Buka Spreadsheet/CSV`.
9. Tekan `Buka Map`.
10. Jika map `NO_GPS_NO_MARKER`, ulangi GPS atau catat alasan operator.

## Input Manual Yang Diizinkan

Workflow utama hanya memakai:

- `point_id`
- operator name opsional
- notes/keterangan operator

Input clearance, tinggi pohon, tinggi tiang, jarak kabel, dan growth rate hanya ada di `Advanced Debug Only` untuk kompatibilitas lama.

## Output

- snapshot runtime: `data/runtime/field_captures/`
- CSV: `outputs/reports/progress5_4_shutter_report.csv`
- map: `outputs/maps/progress5_4_latest_map.html` bila GPS valid

Folder runtime/output ini tidak boleh di-commit.
