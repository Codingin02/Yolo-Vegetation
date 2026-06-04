# Progress 6.2 MakeSense Export To Training

Status target Progress 6.2 adalah memindahkan hasil labeling manual MakeSense ke dataset YOLO, training smoke, dan handoff `best.pt` ke runtime 5.4 tanpa membuat label/model palsu.

## Urutan aman

1. Pastikan runtime 5.4 masih PASS.
2. Taruh export YOLO MakeSense di `data/dataset_yolo/01_makesense_export/`.
3. Jalankan validator:
   `.\venv\Scripts\python.exe scripts\progress6_1_label_export_validator.py --write-reports`
4. Jalankan gate:
   `.\venv\Scripts\python.exe scripts\progress6_2_makesense_export_to_training_gate.py --write-reports`
5. Build dataset hanya jika label valid.
6. Training hanya jika dataset valid dan Progress 5.4 tetap PASS.

Jika export belum ada, status yang benar adalah `PROGRESS_6_2_BLOCKED_MAKESENSE_EXPORT_NOT_FOUND`. Jangan training.

## Larangan

- Jangan membuat label palsu.
- Jangan membuat `.txt` kosong supaya validator lolos.
- Jangan commit gambar, export zip, dataset lokal, `runs/`, `models/`, `weights/`, atau `best.pt`.
- Jangan klaim akurasi final dari training smoke.
