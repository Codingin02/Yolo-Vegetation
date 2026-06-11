# Plan C YOLO Dataset Training Gate

Gate ini memisahkan runtime `/plan-c` dari proses dataset dan training YOLO.

## Tujuan

- Mengecek apakah data lokal cukup untuk training YOLO vegetation.
- Menjaga class order:
  - `0 struktur_penyangga`
  - `1 konduktor`
  - `2 pohon_sono`
  - `3 pohon_non_sono`
- Mengubah feedback operator accepted menjadi manifest review-only.
- Menolak training jika data belum cukup.

## Perintah

```powershell
.\venv\Scripts\python.exe scripts\plan_c_yolo_dataset_gate.py
```

Output status:

- `YOLO_TRAINING_DATA_NOT_ENOUGH`
- `YOLO_TRAINING_DATA_READY`
- `YOLO_TRAINING_SKIPPED_SAFE`

## Aturan Aman

- Gate tidak menjalankan training panjang.
- Gate tidak mengunduh dataset internet.
- Gate tidak scraping Google Images.
- Gate tidak membuat model `.pt`, `.onnx`, atau `.engine`.
- Gate tidak menyalin raw image baru ke Git.
- Feedback accepted tetap masuk review queue, bukan dataset resmi.

## Lokasi Output Runtime

```text
data/training_gate/plan_c_yolo_vegetation/review_queue
data/training_gate/plan_c_yolo_vegetation/gate_report.json
```

File output runtime ini tidak perlu di-stage untuk commit source.

## Syarat Dataset Ready

`dataset.yaml` hanya dibuat jika:

- `images/train` ada,
- `images/val` ada,
- `labels/train` ada,
- `labels/val` ada,
- class mapping valid,
- jumlah label minimal per class terpenuhi.

Jika syarat tidak terpenuhi, status tetap `YOLO_TRAINING_DATA_NOT_ENOUGH`.
