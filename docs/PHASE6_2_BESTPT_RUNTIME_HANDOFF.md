# Phase 6.2 best.pt Runtime Handoff

Jika training menghasilkan:

`runs/field_multiclass/yolov8n_v1/weights/best.pt`

cek model:

```powershell
.\venv\Scripts\python.exe scripts\progress6_1_check_trained_model.py --model runs/field_multiclass/yolov8n_v1/weights/best.pt
```

Integrasi runtime:

```powershell
.\venv\Scripts\python.exe scripts\progress6_1_integrate_bestpt_runtime.py --model runs/field_multiclass/yolov8n_v1/weights/best.pt
.\venv\Scripts\python.exe scripts\progress5_4_remote_https_camera_yolo_gate.py
```

File `.pt` tidak boleh di-commit. Runtime boleh berubah dari `MODEL_NOT_READY` ke `REAL_MODEL` hanya jika model load, class order benar, dan predict smoke berjalan.

Jika `best.pt` belum ada, runtime tetap `MODEL_NOT_READY` safe mode. Itu bukan error.
