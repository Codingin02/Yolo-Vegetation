# Environmental Data Sources for Surabaya Utara - Perak

Phase 6 hanya menyiapkan registry sumber data. Tidak ada scraping internet, tidak ada angka cuaca/tanah palsu, dan tidak ada klaim final.

## Sumber Cuaca yang Disiapkan

- BMKG manual atau API bila nanti tersedia.
- NASA POWER hourly bila nanti dipakai operator.
- Open-Meteo historical/forecast bila nanti dipakai operator.

## Sumber Tanah yang Disiapkan

- SoilGrids bila nanti dipakai operator.
- CSV manual survei lapangan.

## Parameter Didukung

- `temperature_2m_c`
- `relative_humidity_2m_percent`
- `precipitation_mm`
- `rainfall_7d_mm`
- `rainfall_30d_mm`
- `dry_days_count_14d`
- `wind_speed_10m_ms`
- `wind_gust_ms`
- `solar_radiation`
- `soil_ph`
- `soil_clay_percent`
- `soil_sand_percent`
- `soil_silt_percent`
- `soil_organic_carbon`
- `soil_bulk_density`
- `soil_moisture_proxy`
- `elevation_m`

## Template Manual

Gunakan:

```text
data/templates/environmental_manual_template.csv
```

Jika data tidak tersedia, kosongkan kolom. Sistem akan memberi `DATA_SOURCE_PARTIAL` atau `ENVIRONMENTAL_DATA_NOT_READY`, bukan mengarang angka.
