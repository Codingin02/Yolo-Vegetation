# Phase 14 JTM 20 kV Asset Profile Notes

File `configs/electrical_asset_profiles.yaml` menyiapkan parameter untuk JTM 20 kV Distribution, tetapi belum mengunci angka sebagai standar final PLN.

## Cara Mengisi Tinggi Acuan

Operator dapat mengisi `pole_height_reference_m` setelah salah satu data berikut tersedia:

- data PLN/ULP untuk tipe tiang di titik inspeksi,
- pengukuran lapangan terverifikasi,
- dokumen standar resmi yang relevan,
- calibration board atau objek referensi yang difoto bersama tiang.

## Kenapa Nullable

Auto measurement butuh konversi pixel ke meter:

```text
meter_per_pixel = pole_height_reference_m / pole_pixel_height
```

Jika tinggi acuan tidak tersedia, sistem harus mengembalikan `REFERENCE_HEIGHT_REQUIRED`, bukan mengarang tinggi tiang/kabel.

## Catatan

- Candidate 9, 11, 12, 13, 14 m hanya daftar konfigurasi awal untuk dipilih setelah ada konfirmasi.
- `minimum_clearance_policy_m` dan `transformer_clearance_policy_m` harus diisi dari standar/lapangan yang valid.
- Semua hasil Phase 14 adalah kerangka auto-measurement, bukan klaim akurasi final.
