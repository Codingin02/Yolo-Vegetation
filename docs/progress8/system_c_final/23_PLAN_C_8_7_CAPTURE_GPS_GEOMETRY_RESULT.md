# Plan C 8.7 Capture GPS Geometry Result

## UI Capture

Capture Plan C diperbarui menjadi alur field trial:

1. Operator membuka session capture.
2. Muncul konfirmasi posisi di bawah pohon.
3. Jika operator memilih tidak, browser kembali ke `/plan-c`.
4. Jika operator memilih ya, kamera fullscreen dibuka dan GPS watch dimulai.

Operator page tidak menampilkan status chip panjang seperti camera ready, GPS ready, atau server ready. Detail teknis tetap disimpan untuk developer diagnostics.

## Gallery Upload

Capture page menyediakan tombol ikon galeri tanpa teks. File picker memakai `accept=image/*` dan tidak memaksa `capture`, sehingga operator bisa memilih foto dari galeri. Foto galeri dikirim ke endpoint snapshot yang sama dengan shutter kamera.

## Lens Normal Selection

Kamera memakai `facingMode=environment` sebagai default. Setelah izin kamera diberikan, browser menjalankan `enumerateDevices` dan memilih kamera belakang yang labelnya tidak mengandung `ultra`, `ultrawide`, `wide angle`, atau `0.5x`. Saat pindah lensa, track stream lama dihentikan sebelum stream baru diminta.

## GPS Anchor Tracking

Saat operator mengonfirmasi sudah di bawah pohon, frontend menjalankan `navigator.geolocation.watchPosition` dengan:

```text
enableHighAccuracy = true
maximumAge = 0
timeout = 10000
```

Posisi valid pertama disimpan sebagai `tree_anchor_gps`. Posisi terbaik terakhir saat shutter/galeri dipakai disimpan sebagai `shutter_gps`. Track ringkas dikirim ke backend.

## Distance dan Estimasi Langkah

Backend menghitung ulang jarak anchor ke shutter menggunakan rumus Haversine. Estimasi langkah:

```text
estimated_steps_from_anchor = gps_distance_from_anchor_m / 0.75
```

Nilai tersebut ditampilkan sebagai estimasi langkah, bukan sensor langkah aktual.

## Geometry Formula

Jika `struktur_penyangga`, `konduktor`, dan pohon terdeteksi, geometri memakai struktur sebagai referensi tinggi:

```text
meter_per_pixel = structure_height_m / structure_bbox_height_px
tree_height_m = tree_bbox_height_px * meter_per_pixel
conductor_height_m = (ground_reference_y_px - conductor_center_y_px) * meter_per_pixel
clearance_estimate_m = conductor_height_m - tree_height_m
```

Sumber tinggi struktur dicatat sebagai `STRUCTURE_HEIGHT_MANUAL`, `STRUCTURE_HEIGHT_CONFIG_DEFAULT`, atau `STRUCTURE_HEIGHT_UNKNOWN`.

## Prediction Months/Days

Prediction menggunakan growth profile yang tersedia:

```text
growth_rate_m_per_day = adjusted_growth_rate_m_per_quarter / 91.25
remaining_clearance_to_tebang_m = clearance_estimate_m - 3.0
prediction_days = floor(remaining_clearance_to_tebang_m / growth_rate_m_per_day)
```

Jika clearance sudah kurang atau sama dengan 3 meter, output menjadi `0 bulan 0 hari`.

## Zone Overlay Rule

Zona dihitung dari posisi konduktor:

```text
ZONA_TEBANG = 0-3 m di bawah konduktor
ZONA_PANTAU = 3-6 m di bawah konduktor
ZONA_AMAN = batas 6 m sampai ground_reference_y
```

Zona aman tidak memakai bawah foto secara otomatis. Jika konduktor atau skala tidak valid, zona presisi tidak diklaim.

## Validation

Validasi yang dijalankan:

```text
py_compile Plan C runtime files
scripts/plan_c_capture_ui_v5_smoke.py
scripts/plan_c_gps_anchor_geometry_smoke.py
scripts/plan_c_gallery_upload_smoke.py
scripts/plan_c_prediction_days_smoke.py
git diff --check
```

## Menunggu Pipeline Dataset

Dataset download, pre-label, review Roboflow, training gate final, dan model registry final tetap dikerjakan melalui PowerShell/dataset pipeline terpisah. Task ini tidak menjalankan download dataset, scraping, atau training berat.
