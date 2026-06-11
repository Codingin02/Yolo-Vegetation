# SYSTEM C FINAL — Runtime Plan C Acceptance

## Acceptance target

Runtime Plan C dianggap final field-trial jika:

```text
PLAN_C_SYSTEM_FINAL_FIELD_TRIAL_READY
```

## Checklist halaman

```text
GET /plan-c                         200
GET /plan-c/capture/<session_id>    200
GET /plan-c/processing/<session_id> 200
GET /plan-c/result/<session_id>     200
GET /plan-c/map                     200
GET /plan-c/developer/<session_id>  200
```

## Checklist API

```text
POST /api/plan-c/session/start             201
POST /api/plan-c/session/tree-anchor       200
POST /api/plan-c/session/snapshot          202
GET  /api/plan-c/session/<id>/status       200
GET  /api/plan-c/session/<id>/result       200
POST /api/plan-c/operator-feedback         200
```

## Checklist hasil

Setiap session harus memiliki:

```text
original.jpg
annotated.jpg
result.json
developer.json
metadata.json
yolo_raw.json
geometry.json
```

Jika AI validator aktif:

```text
ai_raw.json
```

Jika AI validator nonaktif:

```text
AI_VALIDATOR_DISABLED
```

## Checklist storage

```text
data/runtime/plan_c/sessions/<session_id>/
data/runtime/plan_c/spreadsheet/plan_c_records.csv
data/runtime/plan_c/spreadsheet/plan_c_records.jsonl
data/runtime/plan_c/map/plan_c_markers.json
```

Storage append-only. Jangan reset CSV/map marker saat server restart.

## Checklist result page

Result page harus memuat:

```text
risk_status
prediction_window
clearance_estimate_m
tree_height_estimate_m
detection_count
gps_status
growth_profile_status
map link
developer link
operator feedback buttons
```

## Checklist zona

```text
ZONA_TEBANG 0–3 m di bawah konduktor
ZONA_PANTAU 3–6 m di bawah konduktor
ZONA_AMAN dari batas 6 m ke ground_reference_y
```

Jika konduktor tidak tervalidasi:

```text
DATA_TIDAK_CUKUP
```

## Checklist safety

```text
no_fake_detection = true
no_fake_gps = true
no_fake_clearance = true
no_fake_model_ready = true
manual_review_required jika data kurang
```

## Smoke scripts wajib

```text
scripts/plan_c_smoke.py
scripts/plan_c_detection_zone_smoke.py
scripts/plan_c_final_zone_geometry_smoke.py
scripts/plan_c_86_dataset_quality_gate.py
scripts/plan_c_89_final_field_trial_acceptance.py
```

## Forbidden commit

Jangan commit:

```text
data/runtime
data/dataset_yolo/plan_c_final_v1/images
data/dataset_yolo/plan_c_final_v1/labels
roboflow_package
runs
weights
models/*.pt
.env
token
credential
ngrok URL
```
