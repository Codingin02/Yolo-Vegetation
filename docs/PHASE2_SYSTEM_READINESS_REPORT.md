# Phase 2 System Readiness Report

## Identitas

- Branch aktif: `system-finalization-no-label-touch`
- Commit awal sebelum edit Phase 2: `0cff7d8`
- Mode: `SYSTEM_SCAFFOLD_HARDENING_AND_VALIDATION`
- Status label: `WAITING_FOR_MAKESENSE_EXPORT`
- Status training final: `NOT_RUN`

## File Dibuat atau Diubah

File baru:

- `docs/LEGACY_SCRIPTS_AUDIT.md`
- `docs/PHASE2_SYSTEM_READINESS_REPORT.md`
- `pytest.ini`
- `scripts/phase2_system_smoke_test.py`
- `tests/test_risk_stub.py`

File diperbaiki:

- `src/ulp_project/makesense_import.py`
- `src/ulp_project/dataset_split.py`
- `src/ulp_project/train_launcher.py`
- `tests/test_yolo_validator.py`
- `tests/test_dataset_splitter.py`
- `tests/test_paths.py`

## Hasil Compileall

Command:

```powershell
.\venv\Scripts\python.exe -m compileall src scripts tests
```

Hasil: `PASS`

Catatan: compileall hanya melakukan syntax/bytecode check. Tidak menjalankan training, kamera, ngrok, import label final, atau build dataset final.

## Hasil Pytest

Command:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Hasil akhir:

```text
14 passed in 0.12s
```

Catatan: percobaan awal `pytest -q` timeout karena Pytest ikut mengoleksi file legacy `scripts/test_*.py` yang bukan unit test aman. Ditambahkan `pytest.ini` agar discovery hanya membaca `tests/`.

## Hasil Phase 2 Smoke Test

Command:

```powershell
.\venv\Scripts\python.exe scripts\phase2_system_smoke_test.py
```

Hasil:

```text
PHASE2_SYSTEM_SMOKE_PASS
```

Ringkasan cek:

- Class order tetap `0 struktur_penyangga`, `1 konduktor`, `2 pohon_sono`.
- `dataset_botol` bukan dataset utama.
- Importer dry-run tidak menyalin label.
- Generator `data.yaml` memakai class order terkunci.
- Risk skeleton mengembalikan `ENV_DATA_NOT_AVAILABLE`, bukan klaim prediksi final.
- CLI `--help` untuk script scaffold utama berjalan.
- Dataset builder dry-run tetap `LABELS_NOT_READY`.

## Hasil Dry-Run Import makesense.ai

Command:

```powershell
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
```

Hasil:

```text
status: LABELS_NOT_READY
images_found: 19
labels_found_in_export: 0
matched_labels: 0
missing_labels: 19
orphan_labels: 0
copied_labels: 0
skipped_existing_labels: 0
invalid_export_labels: 0
manifest: SKIPPED_BY_DRY_RUN
```

Catatan: dry-run tidak menulis manifest otomatis dan tidak menyalin label.

## Hasil Dry-Run Build Dataset

Command:

```powershell
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
```

Hasil:

```text
status: LABELS_NOT_READY
total_pairs: 0
train_count: 0
val_count: 0
target_dir: E:\Projects\ULP_Project\data\dataset_yolo\field_multiclass_v1
result: WAITING_FOR_LABELS
```

Catatan: tidak membuat dataset final karena label belum lengkap.

## Hasil Dry-Run Train Launcher

Command:

```powershell
.\venv\Scripts\python.exe scripts\train_yolov8_field_multiclass.py --dry-run
```

Hasil:

```text
dataset_status: DATASET_NOT_READY
reason: missing data.yaml: E:\Projects\ULP_Project\data\dataset_yolo\field_multiclass_v1\data.yaml
result: DATASET_NOT_READY
```

Catatan: launcher tidak menjalankan training final.

## Bukti Folder Labeling Tidak Disentuh

Tidak ada file yang dibuat/diubah/stage di:

- `data/dataset_yolo/00_review_candidates/`
- `data/exports/`
- `data/raw/`
- `data/gps/`
- `data/processed/`
- `data/dataset_yolo/field_multiclass_v1/`

Dry-run import hanya membaca `images_selected` untuk menghitung gambar dan tidak menulis ke `labels_selected`.

## Bukti dataset_botol Tidak Dipakai Sebagai Dataset Utama

- Target dataset utama tetap `data/dataset_yolo/field_multiclass_v1`.
- Test `tests/test_no_dataset_botol_as_main.py` memastikan `dataset_botol` berbeda dari target dataset utama.
- Smoke test Phase 2 juga memeriksa `DATASET_BOTOL_DIR != FIELD_DATASET_DIR`.

## Command Setelah Export YOLO Dari makesense.ai Selesai

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy
.\venv\Scripts\python.exe scripts\validate_yolo_labels.py --point V001_pohon_sono
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode build --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\generate_data_yaml.py --mode write
.\venv\Scripts\python.exe scripts\train_yolov8_field_multiclass.py --dry-run
```

Training final hanya boleh dijalankan setelah validator label `VALID`.
