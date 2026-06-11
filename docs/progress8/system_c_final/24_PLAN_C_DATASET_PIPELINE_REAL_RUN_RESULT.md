# Progress 8.8 / System C Dataset Pipeline Real Run Result

Tanggal run: 2026-06-11

## Ringkasan

Pipeline dataset System C sudah diperbaiki agar HTTP 429 tidak menghentikan seluruh run. Downloader sekarang mencatat URL/source yang terkena rate limit sebagai `RATE_LIMITED_RETRY_LATER`, lalu melanjutkan kandidat berikutnya. Setelah source/host terkena 429 berulang dalam satu run, kandidat berikutnya dari source/host itu dicatat sebagai `RATE_LIMITED_RETRY_LATER_SOURCE_SKIPPED` tanpa request tambahan.

Pipeline juga sudah menulis output nyata ke dataset final YOLO review-only:

- Dataset final: `E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1`
- Download/staging: `D:\Users\All Users\Downloads\ULP_Project_PlanC_Dataset_Downloads`
- Roboflow package: `E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1\roboflow_package`
- Manifest download terbaru: `data\dataset_yolo\plan_c_final_v1\review\system_c_download_manifest_20260611_200318.csv`
- Manifest review terbaru: `data\dataset_yolo\plan_c_final_v1\review\system_c_yolo_review_manifest_20260611_200319.csv`

## Perubahan Pipeline

- `download_candidate()` tidak lagi melempar exception untuk satu URL gagal.
- Semua HTTP request memakai User-Agent:
  `ULPPlanCResearchDatasetBot/1.0 (academic field-trial dataset; contact: local-project)`
- HTTP 429 membaca `Retry-After` jika tersedia.
- Pipeline utama men-skip source/host setelah 429 berulang dalam run yang sama.
- Source rotation mencakup Wikimedia, GBIF, iNaturalist, Openverse, dan placeholder Flickr controlled-skip jika tidak ada API key.
- Filter lisensi menerima variasi legal seperti `cc0`, `cc-by`, `cc-by-sa`, dan URL Creative Commons.
- Filter iNaturalist/GBIF diperketat: occurrence `pohon_sono` harus benar-benar `Pterocarpus indicus`, bukan common-name ambigu.
- Export dataset final melakukan dedupe berbasis hash/URL sebelum split.
- Export managed membersihkan artefak class-prefix lama agar gate tidak membaca duplikat run sebelumnya.
- Autolabel review-only membuat label YOLO hanya ketika segmentasi vegetasi cukup yakin. Jika tidak yakin, gambar masuk review queue tanpa label palsu.

## Hasil Run Nyata

Command:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_system_c_run_all_dataset_pipeline.py --download --autolabel --build-roboflow --gate --train-if-ready --register-if-valid --limit-per-source 30
```

Status pipeline:

- `SYSTEM_C_PIPELINE_COMPLETED_WITH_SAFE_SKIPS`
- Source registry count: 37
- Candidate rows pada download manifest: 678
- Downloaded/already exists: 12
- Export dedupe ke dataset final: 6 gambar
- Label YOLO review-only valid: 5
- Needs manual check tanpa label: 1
- Duplicate image hash: 0

## Accepted / Restricted / Rejected

Berdasarkan manifest download terbaru:

- `ACCEPT_TRAINING_REFERENCE`: 15
- `RESTRICTED_REFERENCE_ONLY`: 232
- `REJECT_LICENSE_UNCLEAR`: 44
- `RATE_LIMITED_RETRY_LATER`: 387

Download status:

- `DOWNLOADED_ALREADY_EXISTS`: 12
- `DOWNLOAD_SKIPPED_NOT_ALLOWED`: 276
- `RATE_LIMITED_RETRY_LATER`: 3
- `RATE_LIMITED_RETRY_LATER_SOURCE_SKIPPED`: 387

Per target candidate:

- `pohon_sono`: 438
- `konduktor`: 120
- `struktur_penyangga`: 120

Per target yang masuk review export:

- `pohon_sono`: 6 gambar
- `konduktor`: 0 gambar
- `struktur_penyangga`: 0 gambar
- `pohon_non_sono`: 0 gambar
- `non_target`: 0 gambar

## Autolabel YOLO Review-Only

Label yang dibuat:

- Class `2 pohon_sono`: 5 label valid
- Class `0 struktur_penyangga`: 0
- Class `1 konduktor`: 0
- Class `3 pohon_non_sono`: 0

Catatan:

- Semua label adalah draft review-only, bukan ground truth.
- Tidak ada bbox palsu untuk konduktor/struktur.
- Gambar yang segmentasi vegetasinya tidak cukup yakin dimasukkan ke review manual.

## Roboflow Package

Status:

- `ROBOFLOW_REVIEW_PACKAGE_READY`
- Copied images: 6
- Copied label files: 5

Package harus direview manual di Roboflow sebelum dataset dianggap siap training.

## Training Gate

Status:

- `YOLO_TRAINING_SKIPPED_DATASET_NOT_READY`
- Training tidak dijalankan.
- Model registry belum dibuat.
- Runtime Plan C tetap safe mode jika registry belum valid.

Kondisi gate terbaru:

- `pohon_sono`: 6 image, 5 label; target minimal 80 image dan 80 label.
- `konduktor`: 0 image, 0 label; target minimal 60 image dan 60 label.
- `struktur_penyangga`: 0 image, 0 label; target minimal 40 image dan 40 label.
- `pohon_non_sono`: 0 image; target minimal 40 image.
- `non_target_negative`: 0 image; target minimal 60 image.

## Error 429

Sumber/host yang kena rate limit:

- `api.openverse.org`
- `commons.wikimedia.org`
- beberapa image URL Wikimedia upload saat download file besar.

Status akhir:

- HTTP 429 tidak lagi menghentikan pipeline.
- Source/host yang kena 429 berulang di-skip sementara dalam run yang sama.
- Tidak ada candidate palsu yang dibuat untuk mengganti candidate rate-limited.

## Next Action

Dataset belum cukup untuk training. Langkah berikutnya:

1. Jalankan ulang pipeline dengan jeda lebih panjang atau limit lebih kecil untuk host yang kena 429.
2. Prioritaskan `pohon_sono` dari GBIF/iNaturalist/Wikimedia yang sudah memiliki metadata `Pterocarpus indicus`.
3. Tambahkan sumber legal untuk `konduktor` dan `struktur_penyangga` yang tidak bergantung hanya pada Wikimedia/Openverse.
4. Upload Roboflow package saat ini hanya untuk review awal, bukan training final.
5. Setelah jumlah image/label memenuhi gate, jalankan training gate ulang sebelum training.

Tidak ada klaim akurasi final, tidak ada fake label, dan tidak ada model siap runtime yang dibuat pada tahap ini.
