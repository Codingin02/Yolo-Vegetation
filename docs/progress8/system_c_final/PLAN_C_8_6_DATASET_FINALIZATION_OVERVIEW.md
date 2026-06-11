# PLAN C 8.6 — Dataset Finalization Overview

## Tujuan tahap ini

Tahap 8.6 berfokus menyelesaikan jalur dataset YOLOv8 untuk sistem monitoring vegetasi jaringan distribusi 20 kV. Fokusnya bukan UI, bukan route web, dan bukan runtime Plan C. Fokusnya adalah membuat dataset final yang bisa dipakai untuk melatih model YOLOv8 secara lebih stabil.

Prioritas objek:

1. `pohon_sono`
2. `konduktor`
3. `struktur_penyangga`
4. negative sample: manusia, wajah, kendaraan, tembok, indoor object, atap, lampu, benda kecil, dan pohon non-sono.

## Keputusan dataset

Dataset final target:

```text
E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1\
```

Struktur wajib:

```text
data/dataset_yolo/plan_c_final_v1/
  data.yaml
  classes.txt
  source_manifest.csv
  license_manifest.csv
  review_manifest.csv
  acquisition_report.md
  images/train
  images/val
  images/test
  labels/train
  labels/val
  labels/test
  rejected/license_unclear
  rejected/low_quality
  rejected/not_species_specific
  rejected/non_target
  review/needs_manual_check
  review/accepted_pseudo_label
  review/rejected_pseudo_label
  roboflow_package
```

Catatan penting:

- Folder `data/dataset_yolo/plan_c_final_v1` adalah folder dataset YOLO final target, bukan folder runtime acak.
- Gambar boleh masuk ke folder final hanya jika metadata minimal lengkap: source URL, license, author, class target, checksum.
- Label YOLO-compatible boleh dibuat otomatis sebagai pseudo-label, tetapi statusnya tetap `needs_manual_check` sampai dikonfirmasi.
- Dataset yang belum direview tidak boleh dipakai untuk klaim akurasi final.
- Training YOLO boleh dilakukan hanya setelah gate dataset menyatakan jumlah dan distribusi minimal sudah cukup.

## Class final

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono
```

Kebijakan class:

- `pohon_sono` hanya untuk Pterocarpus indicus / angsana / sonokembang / narra yang metadata spesiesnya kuat atau foto lapangan sudah dikonfirmasi.
- `pohon_non_sono` untuk pohon lain atau vegetasi umum.
- `konduktor` untuk kabel listrik / power line / overhead conductor.
- `struktur_penyangga` untuk tiang, pole, crossarm, struktur penyangga kabel.
- Manusia, wajah, kendaraan, tembok, ruangan, lampu, atap, langit, tanah, dan objek rumah tangga tidak boleh diberi bbox target.

## Tahapan kerja 8.6

1. Source registry 15+ sumber legal.
2. Download legal dan manifest.
3. Pseudo-label YOLO-compatible dengan status `needs_manual_check`.
4. Dataset quality gate.
5. Roboflow package untuk review.
6. YOLO training gate, bukan training paksa.

## Output wajib Codex

```text
docs/progress8/PLAN_C_8_6_DATASET_FINALIZATION_REPORT.md
docs/progress8/PLAN_C_8_6_SOURCE_REGISTRY_REPORT.md
docs/progress8/PLAN_C_8_6_ROBOFLOW_PACKAGE_REPORT.md
scripts/plan_c_86_acquire_pohon_sono_priority.py
scripts/plan_c_86_acquire_conductor_priority.py
scripts/plan_c_86_acquire_structure_priority.py
scripts/plan_c_86_build_yolo_dataset.py
scripts/plan_c_86_autolabel_yolo_compatible.py
scripts/plan_c_86_dataset_quality_gate.py
scripts/plan_c_86_build_roboflow_package.py
```

## Status sukses minimal

```text
PLAN_C_8_6_DATASET_SOURCE_REGISTRY_READY
PLAN_C_8_6_POHON_SONO_CANDIDATES_COLLECTED
PLAN_C_8_6_YOLO_COMPATIBLE_PSEUDO_LABELS_READY
PLAN_C_8_6_ROBOFLOW_PACKAGE_READY
PLAN_C_8_6_DATASET_GATE_READY
```
