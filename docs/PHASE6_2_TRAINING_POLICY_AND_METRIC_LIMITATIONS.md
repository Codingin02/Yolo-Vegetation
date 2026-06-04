# Phase 6.2 Training Policy And Metric Limitations

Training hanya boleh dijalankan jika:

- export MakeSense tersedia
- label valid
- dataset build valid
- `data.yaml` valid
- Progress 5.4 tetap PASS

Jika CPU only atau dataset kecil, gunakan training smoke. Smoke training membuktikan pipeline, bukan akurasi final.

Command awal GPU:

```powershell
.\venv\Scripts\yolo.exe detect train model=yolov8n.pt data=data/dataset_yolo/field_multiclass_v1/data.yaml epochs=50 imgsz=640 batch=-1 device=0 project=runs/field_multiclass name=yolov8n_v1 seed=23050874166 patience=15
```

Command smoke CPU:

```powershell
.\venv\Scripts\yolo.exe detect train model=yolov8n.pt data=data/dataset_yolo/field_multiclass_v1/data.yaml epochs=3 imgsz=640 batch=auto device=cpu project=runs/field_multiclass name=yolov8n_v1_cpu_smoke seed=23050874166 patience=15
```

Metrik seperti precision, recall, mAP50, dan loss boleh dilaporkan sebagai smoke/initial metric. Jangan tulis akurasi final sebelum dataset validasi memadai.
