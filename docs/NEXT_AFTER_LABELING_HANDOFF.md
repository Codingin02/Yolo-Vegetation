# Next After Labeling Handoff

Setelah export YOLO makesense.ai selesai:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\phase3_readiness_gate.py
.\venv\Scripts\python.exe scripts\phase4_integration_gate.py
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy
.\venv\Scripts\python.exe scripts\validate_yolo_labels.py --point V001_pohon_sono
```

Setelah validator `VALID`:

```powershell
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode build --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\generate_data_yaml.py --mode write
.\venv\Scripts\python.exe scripts\train_yolov8_field_multiclass.py --dry-run
```

Training aktual tetap butuh izin operator eksplisit.
