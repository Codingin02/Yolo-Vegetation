# Phase 6.2 Dataset Build And data.yaml Guide

Dataset final lokal ditulis ke:

`data/dataset_yolo/field_multiclass_v1/`

Struktur:

- `images/train`
- `images/val`
- `images/test` jika cukup data
- `labels/train`
- `labels/val`
- `labels/test` jika cukup data
- `data.yaml`
- `dataset_manifest.csv`
- `dataset_build_report.json`

Split default `70/20/10` dengan seed `23050874166`. Untuk dataset kecil, test split boleh dilewati dan statusnya `TEST_SPLIT_SKIPPED_SMALL_DATASET`.

`data.yaml` wajib memakai class order:

```yaml
path: data/dataset_yolo/field_multiclass_v1
train: images/train
val: images/val
names:
  0: struktur_penyangga
  1: konduktor
  2: pohon_sono
```

Dataset lokal tidak boleh di-stage.
