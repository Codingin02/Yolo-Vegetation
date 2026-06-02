# Calibration And Distance Estimation

Phase 5 menyiapkan fungsi estimasi jarak berbasis geometri piksel.

## Status

Jika konfigurasi kalibrasi belum tersedia, fungsi wajib mengembalikan:

```text
CALIBRATION_NOT_READY
```

## Threshold Operasional

Default konfigurasi:

- `danger`: `distance_m < 1.5`
- `warning`: `1.5 <= distance_m < 3.0`
- `safe`: `distance_m >= 3.0`
- `unknown`: kalibrasi/geometri belum tersedia

Ambang 3 meter dipakai sebagai threshold operasional perencanaan sistem. Dokumen ini tidak mengklaim threshold tersebut sebagai jarak legal final PLN.

## Fungsi

- `load_calibration_config()`
- `estimate_pixel_scale()`
- `estimate_object_distance_to_conductor()`
- `classify_clearance_risk()`
