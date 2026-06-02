# Span Clearance and ETA Method

Span adalah bentangan kabel antara dua tiang. Titik tengah span dapat lebih rendah karena sag, sehingga clearance minimum pada span harus diperlakukan sebagai titik risiko.

## Clearance

Sistem menerima:

- `span_mid_sag_height_m`,
- `asset_height_m`,
- `crown_top_m`,
- `horizontal_distance_to_asset_m`,
- `uncertainty_m`,
- `clearance_source`.

Output:

- `vertical_clearance_m`,
- `minimum_clearance_m`,
- `uncertainty_m`,
- `calibration_status`,
- `calibration_method`.

## ETA

ETA dihitung hanya jika minimum clearance dan growth rate tersedia. Jika tidak, sistem mengembalikan `INSUFFICIENT_DATA`, bukan angka palsu.
