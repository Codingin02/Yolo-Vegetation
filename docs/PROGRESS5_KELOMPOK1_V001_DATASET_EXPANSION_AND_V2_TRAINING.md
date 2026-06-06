# Progress 5 Kelompok 1 - V001 Dataset Expansion and V2 Training

## Tujuan

Progress 5 Kelompok 1 menyiapkan ekspansi dataset khusus `V001_pohon_sono` untuk kandidat YOLOv8n single-class v2. Target kelas tetap hanya:

```yaml
0: pohon_sono
```

Baseline Progress 4 tetap dikunci sebagai kandidat v1:

```text
runs/detect/v001_pohon_sono_only_v1/weights/best.pt
```

File baseline tersebut tidak boleh dioverwrite.

## Batas terhadap Kelompok 2

Progress ini tidak mengubah runtime Kelompok 2. Tidak ada perubahan Flask, Ngrok, WebSocket, GPS, map, Google Sheets, dashboard, prediksi trimming, ETA, atau clearance. Output Progress 5 Kelompok 1 hanya dataset expansion, label review handoff, training candidate v2, dan comparison v1 vs v2.

## Kenapa tidak training prediksi trimming dulu

Model v1 baru kandidat deteksi pohon sono. Prediksi trimming membutuhkan bukti deteksi yang stabil, geometri lapangan, validasi jarak, dan kebijakan operasional terpisah. Karena itu Progress 5 Kelompok 1 tidak membuat klaim clearance, tidak membuat ETA trimming, dan tidak membuat rekomendasi eksekusi lapangan.

## Kenapa tidak multi-class dulu

Fase ini sengaja single-class karena tujuan terdekat adalah memperbaiki deteksi `pohon_sono`. Kelas project final tetap diingat:

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
```

Namun P001/K001 tidak dimasukkan ke training v2. Multi-class final menunggu data conductor dan struktur yang cukup serta validasi terpisah.

## Status Data Raw dari Operator

Data raw terbaru yang menjadi konteks:

- `data/raw/01_field_points/V001_pohon_sono/images`: 8 jpg
- `data/raw/01_field_points/V001_pohon_sono/videos`: 1 mp4
- `data/raw/01_field_points/P001_struktur_penyangga/images`: 5 jpg
- `data/raw/01_field_points/P001_struktur_penyangga/videos`: 1 mp4
- `data/raw/01_field_points/K001_konduktor/images`: 6 jpg
- `data/raw/01_field_points/K001_konduktor/videos`: 1 mp4
- Folder P001 sampai P017 tersedia.
- Folder K001 dan K002 tersedia.

Raw data hanya dibaca. Tidak ada move, rename, atau delete.

## Alur Frame Extraction

Command:

```powershell
.\venv\Scripts\python.exe scripts\progress5_extract_v001_frames.py
```

Default input:

```text
data/raw/01_field_points/V001_pohon_sono/videos
```

Default output:

```text
data/dataset_yolo/00_review_candidates/V001_pohon_sono_v2/images_all
```

Sampling default adalah 1 frame per 1 detik. Nama frame memakai prefix:

```text
V001_pohon_sono_frame_000001.jpg
```

File existing tidak dioverwrite. Ringkasan ditulis ke:

```text
data/metadata/progress5_v001_frame_extract_summary.json
```

## Alur Quality Filter

Command:

```powershell
.\venv\Scripts\python.exe scripts\progress5_filter_v001_frame_quality.py
```

Filter menilai blur Laplacian, brightness mean, dan duplicate sederhana. File sumber tidak dihapus dan tidak dipindah. Frame disalin ke:

```text
data/dataset_yolo/00_review_candidates/V001_pohon_sono_v2/images_selected
data/dataset_yolo/00_review_candidates/V001_pohon_sono_v2/images_rejected
```

Filter kualitas bukan auto-label. Operator tetap wajib review apakah pohon sono jelas dan apakah tajuk perlu box ketat.

## Alur Review Label

Setelah `images_selected` siap, operator memberi label YOLO single-class:

```text
0 pohon_sono
```

Label disimpan ke:

```text
data/dataset_yolo/00_review_candidates/V001_pohon_sono_v2/labels_selected
```

Audit label:

```powershell
.\venv\Scripts\python.exe scripts\progress5_audit_v001_labels.py
```

Audit menolak label kosong, label hilang, orphan label, format non-YOLO, koordinat di luar 0 sampai 1, width/height tidak positif, dan class selain 0.

## Alur Build Dataset V2

Dry-run:

```powershell
.\venv\Scripts\python.exe scripts\progress5_build_v001_dataset_v2.py --mode dry-run
```

Build setelah audit PASS:

```powershell
.\venv\Scripts\python.exe scripts\progress5_build_v001_dataset_v2.py --mode build
```

Output:

```text
data/dataset_yolo/v001_pohon_sono_only_v2
```

Split stabil 80/20 memakai seed aman `1576037691`. Dataset hanya V001, tidak memakai P001/K001 dan tidak memakai `dataset_botol`.

## Alur Train V2

Dry-run:

```powershell
.\venv\Scripts\python.exe scripts\progress5_train_v001_yolov8n_v2.py
```

Training nyata setelah dataset valid:

```powershell
.\venv\Scripts\python.exe scripts\progress5_train_v001_yolov8n_v2.py --epochs 50 --imgsz 640 --batch 4 --run
```

Output run:

```text
runs/detect/v001_pohon_sono_only_v2
```

`exist_ok=False` dipakai agar run v2 tidak dioverwrite.

## Alur Compare V1 vs V2

Setelah v2 `best.pt` tersedia:

```powershell
.\venv\Scripts\python.exe scripts\progress5_compare_v001_v1_v2.py
```

Comparison memakai confidence operator `0.25`. Ultra-low confidence tidak digunakan sebagai output operator. Visual comparison ditulis ke:

```text
results/progress5_v001_compare_v1_v2
```

Summary ditulis ke:

```text
data/metadata/progress5_v001_compare_v1_v2_summary.json
```

## Batas Klaim

Status v2 adalah candidate only. Bukan model production, bukan final accuracy, bukan clearance prediction, dan bukan prediksi trimming. Jika deteksi lemah atau over-detection, status harus dilaporkan apa adanya.

## Gate

Command:

```powershell
.\venv\Scripts\python.exe scripts\progress5_kelompok1_gate.py
```

Gate dapat menghasilkan:

```text
PROGRESS5_KELOMPOK1_READY_FOR_V001_DATASET_EXPANSION
PROGRESS5_WAITING_FOR_V001_LABEL_REVIEW
PROGRESS5_V001_POHON_SONO_V2_TRAINING_CANDIDATE_READY
```

Jika `labels_selected` belum ada, berhenti di `PROGRESS5_WAITING_FOR_V001_LABEL_REVIEW` dan jangan build dataset atau training.
