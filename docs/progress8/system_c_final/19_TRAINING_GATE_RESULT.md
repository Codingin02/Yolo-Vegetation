# Training Gate Result

## Target Minimal

- `pohon_sono`: 80 gambar accepted/reviewed dan 80 label valid
- `konduktor`: 60 gambar accepted/reviewed dan 60 label valid
- `struktur_penyangga`: 40 gambar accepted/reviewed dan 40 label valid
- `pohon_non_sono`: 40 gambar
- non-target negative: 60 gambar

## Pemeriksaan

Gate memeriksa:

- jumlah gambar per class
- jumlah label valid per class
- `classes.txt`
- `data.yaml`
- duplicate image hash
- class id hanya `0..3`
- koordinat label normalized

## Status

Jika target belum terpenuhi, status wajib:

```text
YOLO_TRAINING_SKIPPED_DATASET_NOT_READY
```

Training tidak boleh dipaksa ketika status ini muncul.
