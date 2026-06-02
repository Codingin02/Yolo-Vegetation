# PLN Vegetation Risk Model Spec

Risk engine Phase 8 menilai vegetasi terhadap aset listrik:

- conductor/kabel,
- span atau bentangan kabel antar tiang,
- transformer/trafo,
- aset lain bila relevan.

## Priority

- `DANGER_NOW`: clearance <= 0.
- `CRITICAL`: ETA <= 30 hari.
- `HIGH`: ETA <= 90 hari.
- `MEDIUM`: ETA <= 180 hari.
- `LOW`: ETA > 180 hari.
- `INSUFFICIENT_DATA`: data clearance/growth/environment belum cukup.

## ETA

```text
days_to_contact = clearance_m / adjusted_growth_rate_m_per_day
```

Jika growth rate spesies null, status harus `GROWTH_RATE_NOT_READY`. Jika data lingkungan kurang dan provisional tidak diizinkan, status harus `INSUFFICIENT_ENVIRONMENTAL_DATA`.

Tidak ada klaim akurasi sampai YOLO, kalibrasi, data lingkungan, dan ground truth tersedia.
