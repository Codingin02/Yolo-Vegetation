# Phase 6.6 Pohon Sono Growth Prior Limitations

Dataset pohon sono Surabaya Utara 2015-2025 adalah prior proxy, bukan observasi lapangan final.

Status wajib:

- `PROXY_NOT_FIELD_OBSERVED` untuk semua row dari Excel proxy.
- `GROWTH_PRIOR_READY_PROXY_DATASET` jika workbook tersedia dan sheet utama valid.
- `GROWTH_PRIOR_DATASET_NOT_FOUND` jika workbook tidak tersedia.
- `GROWTH_PRIOR_DATASET_INVALID` jika workbook rusak atau sheet wajib hilang.

Rumus awal deterministic:

`growth_m_per_year = base_growth * ph_factor * rainfall_factor * temperature_factor * humidity_factor * soil_fertility_factor * urban_stress_factor * season_factor`

Rumus ini sengaja heuristic dan di-clamp agar tidak menjadi klaim absolut.

Batas literatur yang dipakai sebagai catatan prior:

- Pterocarpus indicus cocok pada suhu sekitar 24-27 C.
- Curah hujan tahunan cocok sekitar 900-2200 mm.
- Tanah neutral sampai slightly acidic, sandy/clay loam, lebih sesuai untuk prior.

Catatan penting:

- Browser GPS bukan RTK atau survey-grade.
- Growth prior tidak menggantikan observasi tinggi pohon lapangan.
- ETA clearance hanya boleh muncul jika `clearance_m` berasal dari geometry/calibration yang cukup.
- Jika model YOLO masih `MODEL_NOT_READY`, runtime tidak boleh membuat deteksi palsu.
- Field calibration dan data pruning/observasi nyata perlu dipakai untuk naik ke `FIELD_CALIBRATED`.
