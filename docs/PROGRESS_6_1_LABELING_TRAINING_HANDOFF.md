# Progress 6.1 Labeling Training Handoff

Progress 6.1 berpindah ke Kelompok 1: labeling, validasi export MakeSense, dataset YOLO, training awal, dan handoff `best.pt` ke runtime Progress 5.4.

Progress 5.4 tidak diulang. Runtime HTTPS, camera/GPS, shutter autosave, map, CSV, favicon, dan tunnel sync harus tetap PASS.

Status saat label MakeSense belum tersedia:

`PROGRESS_6_1_LABELING_HANDOFF_READY_WAITING_FOR_MAKESENSE_EXPORT`

## Class Order Final

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
```

Jangan mengganti urutan atau nama class. Alias boleh dipakai untuk penjelasan, bukan untuk label final.

## Validasi

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\progress5_4_remote_https_camera_yolo_gate.py
.\venv\Scripts\python.exe scripts\progress6_1_prepare_labeling_handoff.py
.\venv\Scripts\python.exe scripts\progress6_1_label_export_validator.py --write-reports
.\venv\Scripts\python.exe scripts\progress6_1_labeling_training_gate.py
```

Jika label belum ada, jangan training. Lanjutkan manual labeling di MakeSense lalu simpan export YOLO ke:

```text
data/dataset_yolo/01_makesense_export/
```
