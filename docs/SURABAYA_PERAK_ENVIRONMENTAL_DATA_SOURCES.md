# Surabaya Perak Environmental Data Sources

Setiap titik inspeksi harus memakai GPS masing-masing. Jangan mengunci satu koordinat untuk seluruh ULP Perak.

## Sumber yang Disiapkan

- BMKG untuk musim jika tersedia.
- Open-Meteo untuk cuaca historis/forecast jika nanti dipakai.
- NASA POWER untuk cuaca/solar proxy jika nanti dipakai.
- SoilGrids untuk tanah jika nanti dipakai.
- CSV manual dari survei lapangan.

## Parameter

- `rainfall_mm_7d`
- `rainfall_mm_30d`
- `rainfall_mm_90d`
- `temperature_c_mean_7d`
- `temperature_c_mean_30d`
- `humidity_mean_7d`
- `humidity_mean_30d`
- `wind_speed_mean_7d`
- `season_label`
- `soil_ph`
- `soil_moisture_proxy`
- `soil_texture`
- `data_source`
- `source_timestamp`
- `data_quality`

Season logic:

- `BMKG_SEASON` jika data BMKG tersedia.
- `RAINFALL_PROXY_SEASON` jika fallback dari curah hujan 30/90 hari.
- `UNKNOWN_SEASON` jika data belum ada.
