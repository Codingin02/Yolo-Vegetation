# SYSTEM C FINAL — Roboflow Review Package Workflow

## Tujuan

Roboflow dipakai untuk review manual, koreksi bounding box, dan export YOLOv8. Roboflow bukan tempat menyimpan secret dan bukan tempat mengklaim dataset otomatis final.

## Folder package

```text
E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1\roboflow_package
```

Struktur:

```text
roboflow_package/
  data.yaml
  README_ROBOFLOW_REVIEW.md
  source_manifest.csv
  license_manifest.csv
  review_manifest.csv
  images/
  labels/
```

## Isi README_ROBOFLOW_REVIEW.md

Harus menjelaskan:

```text
- class order
- license policy
- status auto-label sebagai needs_manual_check
- cara review pohon_sono
- cara review konduktor
- cara review struktur_penyangga
- cara menolak negative sample
- cara export YOLOv8
```

## Review di Roboflow

Langkah review:

1. Upload package.
2. Pastikan class order tidak berubah.
3. Review `pohon_sono` dulu.
4. Review `konduktor`.
5. Review `struktur_penyangga`.
6. Tandai gambar negative.
7. Export YOLOv8.
8. Simpan hasil export kembali ke dataset final hanya setelah license dan review manifest sinkron.

## Class order tidak boleh berubah

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono
```

Jika Roboflow mengurutkan ulang class, Codex harus membuat converter yang mengembalikan urutan class ini.

## Output setelah export

```text
data/dataset_yolo/plan_c_final_v1/exported_yolov8_reviewed/
  data.yaml
  images/
  labels/
```

Folder exported tetap tidak di-commit ke Git jika berisi gambar/label.

## Gate setelah Roboflow

Setelah export:

```text
scripts/plan_c_86_dataset_quality_gate.py
```

Gate harus memeriksa:

```text
- label format YOLO valid
- class id valid 0..3
- bbox normalized 0..1
- source manifest ada
- license manifest ada
- duplicate sha256 tidak ada
- jumlah per class cukup
- split train/val/test ada
```
