# CODEX MASTER PROMPT — SYSTEM C FINAL SAMPAI AKHIR

Tempel prompt ini ke Codex saat limit aktif.

---

Anda bekerja di repo lokal:

```text
E:\Projects\ULP_Project
```

Mode:

```text
Work locally
Jangan New worktree
Jangan branch baru
Jangan checkout
Jangan reset
Jangan git add .
Jangan commit sebelum validasi PASS
```

## Baca dokumen acuan dulu

Baca semua file berikut:

```text
E:\Projects\ULP_Project\docs\progress8\system_c_final\00_README_SYSTEM_C_FINAL.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\01_SYSTEM_C_ARCHITECTURE_FINAL.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\02_DATASET_FINAL_TARGET_AND_FOLDER_POLICY.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\03_SOURCE_REGISTRY_25_PLUS.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\04_LEGAL_LICENSE_AND_DOWNLOAD_POLICY.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\05_AUTOLABEL_AND_BOUNDING_POLICY.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\06_ROBOFLOW_REVIEW_PACKAGE_WORKFLOW.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\07_YOLOV8_TRAINING_GATE_AND_TRAINING_PLAN.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\08_MODEL_REGISTRY_AND_RUNTIME_INTEGRATION.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\09_RUNTIME_PLAN_C_FINAL_ACCEPTANCE.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\10_FIELD_TEST_HP_NGROK_FINAL_RUNBOOK.md
E:\Projects\ULP_Project\docs\progress8\system_c_final\11_FINAL_REPORT_WORDING_AND_CLAIM_POLICY.md
```

## Tujuan final

Selesaikan Plan C final. Jangan lanjut eksperimen Plan A/B. Jangan menambal `/field-camera` lama. Fokus hanya Sistem C final:

```text
/plan-c
/api/plan-c
data/dataset_yolo/plan_c_final_v1
models/registry/plan_c_model_registry.json
```

## Folder download sumber gambar

Gunakan folder download awal:

```text
D:\Users\All Users\Downloads\ULP_Project_PlanC_Dataset_Downloads
```

## Folder dataset final

Gunakan folder dataset final:

```text
E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1
```

## Prioritas pengerjaan

1. Pohon sono / Pterocarpus indicus.
2. Konduktor.
3. Struktur penyangga.
4. Pohon non-sono.
5. Negative sample.
6. Roboflow package.
7. Dataset gate.
8. Training YOLOv8 jika gate siap.
9. Model registry.
10. Integrasi model ke Plan C runtime.
11. Field test smoke.

## Jangan hanya audit

Audit awal boleh singkat. Setelah itu harus membuat implementasi nyata:

```text
source registry
legal downloader
manifest writer
pseudo-labeler
YOLO dataset builder
Roboflow package builder
dataset quality gate
training gate
model registry selector
Plan C runtime model integration
final field acceptance smoke
```

## File yang harus dibuat minimal

```text
src/ulp_project/plan_c_86_source_registry.py
src/ulp_project/plan_c_86_license_policy.py
src/ulp_project/plan_c_86_polite_downloader.py
src/ulp_project/plan_c_86_manifest.py
src/ulp_project/plan_c_86_pseudo_labeler.py
src/ulp_project/plan_c_86_yolo_export.py
src/ulp_project/plan_c_86_quality_gate.py
src/ulp_project/plan_c_model_registry.py
scripts/plan_c_86_acquire_pohon_sono_priority.py
scripts/plan_c_86_acquire_conductor_priority.py
scripts/plan_c_86_acquire_structure_priority.py
scripts/plan_c_86_acquire_negative_priority.py
scripts/plan_c_86_build_dataset_final.py
scripts/plan_c_86_build_roboflow_package.py
scripts/plan_c_86_dataset_quality_gate.py
scripts/plan_c_87_train_yolov8_plan_c_final.py
scripts/plan_c_88_register_model_candidate.py
scripts/plan_c_89_final_field_trial_acceptance.py
docs/progress8/PLAN_C_8_6_DATASET_FINALIZATION_REPORT.md
docs/progress8/PLAN_C_8_7_TRAINING_AND_MODEL_REGISTRY_REPORT.md
docs/progress8/PLAN_C_8_9_FINAL_FIELD_ACCEPTANCE_REPORT.md
```

## Legal source policy

Gunakan minimal 15 sumber. Jangan hanya Wikimedia. Jangan mengambil dari Google Images langsung. Jangan membuat kandidat palsu. Jika sumber rate-limited, catat lalu pindah sumber.

## Auto-label policy

Auto-label boleh dibuat tetapi statusnya `needs_manual_check`. Jangan klaim label otomatis sebagai label manual final.

## Training policy

Jika dataset gate belum siap:

```text
YOLO_TRAINING_SKIPPED_DATASET_NOT_READY
```

Jika dataset gate siap:

```text
PLAN_C_8_6_YOLO_TRAINING_READY
```

Baru training.

## Runtime policy

Jika model registry belum valid:

```text
YOLO_MODEL_NOT_READY
DATA_TIDAK_CUKUP
manual_review_required true
```

Jika model valid:

```text
MODEL_READY_FOR_FIELD_TRIAL
YOLO_DETECTION_READY
```

## Validasi wajib

Jalankan:

```powershell
.\venv\Scripts\python.exe -m py_compile src\ulp_project\plan_c_86_source_registry.py src\ulp_project\plan_c_86_license_policy.py src\ulp_project\plan_c_86_polite_downloader.py src\ulp_project\plan_c_86_manifest.py src\ulp_project\plan_c_86_pseudo_labeler.py src\ulp_project\plan_c_86_yolo_export.py src\ulp_project\plan_c_86_quality_gate.py src\ulp_project\plan_c_model_registry.py
.\venv\Scripts\python.exe scripts\plan_c_86_dataset_quality_gate.py
cmd /c "git diff --check"
```

Jika membuat smoke tambahan, jalankan juga.

## Git safety

Boleh stage:

```text
src/ulp_project/plan_c_86_*.py
src/ulp_project/plan_c_model_registry.py
scripts/plan_c_86_*.py
scripts/plan_c_87_*.py
scripts/plan_c_88_*.py
scripts/plan_c_89_*.py
docs/progress8/PLAN_C_8_*.md
tests/test_plan_c_86_*.py
.gitignore
```

Jangan stage:

```text
data/
runs/
weights/
models/*.pt
*.jpg
*.jpeg
*.png
*.webp
*.zip
.env
token
credential
ngrok
D:/Users/All Users/Downloads
```

## Commit message

Jika validasi PASS:

```text
Implement System C final dataset training and model integration pipeline
```

## Ringkasan akhir wajib

Berikan:

```text
HEAD sebelum
HEAD sesudah
jumlah source registry
jumlah kandidat gambar
jumlah gambar lokal
jumlah label YOLO
status Roboflow package
status dataset gate
status training gate
status model registry
status Plan C runtime
file yang di-stage
file yang tidak di-commit
```
