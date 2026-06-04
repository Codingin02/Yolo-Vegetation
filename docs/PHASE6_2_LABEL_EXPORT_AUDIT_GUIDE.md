# Phase 6.2 Label Export Audit Guide

Letakkan export MakeSense YOLO di:

`data/dataset_yolo/01_makesense_export/`

Format yang diterima:

- file label `.txt` per gambar
- folder `images/` dan `labels/`
- `classes.txt` atau `labels.txt`
- `.zip` export MakeSense, yang akan diekstrak ke folder ignored `data/dataset_yolo/01_makesense_export/extracted/`

Validator memeriksa:

- class id hanya `0`, `1`, `2`
- koordinat YOLO normalized `0..1`
- width/height positif
- bbox tidak keluar gambar
- pasangan image-label cocok
- duplicate/corrupt image
- class order tetap `struktur_penyangga`, `konduktor`, `pohon_sono`
- bbox terlalu kecil, terlalu besar, atau menyentuh tepi masuk review warning

Output audit lokal berada di `data/dataset_yolo/02_label_audit/` dan tidak boleh di-commit.
