# System Finalization No Label Touch Runbook

Mode kerja ini memisahkan dua jalur:

- Kelompok A: labeling manual di makesense.ai oleh user.
- Kelompok B: sistem finalisasi oleh Codex tanpa menyentuh data labeling.

## Folder Yang Tidak Boleh Disentuh

- `data/dataset_yolo/00_review_candidates/`
- `data/dataset_yolo/00_review_candidates/V001_pohon_sono/images_selected`
- `data/dataset_yolo/00_review_candidates/V001_pohon_sono/labels_selected`
- `data/dataset_yolo/00_review_candidates/V001_pohon_sono/images_all`
- `data/dataset_yolo/00_review_candidates/V001_pohon_sono/images_rejected`
- `data/exports/`
- `data/raw/`
- `data/gps/`
- `data/processed/`
- `dataset_botol/`

`dataset_botol` hanya dataset uji/stabilizer lama dan bukan dataset utama.

## Class Order Wajib

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
```

## Alur Setelah Export YOLO Dari makesense.ai

1. Letakkan export YOLO di folder export yang aman, contoh:

```powershell
E:\Projects\ULP_Project\data\exports\make_sense\V001_pohon_sono
```

2. Jalankan import dry-run:

```powershell
python scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
```

3. Jika ringkasan sudah benar, jalankan copy eksplisit:

```powershell
python scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy
```

4. Validasi label:

```powershell
python scripts\validate_yolo_labels.py --point V001_pohon_sono
```

5. Build dataset dry-run:

```powershell
python scripts\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
```

6. Build dataset final hanya setelah validator PASS:

```powershell
python scripts\build_field_multiclass_dataset.py --mode build --val-ratio 0.2 --seed 23050874166
```

7. Generate `data.yaml` jika diperlukan:

```powershell
python scripts\generate_data_yaml.py --mode write
```

8. Training launcher tetap dry-run dulu:

```powershell
python scripts\train_yolov8_field_multiclass.py --dry-run
```

9. Training sebenarnya hanya setelah dataset valid:

```powershell
python scripts\train_yolov8_field_multiclass.py --run --model yolov8n.pt --epochs 50 --imgsz 640 --batch auto --device 0
```

## Flask

```powershell
python scripts\run_flask_dev.py
```

Jika model belum ada, endpoint mengembalikan `MODEL_NOT_AVAILABLE`.

## Map GPS

```powershell
python scripts\build_field_map.py
```

Jika data GPS belum bisa diparse, status menjadi `GPS_DATA_NOT_READY`, bukan koordinat palsu.

## Spreadsheet Lokal

```powershell
python scripts\export_project_metadata_csv.py
```

CSV lokal dibuat dari metadata nyata. Google API tidak dipaksa dan credential tidak disimpan di repo.

## Troubleshooting

- `LABELS_NOT_READY`: masih ada gambar tanpa label atau label belum diexport.
- `EXPORT_LABELS_INVALID`: ada baris label YOLO yang formatnya salah.
- `DATASET_NOT_READY`: dataset train/val belum lengkap atau `data.yaml` belum ada.
- `MODEL_NOT_AVAILABLE`: bobot model final belum tersedia.
- `GPS_DATA_NOT_READY`: data GPS belum ada atau belum bisa diparse.

Jangan training sebelum validator label PASS.
