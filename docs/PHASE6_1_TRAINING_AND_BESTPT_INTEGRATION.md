# Phase 6.1 Training And Bestpt Integration

Training tidak dijalankan jika label belum ada atau dataset belum valid.

CUDA check:

```powershell
.\venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Dry-run training plan:

```powershell
.\venv\Scripts\python.exe scripts\progress6_1_train_yolov8_initial.py
```

Training awal setelah dataset valid:

```powershell
.\venv\Scripts\yolo.exe detect train model=yolov8n.pt data=data/dataset_yolo/field_multiclass_v1/data.yaml epochs=50 imgsz=640 batch=-1 device=0 project=runs/field_multiclass name=yolov8n_v1 seed=23050874166 patience=15
```

Jika CPU only atau data sangat kecil, gunakan smoke 3 epoch dan tulis status sebagai pipeline smoke, bukan akurasi final.

Best.pt hasil training tidak boleh di-commit. Runtime dapat membaca kandidat:

```text
runs/field_multiclass/yolov8n_v1/weights/best.pt
models/field/best.pt
```

Validasi:

```powershell
.\venv\Scripts\python.exe scripts\progress6_1_check_trained_model.py --model runs/field_multiclass/yolov8n_v1/weights/best.pt
.\venv\Scripts\python.exe scripts\progress5_4_remote_https_camera_yolo_gate.py
```
