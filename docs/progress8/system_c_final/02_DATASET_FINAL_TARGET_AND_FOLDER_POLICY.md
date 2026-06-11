# SYSTEM C FINAL — Dataset Final Target dan Folder Policy

## Folder download sumber

Semua hasil download kandidat gambar dari internet diarahkan dulu ke:

```text
D:\Users\All Users\Downloads\ULP_Project_PlanC_Dataset_Downloads
```

Folder ini bukan dataset final. Folder ini adalah tempat unduhan awal, cache legal, manifest sumber, dan kandidat yang masih harus disaring.

## Folder dataset final

Dataset YOLO final berada di:

```text
E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1
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
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
  rejected/
    license_unclear/
    low_quality/
    not_species_specific/
    non_target/
  review/
    needs_manual_check/
    accepted_pseudo_label/
    rejected_pseudo_label/
    accepted_manual_label/
  roboflow_package/
```

## Isi classes.txt

```text
struktur_penyangga
konduktor
pohon_sono
pohon_non_sono
```

## Isi data.yaml

```yaml
path: E:/Projects/ULP_Project/data/dataset_yolo/plan_c_final_v1
train: images/train
val: images/val
test: images/test

names:
  0: struktur_penyangga
  1: konduktor
  2: pohon_sono
  3: pohon_non_sono
```

## Manifest wajib

Setiap gambar harus memiliki catatan di:

```text
source_manifest.csv
license_manifest.csv
review_manifest.csv
```

Kolom minimal:

```text
local_path
label_path
source_site
source_url
direct_image_url
scientific_name
common_name
target_class
license
license_url
author
attribution
country_or_location
width
height
sha256
downloaded_at
accept_status
review_status
risk_note
```

## Status gambar

```text
ACCEPT_POSITIVE_REFERENCE
ACCEPT_NEGATIVE_REFERENCE
ACCEPT_CONDUCTOR_REFERENCE
ACCEPT_STRUCTURE_REFERENCE
RESTRICTED_REFERENCE_ONLY
REJECT_LICENSE_UNCLEAR
REJECT_NOT_SPECIES_SPECIFIC
REJECT_LOW_QUALITY
REJECT_NOT_TARGET_OBJECT
REJECT_DUPLICATE
```

## Status review label

```text
needs_manual_check
accepted_pseudo_label
rejected_pseudo_label
accepted_manual_label
```

## Target minimal dataset

Target awal:

```text
pohon_sono          : 80 gambar accepted/review candidate
konduktor           : 60 gambar accepted/review candidate
struktur_penyangga  : 40 gambar accepted/review candidate
pohon_non_sono      : 60 gambar
non_target_negative : 100 gambar
```

Jika target tidak tercapai, sistem tetap harus jujur dan mengeluarkan:

```text
PLAN_C_8_6_DATASET_NOT_READY
YOLO_TRAINING_SKIPPED_DATASET_NOT_READY
```

## Larangan

Jangan commit:

```text
images/
labels/
roboflow_package/
*.zip
*.jpg
*.jpeg
*.png
*.webp
*.pt
*.onnx
runs/
weights/
models/
.env
token
credential
ngrok
```
