# Environmental Risk Model Plan

Phase 4 hanya menyediakan skeleton. Belum ada model prediksi ilmiah final.

## Input Kandidat

- `soil_ph`
- `rainfall_mm`
- `humidity_percent`
- `temperature_c`
- `season_label`
- `tree_species`
- `distance_to_conductor_m`
- `growth_stage`
- `maintenance_history`

## Status Saat Ini

Jika input belum lengkap, fungsi mengembalikan:

```text
DATA_NOT_READY
```

Jika semua input tersedia, fungsi tetap mengembalikan:

```text
RULE_BASED_STUB
```

Artinya bobot risiko belum final dan masih menunggu Deep Research.

## Deep Research Nanti

Sumber yang harus dipakai nanti:

- BPS
- BMKG
- KLHK
- data.go.id
- OpenStreetMap
- literatur pohon sono
- dokumen PLN terkait ROW/pemeliharaan jaringan

Tidak ada klaim pH tanah, curah hujan, musim, atau faktor Surabaya yang dibuat tanpa sumber.
