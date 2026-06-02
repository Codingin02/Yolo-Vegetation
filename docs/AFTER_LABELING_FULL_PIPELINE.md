# After Labeling Full Pipeline

Setelah export YOLO dari makesense.ai selesai, letakkan export di:

```text
E:\Projects\ULP_Project\data\exports\make_sense\V001_pohon_sono
```

Lalu jalankan dari root project:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\phase3_readiness_gate.py
.\venv\Scripts\python.exe scripts\phase4_integration_gate.py
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy
.\venv\Scripts\python.exe scripts\validate_yolo_labels.py --point V001_pohon_sono
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode build --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\generate_data_yaml.py --mode write
.\venv\Scripts\python.exe scripts\train_yolov8_field_multiclass.py --dry-run
```

Training actual hanya boleh dijalankan setelah dry-run valid dan user memberi izin eksplisit.
