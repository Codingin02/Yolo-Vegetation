# Environmental Data Sources Surabaya Perak

Setiap titik inspeksi memakai GPS masing-masing. Jangan mengunci satu koordinat untuk semua titik.

Adapter yang disiapkan:

- BMKG untuk cuaca/prakiraan/musim bila tersedia.
- NASA POWER untuk meteorologi berbasis koordinat.
- SoilGrids untuk tanah global seperti pH jika data lokal belum ada.
- Manual CSV override untuk data PLN/BPS/survei lapangan.
- Open-Meteo sebagai fallback opsional.

Parameter minimal:

- latitude,
- longitude,
- observation_date,
- season_label,
- rainfall_7d_mm,
- rainfall_30d_mm,
- temperature_avg_c,
- humidity_avg_percent,
- soil_ph,
- soil_moisture_proxy,
- wind_speed_avg,
- data_source,
- freshness_status,
- source_confidence.

Fetch tidak boleh massal. Cache hanya di `data/cache/` atau `data/runtime/`, yang di-ignore Git.
