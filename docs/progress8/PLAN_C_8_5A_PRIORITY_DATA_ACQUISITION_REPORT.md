# Progress 8.5A Priority Data Acquisition

Judul kerja: `PROGRESS 8.5A PRIORITY DATA ACQUISITION FOR POHON SONO FIRST, THEN 20KV CONDUCTOR, THEN STRUCTURE SUPPORT`.

## Alasan

Field trial Plan C membutuhkan foto yang lebih banyak. Tahap 8.5A memprioritaskan kandidat legal untuk `pohon_sono` karena kekurangan foto target spesies adalah hambatan utama sebelum memperbaiki deteksi konduktor dan struktur.

Urutan prioritas:

1. `pohon_sono` / Angsana / `Pterocarpus indicus` / Sonokembang / Narra.
2. `konduktor` overhead distribution/medium voltage/20 kV jika metadata menyebut eksplisit.
3. `struktur_penyangga` seperti utility pole, electric pole, concrete pole, crossarm.

Negative sample hanya untuk membantu false-positive review.

## Sumber Legal

Pipeline mendukung:

- Wikimedia Commons melalui MediaWiki API.
- GBIF occurrence media untuk `Pterocarpus indicus`.
- iNaturalist observation photo untuk `Pterocarpus indicus`.
- Wikimedia Commons category untuk conductor dan utility pole/crossarm.

Sumber yang tidak dipakai:

- Google Images langsung.
- Pinterest, Instagram, Facebook, TikTok.
- Blog atau dataset tanpa lisensi jelas.
- GitHub sebagai sumber media.

## License Policy

Allowed:

- CC0
- Public Domain
- CC BY
- CC BY-SA

Restricted review-only:

- CC BY-NC
- CC BY-NC-SA
- CC BY-ND
- CC BY-NC-ND

Reject:

- all rights reserved
- unknown
- no license
- unclear

## Output Folder

Runtime dan media kandidat ditulis ke folder yang tidak boleh di-commit:

```text
data/external_dataset_inbox/
data/runtime/plan_c_dataset_acquisition/
```

Manifest:

```text
data/runtime/plan_c_dataset_acquisition/manifests/
```

Package review:

```text
data/runtime/plan_c_dataset_acquisition/roboflow_package/
data/runtime/plan_c_dataset_acquisition/yolov8_review_package/
```

## Dry-Run

```powershell
.\venv\Scripts\python.exe scripts\plan_c_priority_acquire_pohon_sono.py --source wikimedia --limit 150 --dry-run
.\venv\Scripts\python.exe scripts\plan_c_priority_acquire_pohon_sono.py --source all --limit 300 --dry-run
.\venv\Scripts\python.exe scripts\plan_c_priority_acquire_conductor.py --limit 100 --dry-run
.\venv\Scripts\python.exe scripts\plan_c_priority_acquire_structure.py --limit 80 --dry-run
```

## Download Legal Terbatas

Download harus eksplisit:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_priority_acquire_pohon_sono.py --source wikimedia --limit 150 --download
.\venv\Scripts\python.exe scripts\plan_c_priority_acquire_pohon_sono.py --source gbif --limit 100 --download
.\venv\Scripts\python.exe scripts\plan_c_priority_acquire_pohon_sono.py --source inaturalist --limit 100 --download
```

Pipeline tidak mengunduh license reject. Restricted license tidak masuk package final training.

## Package Review

Roboflow:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_priority_build_roboflow_package.py --mode dry-run
.\venv\Scripts\python.exe scripts\plan_c_priority_build_roboflow_package.py --mode build
```

YOLOv8 review-only:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_priority_build_yolov8_review_package.py --mode dry-run
.\venv\Scripts\python.exe scripts\plan_c_priority_build_yolov8_review_package.py --mode build
```

Dataset gate:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_priority_dataset_gate.py
```

Status gate:

- `PLAN_C_PRIORITY_DATASET_NOT_ENOUGH`
- `PLAN_C_PRIORITY_DATASET_READY_FOR_ROBOFLOW_REVIEW`

Tidak ada status final training pada tahap ini.

## Batasan

- Kandidat belum siap training sebelum review manual.
- Pseudo-label bersifat draft review-only.
- Jika internet/API tidak tersedia, pipeline tetap siap dan mengembalikan `INTERNET_UNAVAILABLE_PIPELINE_READY` atau `SOURCE_UNAVAILABLE_OR_RATE_LIMITED`, bukan hasil palsu.
- Konduktor generic distribution tidak diklaim 20 kV kecuali metadata menyebut 20 kV.
