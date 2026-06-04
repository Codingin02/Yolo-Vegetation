# Phase 6.1 YOLO Dataset Build Guide

Dataset final memakai class order terkunci:

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
```

Dry-run build:

```powershell
.\venv\Scripts\python.exe scripts\progress6_1_build_yolo_dataset.py --mode dry-run
```

Build hanya setelah label valid:

```powershell
.\venv\Scripts\python.exe scripts\progress6_1_build_yolo_dataset.py --mode build
```

Target lokal:

```text
data/dataset_yolo/field_multiclass_v1/
```

Folder dataset berisi gambar/label lokal dan tidak boleh di-commit.

Split default: train 70%, val 20%, test 10%, seed `23050874166`. Jika data kecil, test split boleh dilewati dengan status `TEST_SPLIT_SKIPPED_SMALL_DATASET`.
