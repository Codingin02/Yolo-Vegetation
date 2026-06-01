# After makesense.ai Export Steps

Dokumen ini dipakai setelah user selesai labeling V001 di makesense.ai.

## 1. Export Dari makesense.ai

Gunakan format YOLO. Pastikan class order tetap:

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
```

Letakkan file `.txt` hasil export di:

```text
data/exports/make_sense/V001_pohon_sono
```

Jangan memindahkan atau mengubah `images_selected`.

## 2. Import Dry-Run

```powershell
python scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
```

Periksa:

- `images_found`
- `labels_found_in_export`
- `matched_labels`
- `missing_labels`
- `orphan_labels`
- `invalid_export_labels`

## 3. Import Copy

```powershell
python scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy
```

Gunakan `--overwrite` hanya jika benar-benar ingin mengganti label yang sudah ada.

## 4. Validasi

```powershell
python scripts\validate_yolo_labels.py --point V001_pohon_sono
```

Status harus `VALID` sebelum dataset final dibuat.

## 5. Build Dataset

```powershell
python scripts\build_field_multiclass_dataset.py --mode dry-run
python scripts\build_field_multiclass_dataset.py --mode build
```

Dataset final:

```text
data/dataset_yolo/field_multiclass_v1
```

## 6. Training

```powershell
python scripts\train_yolov8_field_multiclass.py --dry-run
python scripts\train_yolov8_field_multiclass.py --run --model yolov8n.pt --epochs 50 --imgsz 640
```

Jangan klaim akurasi sebelum training dan evaluasi benar-benar selesai.
