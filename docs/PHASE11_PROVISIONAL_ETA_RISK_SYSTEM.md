# Phase 11 Provisional ETA Risk System

Sistem ini menghitung ETA kasar/provisional untuk risiko pohon terhadap kabel, span, atau trafo. Span adalah bentangan kabel di antara dua tiang; titik tengah span dapat menjadi titik risiko karena sag.

## Rumus Demo

Jika input manual lengkap:

```text
eta_days = clearance_m / adjusted_growth_rate_m_per_day
eta_months = eta_days / 30.4375
```

Jika `clearance_m <= 0`, status menjadi `IMMEDIATE_ACTION`. Jika clearance atau growth rate belum ada, ETA `null` dan status `INSUFFICIENT_DATA`.

## Provisional vs Final

Mode sekarang memakai `PROVISIONAL_MANUAL_INPUT`. Ini belum klaim akurasi final. Presisi final menunggu:

- label YOLO selesai dan valid,
- model YOLO dilatih dengan izin operator,
- kalibrasi tinggi/jarak lapangan,
- data lingkungan nyata/manual CSV,
- ground truth inspeksi.

## Input HP Browser

HP membuka `/field-capture`, lalu mengirim point ID, species, asset type, clearance manual, growth rate manual, GPS opsional, foto opsional, dan notes. Laptop menghitung ETA dan menulis CSV + map jika GPS tersedia.

## Parameter Lingkungan

Field yang disiapkan: musim, curah hujan, suhu, kelembapan, soil moisture, pH tanah, radiasi matahari, evapotranspirasi, dan angin. Jika kosong, sistem tidak mengarang nilai; status lingkungan menjadi partial/manual required.
