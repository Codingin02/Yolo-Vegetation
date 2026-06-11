# SYSTEM C FINAL — Model Registry dan Integrasi Runtime Plan C

## Tujuan

Runtime Plan C tidak boleh memilih model sembarangan. Model harus dipilih dari registry yang valid.

## Registry path

```text
E:\Projects\ULP_Project\models\registry\plan_c_model_registry.json
```

## Isi registry

```json
{
  "active_model_id": "plan_c_final_v1",
  "models": [
    {
      "model_id": "plan_c_final_v1",
      "task": "detect",
      "weights_path": "E:/Projects/ULP_Project/runs/detect/plan_c_final_v1/weights/best.pt",
      "data_yaml": "E:/Projects/ULP_Project/data/dataset_yolo/plan_c_final_v1/data.yaml",
      "classes": {
        "0": "struktur_penyangga",
        "1": "konduktor",
        "2": "pohon_sono",
        "3": "pohon_non_sono"
      },
      "status": "MODEL_READY_FOR_FIELD_TRIAL",
      "created_at": "",
      "metrics": {
        "precision": null,
        "recall": null,
        "map50": null,
        "map50_95": null
      },
      "limitations": [
        "Model field trial, bukan model produksi PLN.",
        "Akurasi harus divalidasi dengan data lapangan ULP Perak."
      ]
    }
  ]
}
```

## Selector policy

Runtime selector harus:

1. Membaca registry.
2. Memastikan file `best.pt` ada.
3. Memastikan class order cocok.
4. Memastikan status `MODEL_READY_FOR_FIELD_TRIAL`.
5. Menolak model jika metrics kosong dan policy mengharuskan metrics.
6. Menolak model lama yang tidak stabil.
7. Jika model tidak siap, return `YOLO_MODEL_NOT_READY`.

## Runtime output jika model siap

```text
YOLO_DETECTION_READY
detections: [...]
annotated.jpg tersedia
result.json tersedia
developer.json tersedia
```

## Runtime output jika model tidak siap

```text
YOLO_MODEL_NOT_READY
detections: []
risk_status: DATA_TIDAK_CUKUP
manual_review_required: true
```

## Larangan

Jangan memilih:

```text
field_multiclass_v1
model yang conf 0.001 false positive explosion
model tanpa registry
model tanpa class map
model tanpa evaluasi
model file yang hilang
```

## Integrasi Plan C

Integrasi dilakukan di:

```text
src/ulp_project/plan_c_processor.py
src/ulp_project/plan_c_yolo.py
src/ulp_project/plan_c_model_registry.py
```

YOLO inference hanya setelah snapshot diterima. Jangan hidupkan realtime YOLO di HP camera.
