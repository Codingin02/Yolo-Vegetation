# Span Cable Trafo Risk Model

Risiko vegetasi dinilai terhadap aset listrik terdekat:

- konduktor/kabel,
- span atau bentang kabel di antara dua tiang,
- trafo,
- tiang/struktur pendukung jika relevan.

## Input Minimum

- `clearance_m`: estimasi jarak vegetasi ke aset listrik.
- `species_base_growth_rate_m_per_day`: laju tumbuh spesies dari kalibrasi/literatur.
- multiplier musim, hujan, kelembapan, suhu, pH tanah, soil moisture, riwayat pangkas, dan kalibrasi lokal.

## ETA

```text
adjusted_growth_rate_m_per_day =
  base_growth_rate
  * season_multiplier
  * rainfall_multiplier
  * humidity_multiplier
  * temperature_multiplier
  * soil_ph_multiplier
  * soil_moisture_multiplier
  * pruning_history_multiplier
  * local_calibration_multiplier

eta_days = clearance_m / adjusted_growth_rate_m_per_day
eta_months = eta_days / 30.44
```

Jika data tidak lengkap, sistem mengembalikan `NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA` dan `eta_days = null`.

## Status Risiko

- `AMAN_MONITOR`
- `PERLU_MONITORING`
- `JADWALKAN_PEMANGKASAN`
- `PRIORITAS_TINGGI`
- `KRITIS_SEGERA`
- `NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA`
