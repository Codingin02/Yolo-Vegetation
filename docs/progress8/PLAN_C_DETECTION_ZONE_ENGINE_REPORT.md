# Plan C Detection Zone Engine Report

## Progress 8.3

Tahap ini menambahkan detection + zone engine untuk jalur snapshot `/plan-c`. Fokusnya adalah membuat output detection YOLO-compatible yang lebih berguna untuk field trial, menolak false-positive non-target, menghitung clearance saat tree + conductor tersedia, menggambar zona informatif pada `annotated.jpg`, dan menyimpan feedback operator secara append-only.

## Alasan Sebelumnya DATA_TIDAK_CUKUP

Sebelumnya pipeline sering berakhir `DATA_TIDAK_CUKUP` karena:

- local YOLO dapat menghasilkan 0 bbox,
- external free vision optional dapat kosong atau gagal,
- bbox pohon, konduktor, dan struktur penyangga belum ternormalisasi konsisten,
- geometry lama membutuhkan tiga class lengkap dan belum menerima fallback visual,
- tidak ada zone overlay saat konduktor tidak tervalidasi.

## YOLO-Compatible Bounding Box

File `plan_c_free_vision_schema.py` sekarang menormalisasi output ke class order:

0. `struktur_penyangga`
1. `konduktor`
2. `pohon_sono`
3. `pohon_non_sono`

Schema menerima bbox `xyxy`, `normalized_1000`, dan `box_2d` `[ymin, xmin, ymax, xmax]` lalu mengubahnya ke pixel `bbox_xyxy`. Output operator tidak menampilkan nama engine eksternal.

## False-Positive Filter

`plan_c_quality_layer.py` menolak kandidat yang mengarah ke objek non-target seperti person, face, head, chin, body, wall, cabinet, roof, floor, door, window, kendaraan, furniture, shadow, dan background. Jika tidak ada tree target, kandidat conductor/support juga ditolak agar selfie/indoor tidak menjadi bbox palsu.

## Species Status

- `pohon_sono` hanya dipakai jika label mengarah ke sono/angsana/Pterocarpus indicus.
- `pohon_non_sono` dipakai untuk tree/vegetation generic atau species tidak yakin.
- Jika `pohon_non_sono`, growth output diberi `generic_vegetation_proxy` dan tidak mengklaim profile pohon_sono sebagai identifikasi final.

## Zona Tebang/Pantau/Aman

`plan_c_zone_overlay.py` dan renderer menggambar:

- `ZONA TEBANG 0-3 m di bawah konduktor` dengan overlay merah,
- `ZONA PANTAU` dengan overlay kuning,
- `ZONA AMAN` dengan overlay hijau.

Jika konduktor tidak tervalidasi, sistem tidak menggambar zona presisi dan menampilkan status `DATA TIDAK CUKUP - KONDUKTOR TIDAK TERVALIDASI`.

## Prediction

`plan_c_geometry.py` sekarang dapat menghitung clearance jika minimal tree + conductor tersedia. Scale berasal dari:

1. struktur penyangga,
2. input manual,
3. fallback visual dengan status `APPROXIMATE_VISUAL_ESTIMATE`.

Risk status:

- `ZONA_TEBANG`
- `PANTAU`
- `AMAN`
- `DATA_TIDAK_CUKUP`

Prediction window tetap kuartalan: `0-3 bulan`, `3-6 bulan`, `6-9 bulan`, `9-12 bulan`, `>12 bulan`, atau `data tidak cukup`.

## Feedback Learning

Endpoint `POST /api/plan-c/operator-feedback`:

- ACCEPT menulis `data/runtime/plan_c/feedback/accepted_records.jsonl` dan label YOLO-compatible ke `data/runtime/plan_c/feedback/yolo_compatible_labels/<session_id>.txt`.
- REJECT menulis `data/runtime/plan_c/feedback/rejected_records.jsonl` dan menandai result sebagai rejected tanpa menghapus file fisik.
- Map page memfilter rejected session saat membaca marker aktif.

Feedback runtime tidak masuk dataset training resmi dan tidak menyentuh `data/raw`, `dataset_yolo`, `runs`, `weights`, atau `models`.

## Validasi

Smoke baru:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_detection_zone_smoke.py
```

Smoke ini memakai mock detection internal deterministic tanpa API eksternal untuk menguji:

- tree + conductor + structure menghasilkan geometry dan prediction,
- human-only tidak menjadi bbox target,
- `pohon_non_sono` memakai generic vegetation proxy,
- missing conductor tidak mengklaim zona presisi,
- feedback ACCEPT/REJECT append-only dan map filtering.

## Batasan

Hasil detection, zone overlay, clearance, dan prediction tetap perlu review lapangan. Sistem tidak menggantikan pengukuran manual PLN dan tidak mengklaim akurasi final biologis atau akurasi final operasional.
