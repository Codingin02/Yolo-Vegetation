# Model Handoff Setelah Labeling dan Training Selesai

Setelah Kelompok 1 selesai labeling dan operator menjalankan training final secara eksplisit, letakkan model hasil training di salah satu path ignored:

```text
models/field/best.pt
models/best.pt
weights/best.pt
runs/detect/train/weights/best.pt
```

Atau pakai environment override:

```powershell
$env:ULP_YOLO_MODEL_PATH="E:\path\to\best.pt"
```

Cek handoff:

```powershell
.\venv\Scripts\python.exe scripts\check_model_handoff_ready.py --dry-load
```

Class order wajib:

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
```

Jika class order tidak bisa diverifikasi, sistem memberi warning `MODEL_PRESENT_CLASS_ORDER_UNVERIFIED`, bukan klaim valid.
