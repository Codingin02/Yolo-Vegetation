# Labeling Handoff makesense.ai

## Input Aktif

```text
data/dataset_yolo/00_review_candidates/V001_pohon_sono/images_selected
```

## Output Export Yang Ditunggu

```text
data/exports/make_sense/V001_pohon_sono
```

## Output Label Setelah Import

```text
data/dataset_yolo/00_review_candidates/V001_pohon_sono/labels_selected
```

Import ke `labels_selected` hanya dilakukan dengan command eksplisit:

```powershell
python scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy
```

Default script adalah `dry-run`.

## Catatan

- Jangan rename file gambar.
- Jangan ubah prefix `P001`, `K001`, atau `V001`.
- Jangan ubah class order.
- Jangan gunakan `dataset_botol` sebagai dataset utama.
