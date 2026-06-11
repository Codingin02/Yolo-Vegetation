# PLAN C — Plan Selanjutnya yang Belum Tercapai

## Status besar yang sudah tercapai

- Route utama `/plan-c` sudah ada.
- Capture snapshot sudah berjalan.
- Result page sudah tampil.
- Bottom navigation sudah ada.
- Zona tebang, zona pantau, dan zona aman sudah mulai terintegrasi.
- GPS dan map sudah masuk alur.
- Growth proxy sudah tersedia.
- Feedback operator benar/salah sudah mulai masuk sebagai learning reference.
- Ada pipeline akuisisi dataset 8.5A/8.5B, tetapi hasil gambar masih sangat kecil dan belum ada label.

## Yang belum tercapai dan masih wajib diselesaikan

### 1. Dataset final pohon_sono belum cukup

Kondisi terakhir:

```text
TOTAL_IMAGE_FILES     : 3
TOTAL_LABEL_TXT_FILES : 0
TOTAL_MANIFEST_FILES  : 10
STATUS                : GAMBAR_ADA_TAPI_BOUNDING_LABEL_BELUM_ADA
```

Target:

```text
pohon_sono minimal 80 gambar
pohon_non_sono minimal 60 gambar
negative sample minimal 100 gambar
```

### 2. Bounding / label YOLO belum ada

Belum ada `.txt` label YOLO-compatible. Ini berarti belum ada bounding box dataset training.

### 3. Konduktor belum punya dataset cukup

Konduktor penting karena zona tebang dihitung dari posisi konduktor. Tanpa deteksi konduktor yang stabil, zona bisa salah.

Target:

```text
konduktor minimal 60 gambar reviewed
```

### 4. Struktur penyangga belum punya dataset cukup

Target:

```text
struktur_penyangga minimal 40 gambar reviewed
```

### 5. Negative sample belum cukup

Target negative:

```text
human face
head
chin
person body
car
motorcycle
truck
wall
indoor object
cabinet
lamp
roof
ceiling
non-sono tree
```

### 6. Roboflow package belum final

Package Roboflow harus dibuat dari dataset folder final:

```text
data/dataset_yolo/plan_c_final_v1/roboflow_package
```

### 7. Training YOLO belum boleh dipaksa

Training belum boleh dijalankan kalau dataset belum cukup. Status benar jika belum cukup:

```text
YOLO_TRAINING_SKIPPED_DATASET_NOT_READY
```

### 8. Model registry final belum selesai

Setelah training, harus ada model registry, tetapi file `.pt` tidak boleh di-commit.

### 9. Runtime Plan C harus membaca model final secara aman

Runtime tidak boleh memilih model lama yang unstable. Model selector harus menolak model tanpa registry, menolak model dengan validation rendah, dan tidak membuat fake detection.

### 10. Uji lapangan HP + ngrok final belum selesai

Setelah dataset dan model siap, lakukan uji HP kamera, GPS kantor, ngrok HTTPS, snapshot outdoor, result zone, map marker, dan feedback benar/salah.

### 11. Laporan akhir magang belum difinalisasi

Laporan akhir nanti harus mengikuti proposal dan perkembangan Plan C. Istilah aman: YOLOv8, bounding box YOLO-compatible, snapshot-based monitoring, Python geometry, growth-risk prediction, field trial system.

## Urutan kerja paling bijak

1. Selesaikan dataset pohon_sono dulu.
2. Setelah itu konduktor.
3. Setelah itu struktur_penyangga.
4. Setelah itu negative sample.
5. Build Roboflow package.
6. Review manual/pseudo-label.
7. Training YOLO.
8. Integrasi model ke Plan C.
9. Field test HP outdoor.
10. Finalisasi laporan.

Keputusan teknis: jangan menambah fitur UI lagi sebelum dataset selesai. UI sudah cukup untuk demo. Masalah utama sekarang adalah kualitas deteksi, dan itu hanya selesai dengan dataset + label + training gate yang benar.
