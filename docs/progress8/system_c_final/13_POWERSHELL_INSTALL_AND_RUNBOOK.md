# SYSTEM C FINAL — PowerShell Install and Runbook

## Tujuan

File ini menjelaskan cara menaruh semua dokumen acuan ke repo lokal.

ZIP yang diunduh:

```text
plan_c_system_c_final_docs.zip
```

Folder download yang diminta:

```text
D:\Users\All Users\Downloads
```

Folder tujuan repo:

```text
E:\Projects\ULP_Project\docs\progress8\system_c_final
```

## Cara pakai cepat

1. Download ZIP.
2. Simpan atau pindahkan ZIP ke:

```text
D:\Users\All Users\Downloads\plan_c_system_c_final_docs.zip
```

3. Jalankan PowerShell.
4. Paste isi file:

```text
INSTALL_SYSTEM_C_FINAL_DOCS.ps1
```

Script akan:

```text
- cek E:\Projects\ULP_Project
- buat folder docs\progress8\system_c_final
- extract semua file MD ke sana
- buat folder download dataset di D:\Users\All Users\Downloads\ULP_Project_PlanC_Dataset_Downloads
- buat folder dataset final di E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1
- tidak git add
- tidak commit
- tidak menghapus file
```

## Setelah install

Buka Codex dan gunakan prompt:

```text
E:\Projects\ULP_Project\docs\progress8\system_c_final\12_CODEX_MASTER_PROMPT_SYSTEM_C_FINAL.md
```

## Jangan jalankan training sebelum dataset gate

Training hanya boleh jalan jika gate siap. Jika belum, status yang benar adalah:

```text
YOLO_TRAINING_SKIPPED_DATASET_NOT_READY
```
