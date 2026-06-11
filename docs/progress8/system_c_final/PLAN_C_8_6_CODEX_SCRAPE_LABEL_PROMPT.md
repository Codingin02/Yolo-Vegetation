# PLAN C 8.6 — Prompt Codex untuk Scraping Legal + Pseudo-Label + Dataset Final

Gunakan prompt ini di percakapan Codex baru.

---

Anda bekerja di repo lokal:

```text
E:\Projects\ULP_Project
```

Mode kerja:

```text
Work locally
Jangan New worktree
Jangan buat branch baru
Jangan checkout
Jangan reset
Jangan git add .
Jangan commit sebelum semua validasi PASS
```

## Tujuan

Selesaikan tahap Progress 8.6: akuisisi dataset final YOLOv8 untuk Plan C, dengan prioritas utama pohon_sono/Pterocarpus indicus, kemudian konduktor, kemudian struktur_penyangga, dan negative sample. Jangan mengubah runtime Flask `/plan-c` kecuali hanya membaca kontrak class. Jangan menyentuh UI.

Dataset target final:

```text
E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1
```

Folder ini adalah folder dataset YOLO final target. Gambar/label yang belum direview harus diberi status `needs_manual_check` dalam manifest. Jangan klaim label otomatis sebagai label manual final.

## Prioritas class

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono
```

Prioritas eksekusi:

1. pohon_sono sebanyak mungkin dan legal.
2. konduktor sebanyak mungkin dan legal.
3. struktur_penyangga sebanyak mungkin dan legal.
4. negative sample sebanyak mungkin untuk manusia, kendaraan, tembok, indoor object, dan pohon non-sono.

## Sumber minimal

Jangan hanya Wikimedia. Buat source registry minimal 15 sumber, termasuk Wikimedia Commons, GBIF, iNaturalist, Flickr Creative Commons, Openverse, EOL, PlantNet, India Biodiversity Portal, Atlas of Living Australia, Kew/POWO reference-only, NParks reference-only, Useful Tropical Plants reference-only, Roboflow Universe per-project license, Open Images, MS COCO, LVIS, Mapillary, ADE20K, LabelMe, dan foto lapangan sendiri.

Jika sumber tidak punya API atau license jelas, jangan download langsung. Masukkan sebagai `REFERENCE_ONLY` atau `REJECT_LICENSE_UNCLEAR`.

## Download policy

Implementasikan polite downloader:

- satu proses saja,
- tidak paralel agresif,
- User-Agent jelas,
- delay antar-request,
- exponential backoff untuk HTTP 429,
- simpan URL yang sudah dicoba agar tidak diulang,
- jika 429 lebih dari batas, pindah sumber lain,
- jangan loop tanpa akhir,
- batas waktu total per source,
- semua output dicatat ke manifest.

## Pseudo-label / bounding policy

Buat label YOLO-compatible `.txt` untuk kandidat yang cukup jelas. Label otomatis harus status `needs_manual_check`.

Aturan bbox:

- `pohon_sono`: bbox seluruh pohon atau bagian pohon yang terlihat, bukan langit/gedung/orang.
- `konduktor`: bbox mengikuti kabel; jika ada 3 kabel terpisah, buat 3 bbox; jika ada lebih dari 3, bbox semua yang terlihat.
- `struktur_penyangga`: bbox tiang/crossarm/struktur, bukan tembok atau lemari.
- `pohon_non_sono`: bbox pohon yang bukan sono.
- manusia/wajah/kendaraan/tembok/indoor object tidak boleh dilabeli sebagai target.

Jika bbox tidak yakin, jangan buat label target. Masukkan `needs_manual_check`.

## Roboflow package

Buat package untuk upload ke Roboflow:

```text
data/dataset_yolo/plan_c_final_v1/roboflow_package
```

Isi:

```text
images/
labels/
data.yaml
README_ROBOFLOW_REVIEW.md
source_manifest.csv
license_manifest.csv
review_manifest.csv
```

## Dataset gate

Buat script:

```text
scripts/plan_c_86_dataset_quality_gate.py
```

Gate harus memeriksa jumlah gambar/label per class, split train/val/test, format YOLO, bbox tidak keluar image, manifest license/source lengkap, duplicate sha256, file kosong, negative sample tidak diberi bbox target, dan roboflow package tersedia.

Target minimum:

```text
pohon_sono: 80 gambar accepted/review candidate
konduktor: 60 gambar accepted/review candidate
struktur_penyangga: 40 gambar accepted/review candidate
pohon_non_sono: 60 gambar
non_target_negative: 100 gambar
```

Jika belum tercapai, jangan membuat angka palsu. Tulis kekurangan di report.

## File yang harus dibuat

```text
src/ulp_project/plan_c_86_source_registry.py
src/ulp_project/plan_c_86_license_policy.py
src/ulp_project/plan_c_86_polite_downloader.py
src/ulp_project/plan_c_86_source_wikimedia.py
src/ulp_project/plan_c_86_source_gbif.py
src/ulp_project/plan_c_86_source_inaturalist.py
src/ulp_project/plan_c_86_source_flickr.py
src/ulp_project/plan_c_86_source_openverse.py
src/ulp_project/plan_c_86_manifest.py
src/ulp_project/plan_c_86_pseudo_labeler.py
src/ulp_project/plan_c_86_yolo_export.py
src/ulp_project/plan_c_86_quality_gate.py
scripts/plan_c_86_acquire_pohon_sono_priority.py
scripts/plan_c_86_acquire_conductor_priority.py
scripts/plan_c_86_acquire_structure_priority.py
scripts/plan_c_86_acquire_negative_priority.py
scripts/plan_c_86_build_dataset_final.py
scripts/plan_c_86_build_roboflow_package.py
scripts/plan_c_86_dataset_quality_gate.py
docs/progress8/PLAN_C_8_6_DATASET_FINALIZATION_REPORT.md
docs/progress8/PLAN_C_8_6_SOURCE_REGISTRY_REPORT.md
docs/progress8/PLAN_C_8_6_ROBOFLOW_PACKAGE_REPORT.md
```

## Git safety

Jangan stage gambar, label, zip, model, `.env`, token, credential, URL ngrok, `runs/`, `weights/`, `models/`, `data/runtime/`, atau `data/external_dataset_inbox/`.

Boleh stage source code, scripts, docs, tests, dan `.gitignore` bila perlu.

Commit message jika semua validasi PASS:

```text
Implement Progress 8.6 final YOLO dataset acquisition and Roboflow package pipeline
```
