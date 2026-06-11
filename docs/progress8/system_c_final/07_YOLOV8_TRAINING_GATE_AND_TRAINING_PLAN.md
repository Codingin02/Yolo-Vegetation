# SYSTEM C FINAL — YOLOv8 Training Gate dan Training Plan

## Training tidak boleh dipaksa

Training hanya boleh dilakukan jika dataset sudah cukup. Jika belum cukup, script harus berhenti dengan status:

```text
YOLO_TRAINING_SKIPPED_DATASET_NOT_READY
```

## Dataset gate

Script wajib:

```text
scripts/plan_c_86_dataset_quality_gate.py
```

Pemeriksaan:

```text
- images/train, images/val, images/test ada
- labels/train, labels/val, labels/test ada
- data.yaml valid
- class order benar
- label YOLO valid
- bbox normalized
- tidak ada class id di luar 0..3
- tidak ada file gambar rusak
- tidak ada duplicate sha256
- source manifest lengkap
- license manifest lengkap
- review manifest lengkap
```

## Threshold minimum

```text
pohon_sono          >= 80
konduktor           >= 60
struktur_penyangga  >= 40
pohon_non_sono      >= 60
negative sample     >= 100
```

## Training command

Training hanya setelah gate memberi:

```text
PLAN_C_8_6_YOLO_TRAINING_READY
```

Command training boleh disiapkan, tetapi jangan dijalankan jika gate gagal:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_87_train_yolov8_plan_c_final.py
```

## Output model

Model training output tidak boleh di-commit.

Output lokal:

```text
runs/detect/plan_c_final_v1/
```

Model candidate:

```text
runs/detect/plan_c_final_v1/weights/best.pt
```

## Evaluasi minimal

Sebelum runtime memilih model:

```text
precision
recall
mAP50
mAP50-95
confusion matrix
sample annotated images
false positive review
```

Jika evaluasi belum cukup, status:

```text
MODEL_CANDIDATE_NOT_READY_FOR_RUNTIME
```

## Model registry

Setelah evaluasi cukup, tulis registry:

```text
models/registry/plan_c_model_registry.json
```

Isi registry tidak menyimpan model file ke Git. Registry hanya menunjuk path lokal dan metadata.

Status model:

```text
MODEL_READY_FOR_FIELD_TRIAL
```

Jika model tidak siap:

```text
YOLO_MODEL_NOT_READY
```
