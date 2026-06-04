# Phase 6.1 Label Quality Rules

Label YOLO valid harus berformat:

```text
class_id x_center y_center width height
```

Aturan:

- `class_id` hanya `0`, `1`, atau `2`.
- Semua koordinat normalized antara `0` dan `1`.
- `width` dan `height` harus lebih dari `0`.
- Nama image dan label harus cocok berdasarkan stem.
- File label kosong perlu alasan review atau status negative eksplisit.
- Gambar blur/backlight/terhalang masuk review.
- Duplicate image dilaporkan.
- Corrupt image dilaporkan.
- Class imbalance dilaporkan jujur, terutama saat fokus awal V001 pohon sono.

Status class imbalance awal yang wajar:

`CLASS_IMBALANCE_EXPECTED_INITIAL_TREE_FOCUS`

Jangan klaim model final akurat sebelum evaluasi dataset memadai.
