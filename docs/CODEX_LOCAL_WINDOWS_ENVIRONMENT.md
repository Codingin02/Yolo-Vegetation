# Codex Local Windows Environment

Dokumen ini menjelaskan konfigurasi aman untuk menjalankan Codex di proyek lokal:

```text
E:\Projects\ULP_Project
```

## Mode Kerja

- Work locally.
- Branch wajib: `system-finalization-no-label-touch`.
- Tidak memakai new worktree.
- Tidak memakai cloud/web worktree.
- Tidak memakai Docker untuk Phase 3.
- Tidak memakai npm karena project utama adalah Python dan belum memiliki kebutuhan frontend build.

## Setup Aman

Setup script Windows cukup `verify-only`:

```powershell
git branch --show-current
git rev-parse --short HEAD
.\venv\Scripts\python.exe --version
.\venv\Scripts\python.exe -m pytest -q
```

Tujuannya hanya memastikan branch, Python venv, dan test lokal siap. Setup tidak boleh menulis ke folder data.

## Cleanup Aman

Cleanup harus `no-op` untuk folder project. Jangan hapus:

- `data/`
- `dataset_botol/`
- `results/`
- `runs/`
- `weights/`
- `models/`
- `.codex/environments/environment.toml`

File `.codex/environments/environment.toml` adalah konfigurasi lokal dan tidak masuk commit.

## Alasan Tidak Memakai npm, Docker, atau Cloud

- `npm`: belum ada kebutuhan build frontend; dashboard saat ini scaffold Flask lokal.
- `Docker`: tidak perlu untuk validasi Phase 3, dan dapat menambah risiko path/data mounting.
- `cloud/web worktree`: data lapangan dan labeling bersifat lokal; mode aman adalah bekerja di repo Windows lokal.

## Batas No-Label-Touch

Codex tidak boleh menulis ke:

- `data/dataset_yolo/00_review_candidates/`
- `data/exports/`
- `data/raw/`
- `data/gps/`
- `data/processed/`
- `data/dataset_yolo/field_multiclass_v1/`
- `dataset_botol/`
- `results/`
- `runs/`
- `weights/`
- `models/`
