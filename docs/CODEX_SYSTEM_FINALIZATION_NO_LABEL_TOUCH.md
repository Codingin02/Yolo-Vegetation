# CODEX_SYSTEM_FINALIZATION_NO_LABEL_TOUCH.md

## 0. Identitas Dokumen

Dokumen ini adalah instruksi kerja untuk **Codex / Agent Coding** pada proyek:

```text
Project root : E:\Projects\ULP_Project
Project name : ULP_Project
Context      : Magang PT PLN UP3 Surabaya Utara ULP Perak
Author       : Ahmad Bagus Idkholus Surur
NIM          : 23050874166
```

Tujuan dokumen ini adalah menjalankan **Kelompok B: Sistem dan Finalisasi** secara paralel dengan **Kelompok A: Labeling di makesense.ai**, tanpa mengganggu, mengubah, merusak, atau memaksa penyelesaian proses labeling.

---

## 1. Keputusan Arsitektur Kerja Paralel

Proyek sekarang dibagi menjadi dua kelompok kerja:

### Kelompok A — Labeling Manual di makesense.ai

Kelompok ini dikerjakan manual oleh user.

Ruang kerja utama:

```text
E:\Projects\ULP_Project\data\dataset_yolo\00_review_candidates\V001_pohon_sono\images_selected
E:\Projects\ULP_Project\data\dataset_yolo\00_review_candidates\V001_pohon_sono\labels_selected
E:\Projects\ULP_Project\data\dataset_yolo\00_review_candidates\V001_pohon_sono\classes.txt
```

Status saat ini:

```text
Point awal labeling : V001_pohon_sono
Jumlah gambar awal  : 19 gambar selected
Tool labeling       : makesense.ai
LabelImg            : dihentikan karena crash PyQt/Qt float-int
```

Codex **DILARANG** mengubah folder labeling aktif.

### Kelompok B — Sistem dan Finalisasi

Kelompok ini boleh dikerjakan oleh Codex/Agent sekarang, selama tidak membutuhkan label final.

Targetnya adalah menyiapkan semua sistem setelah labeling selesai, sehingga begitu file YOLO dari makesense.ai sudah tersedia, pipeline bisa langsung:

```text
import label -> validasi -> split dataset -> data.yaml -> training YOLOv8 -> evaluasi -> inference -> Flask -> peta -> spreadsheet/report
```

---

## 2. Baseline Project yang Tidak Boleh Diubah

Codex wajib menjaga baseline berikut.

### 2.1 Folder utama

```text
E:\Projects\ULP_Project
```

### 2.2 Virtual environment utama

```text
E:\Projects\ULP_Project\venv
```

### 2.3 Folder data mentah HP

```text
E:\Projects\ULP_Project\data\raw\00_inbox_hp
E:\Projects\ULP_Project\data\gps\00_inbox_hp
```

### 2.4 Folder data lapangan hasil sorting

```text
E:\Projects\ULP_Project\data\raw\01_field_points
E:\Projects\ULP_Project\data\gps\01_field_points
```

### 2.5 Folder frame hasil ekstraksi video

```text
E:\Projects\ULP_Project\data\processed\frames\01_field_points
```

### 2.6 Folder kandidat review YOLO

```text
E:\Projects\ULP_Project\data\dataset_yolo\00_review_candidates
```

### 2.7 Dataset botol

```text
dataset_botol
```

`dataset_botol` hanya dataset uji/stabilizer YOLO dari Progress 1–3. Dataset ini **bukan** dataset utama proyek, **bukan** dataset training final, dan **tidak boleh** dipakai sebagai dasar sistem deteksi PLN.

---

## 3. Aturan Nama Titik Lapangan

Codex wajib mempertahankan pola nama user.

```text
P001_struktur_penyangga
K001_konduktor
V001_pohon_sono
```

Penjelasan:

```text
P001 = titik 1 struktur penyangga
K001 = titik 1 konduktor/kabel
V001 = titik 1 vegetasi/pohon sono
```

Titik tidak harus urut spasial. Titik dapat acak karena user merekam per titik di lapangan, lalu pindah lokasi, lalu lanjut titik lain.

Codex tidak boleh mengubah pola ini menjadi `T001`, `point_001`, `pole_001`, atau format lain.

---

## 4. Class Order YOLO yang Dikunci

Class order final untuk proyek ini:

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
```

Isi `classes.txt` wajib:

```text
struktur_penyangga
konduktor
pohon_sono
```

Codex tidak boleh mengurutkan class secara alfabetis jika itu mengubah class id.

---

## 5. Larangan Mutlak untuk Codex

Codex **DILARANG** melakukan hal berikut:

```text
1. Mengubah, menghapus, merename, memindahkan, atau meng-copy ulang isi images_selected.
2. Menghapus atau menimpa labels_selected yang sedang/akan diisi hasil makesense.ai.
3. Mengubah classes.txt tanpa alasan valid.
4. Menggunakan dataset_botol sebagai dataset utama.
5. Mengubah pola folder P001/K001/V001.
6. Memaksa training final sebelum label YOLO valid.
7. Mengklaim akurasi, mAP, precision, recall, atau hasil model jika training belum benar-benar dijalankan.
8. Menjalankan LabelImg lagi sebagai tool utama.
9. Mengubah file raw/00_inbox_hp.
10. Mengubah file raw/01_field_points kecuali hanya membaca.
11. Mengubah file gps/00_inbox_hp.
12. Menghapus script progress sebelumnya.
13. Menghapus history, metadata, manifest, atau file status.
14. Menulis credential Google API ke repository.
15. Membuat perubahan besar tanpa mode dry-run atau backup.
```

---

## 6. Progress yang BOLEH Dikerjakan Sekarang Tanpa Menunggu Labeling

Codex boleh mengerjakan progress berikut sekarang.

| Progress | Modul | Boleh Dikerjakan Sekarang | Catatan |
|---:|---|---|---|
| 22 | Audit struktur repo | Ya | Baca folder dan buat status, tanpa mengubah labeling |
| 23 | Import hasil makesense | Ya, script saja | Eksekusi final setelah zip/export YOLO tersedia |
| 24 | Validator YOLO label | Ya | Bisa jalan pada label kosong/parsial |
| 25 | Dataset splitter train/val | Ya | Jangan run final jika label belum lengkap |
| 26 | Generator data.yaml | Ya | Class order sudah dikunci |
| 27 | Training launcher YOLOv8 | Ya | Default dry-run, training final nanti |
| 28 | Evaluasi model | Ya, skeleton | Tidak boleh klaim mAP sampai model ada |
| 29 | Inference gambar/video | Ya, skeleton | Bisa siapkan CLI |
| 30 | OpenCV edge refinement | Ya, skeleton | Jangan paksa hasil tanpa model |
| 31 | ByteTrack integration | Ya, skeleton | Tracking untuk video sesudah inference |
| 32 | Monocular scaling module | Ya, skeleton | Kalibrasi final menunggu data |
| 33 | GPS linker | Ya | GPS sudah tersedia dari sorting |
| 34 | Folium map export | Ya | Bisa buat map dari GPS/metadata |
| 35 | Flask backend | Ya | Boleh dengan placeholder safe |
| 36 | Spreadsheet export | Ya | CSV/template dulu, Google API optional |
| 37 | Report generator | Ya | Research/report template tanpa klaim akurasi |
| 38 | Environmental risk skeleton | Ya, schema dulu | Data BPS/BMKG/pH ditunda untuk Deep Research |
| 39 | Tests | Ya | Unit test untuk script non-label |
| 40 | Runbook final | Ya | Dokumen cara pakai end-to-end |

---

## 7. Progress yang HARUS Menunggu Labeling Selesai

Codex tidak boleh mengerjakan eksekusi final untuk bagian berikut sampai user memberi aba-aba bahwa hasil makesense.ai sudah selesai dan file YOLO sudah diekspor.

| Progress | Modul | Alasan Menunggu |
|---:|---|---|
| 20 | Labeling final | Dikerjakan manual oleh user di makesense.ai |
| 21 | Import label final | Butuh file YOLO export dari makesense.ai |
| 27-final | Training final YOLOv8 | Butuh label valid dan dataset split |
| 28-final | Evaluasi mAP/confusion matrix | Butuh model hasil training |
| 29-final | Inference validasi model | Butuh bobot model final |
| 30-final | Edge refinement terhadap deteksi nyata | Butuh output model |
| 31-final | Tracking real video | Butuh inference model |
| 32-final | Pengukuran jarak/tinggi final | Butuh deteksi objek dan kalibrasi |
| 38-final | Model risiko vegetasi berbasis data eksternal | Butuh Deep Research / data resmi |

---

## 8. Target File yang Harus Dibuat atau Diperbaiki Codex

Codex boleh membuat/memperbaiki file berikut.

```text
scripts/import_makesense_yolo.py
scripts/validate_yolo_labels.py
scripts/build_field_dataset.py
scripts/generate_data_yaml.py
scripts/train_yolov8_field.py
scripts/evaluate_yolov8_field.py
scripts/run_inference_field.py
scripts/link_gps_metadata.py
scripts/build_folium_map.py
scripts/export_field_spreadsheet.py
scripts/build_report_summary.py
scripts/edge_refinement.py
scripts/track_video_bytetrack.py
scripts/monocular_scaling.py
scripts/vegetation_risk_skeleton.py
scripts/project_status_audit.py

app/flask_app.py
app/templates/index.html
app/static/

configs/classes_field.yaml
configs/dataset_field.yaml
configs/runtime_paths.yaml

docs/RUNBOOK_FIELD_SYSTEM.md
docs/PROGRESS_SYSTEM_FINALIZATION.md
docs/LABELING_HANDOFF_MAKESENSE.md
docs/SAFETY_BOUNDARIES.md

tests/test_paths.py
tests/test_class_order.py
tests/test_yolo_label_format.py
tests/test_dataset_splitter.py
tests/test_gps_linker.py
```

Jika file sudah ada, Codex harus membaca dulu, lalu memperbaiki tanpa menghapus fungsi lama yang masih berguna.

---

## 9. Struktur Dataset Final yang Harus Disiapkan

Target dataset final setelah labeling selesai:

```text
E:\Projects\ULP_Project\data\dataset_yolo\field_multiclass_v1
├─ images
│  ├─ train
│  └─ val
├─ labels
│  ├─ train
│  └─ val
└─ data.yaml
```

Contoh `data.yaml`:

```yaml
path: E:/Projects/ULP_Project/data/dataset_yolo/field_multiclass_v1
train: images/train
val: images/val
names:
  0: struktur_penyangga
  1: konduktor
  2: pohon_sono
```

---

## 10. Script: Import Hasil makesense.ai

Buat script:

```text
scripts/import_makesense_yolo.py
```

Tujuan:

1. Membaca folder export YOLO dari makesense.ai.
2. Mencocokkan basename file `.txt` dengan gambar di `images_selected`.
3. Menyalin label `.txt` ke `labels_selected`.
4. Tidak menghapus label lama kecuali user memberi `--overwrite`.
5. Membuat manifest CSV.
6. Menolak class id selain 0, 1, 2.
7. Menolak label dengan format bukan YOLO normalized xywh.

Contoh CLI:

```powershell
python scripts\import_makesense_yolo.py ^
  --point V001_pohon_sono ^
  --export-dir E:\Exports\makesense_v001_yolo ^
  --mode dry-run

python scripts\import_makesense_yolo.py ^
  --point V001_pohon_sono ^
  --export-dir E:\Exports\makesense_v001_yolo ^
  --mode copy
```

Default wajib `dry-run`.

---

## 11. Script: Validator YOLO Label

Buat atau perbaiki:

```text
scripts/validate_yolo_labels.py
```

Wajib validasi:

```text
1. Setiap image_selected punya pasangan label .txt.
2. Tidak ada label yatim tanpa image.
3. Setiap baris label punya 5 kolom.
4. class_id hanya 0, 1, atau 2.
5. x_center, y_center, width, height berada pada 0..1.
6. width dan height > 0.
7. Tidak ada file kosong jika gambar punya objek.
8. Ringkasan class count dibuat.
9. Output manifest CSV dibuat.
```

Contoh CLI:

```powershell
python scripts\validate_yolo_labels.py --point V001_pohon_sono
```

---

## 12. Script: Build Dataset Train/Val

Buat:

```text
scripts/build_field_dataset.py
```

Fungsi:

1. Mengambil semua point yang sudah memiliki `images_selected` dan `labels_selected`.
2. Menyalin image dan label ke struktur final `field_multiclass_v1`.
3. Split train/val dengan seed tetap.
4. Menjaga nama file agar traceable.
5. Membuat manifest CSV.
6. Tidak mengambil dataset_botol.
7. Tidak mengambil images_all.
8. Tidak mengambil images_rejected.
9. Tidak mengambil raw inbox langsung.
10. Menolak dataset jika label belum valid.

Contoh CLI:

```powershell
python scripts\build_field_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
python scripts\build_field_dataset.py --mode build --val-ratio 0.2 --seed 23050874166
```

---

## 13. Script: Training Launcher YOLOv8

Buat:

```text
scripts/train_yolov8_field.py
```

Ketentuan:

1. Default mode adalah `dry-run`.
2. Tidak menjalankan training jika dataset belum valid.
3. Menyimpan hasil training ke folder project.
4. Tidak mengklaim hasil jika training gagal.
5. Menggunakan GPU jika tersedia, fallback CPU dengan warning.
6. Menulis log training.

Contoh CLI:

```powershell
python scripts\train_yolov8_field.py --mode dry-run
python scripts\train_yolov8_field.py --mode train --model yolov8n.pt --epochs 50 --imgsz 640
```

Output target:

```text
E:\Projects\ULP_Project\runs\detect\field_multiclass_v1
```

---

## 14. Flask Backend yang Boleh Disiapkan Sekarang

Buat atau rapikan:

```text
app/flask_app.py
```

Fitur minimal:

```text
1. Halaman dashboard project.
2. Upload image untuk inference.
3. Tampilkan hasil deteksi jika model tersedia.
4. Jika model belum tersedia, tampilkan status MODEL_NOT_READY.
5. Endpoint /health.
6. Endpoint /status.
7. Endpoint /map.
8. Endpoint /metadata.
```

Tidak boleh error jika model belum ada.

Contoh run:

```powershell
python app\flask_app.py
```

Default host:

```text
127.0.0.1
```

Default port:

```text
5000
```

---

## 15. Folium / Map GPS

Buat:

```text
scripts/build_folium_map.py
```

Fungsi:

1. Membaca GPS dari folder:

```text
data\gps\01_field_points
```

2. Membuat peta HTML:

```text
outputs\maps\field_points_map.html
```

3. Marker harus memakai nama titik asli:

```text
P001_struktur_penyangga
K001_konduktor
V001_pohon_sono
```

4. Jika GPS belum bisa diparse, jangan gagal total. Buat summary `GPS_PARSE_PARTIAL`.

---

## 16. Spreadsheet Export

Buat:

```text
scripts/export_field_spreadsheet.py
```

Output awal tidak perlu langsung Google Sheets API. Buat CSV/XLSX lokal dahulu.

Target output:

```text
outputs\spreadsheets\field_points_summary.csv
outputs\spreadsheets\field_points_summary.xlsx
```

Kolom minimal:

```text
point_id
object_group
object_name
raw_image_count
video_count
frame_count
selected_image_count
label_count
gps_file_count
latitude
longitude
source_status
label_status
training_status
notes
```

Google Sheets API boleh dibuat sebagai adapter optional:

```text
scripts/google_sheets_sync.py
```

Namun credential tidak boleh ditulis ke repo.

---

## 17. Environmental Risk Skeleton

Buat:

```text
scripts/vegetation_risk_skeleton.py
configs/environmental_risk_schema.yaml
docs/DEEP_RESEARCH_ENVIRONMENTAL_DATA_PLAN.md
```

Isi hanya schema dan rencana data, bukan angka palsu.

Variabel kandidat:

```text
curah_hujan
musim
kelembaban
suhu
jenis_tanah
pH_tanah
kedekatan_vegetasi_dengan_konduktor
tinggi_pohon_estimasi
jarak_pohon_ke_jaringan
kepadatan_vegetasi
riwayat pemangkasan
```

Sumber data yang nanti harus dicari via Deep Research:

```text
BPS
BMKG
KLHK
data.go.id
OpenStreetMap
literatur pertumbuhan pohon sono
dokumen PLN terkait ROW / pemeliharaan jaringan
```

Codex tidak boleh mengisi nilai lingkungan dari asumsi.

---

## 18. Testing Minimum

Codex wajib membuat testing minimal:

```text
python -m pytest tests
```

Jika pytest belum terpasang, boleh menambahkan ke requirements.

Test wajib:

```text
1. test_paths.py
2. test_class_order.py
3. test_yolo_label_format.py
4. test_dataset_splitter.py
5. test_gps_linker.py
```

---

## 19. Requirements

Codex boleh membuat atau memperbarui:

```text
requirements.txt
```

Candidate dependency:

```text
ultralytics
opencv-python
pandas
numpy
pyyaml
flask
folium
openpyxl
pytest
```

Jangan memasang dependency berat yang tidak dibutuhkan langsung.

---

## 20. Output Status

Setiap progress harus membuat status:

```text
data\metadata\system_finalization_status.json
data\metadata\system_finalization_status.txt
docs\PROGRESS_SYSTEM_FINALIZATION.md
```

Status wajib membedakan:

```text
READY
DRY_RUN_READY
WAITING_FOR_LABELS
SKIPPED_BY_DESIGN
FAILED
```

Contoh status yang benar:

```text
Label import script       : DRY_RUN_READY
YOLO validator            : READY
Dataset splitter          : WAITING_FOR_LABELS
Training launcher         : DRY_RUN_READY
Flask backend             : READY_WITH_MODEL_NOT_READY_STATE
Folium map                : READY_OR_GPS_PARTIAL
Google Sheets local export: READY_LOCAL_CSV_XLSX
Environmental model       : SCHEMA_READY_WAITING_DEEP_RESEARCH
```

---

## 21. Prompt Utama untuk Codex

Gunakan prompt ini di Codex/Agent Coding pada branch sistem-finalisasi.

```text
Kamu adalah coding agent untuk proyek E:\Projects\ULP_Project milik Ahmad Bagus Idkholus Surur, mahasiswa S1 Teknik Elektro UNESA, proyek magang PT PLN UP3 Surabaya Utara ULP Perak.

Tugasmu adalah mengerjakan KELOMPOK B: Sistem dan Finalisasi tanpa menyentuh KELOMPOK A: Labeling. User sedang melakukan labeling manual di makesense.ai. Jangan ubah images_selected, labels_selected, classes.txt, images_all, images_rejected, raw inbox, atau dataset_botol. dataset_botol hanya dataset uji stabilizer dari Progress 1–3, bukan dataset utama.

Baseline project:
- Root: E:\Projects\ULP_Project
- Venv: E:\Projects\ULP_Project\venv
- Folder field points: data\raw\01_field_points dan data\gps\01_field_points
- Folder review YOLO: data\dataset_yolo\00_review_candidates
- Class order wajib:
  0 struktur_penyangga
  1 konduktor
  2 pohon_sono

Titik P/K/V adalah nama titik lapangan user, bukan urutan spasial. Jangan ubah P001/K001/V001 menjadi format lain. Titik dapat acak dan tidak semua titik punya konduktor.

Baca seluruh repo dan dokumen status yang ada. Jangan menghapus script lama. Tambahkan atau perbaiki sistem lanjutan yang bisa dikerjakan tanpa menunggu label final.

Kerjakan target berikut:
1. Audit struktur repo dan buat status.
2. Buat script import hasil makesense YOLO dengan default dry-run.
3. Buat validator YOLO labels untuk class 0/1/2.
4. Buat dataset builder train/val field_multiclass_v1.
5. Buat generator data.yaml dengan class order terkunci.
6. Buat training launcher YOLOv8 default dry-run.
7. Buat evaluator skeleton tanpa klaim metrik palsu.
8. Buat inference CLI yang aman jika model belum ada.
9. Buat Flask backend yang tetap jalan walau model belum tersedia.
10. Buat Folium map dari GPS field points.
11. Buat export spreadsheet lokal CSV/XLSX.
12. Buat skeleton environmental risk model tanpa angka asumsi.
13. Buat docs runbook dan progress finalisasi.
14. Buat pytest minimal untuk path, class order, label format, splitter, GPS linker.

Jangan menjalankan training final sampai label makesense selesai dan validator PASS. Jangan mengambil dataset_botol. Jangan menyentuh data labeling aktif. Semua script yang berpotensi mengubah file harus punya --mode dry-run dan mode eksekusi eksplisit.

Setelah selesai, tampilkan:
- file yang dibuat/diubah
- command smoke test
- status tiap modul
- apa yang masih WAITING_FOR_LABELS
- apa yang harus dijalankan user setelah export YOLO dari makesense.ai
```

---

## 22. Command Awal untuk User Sebelum Menjalankan Codex

Jalankan di PowerShell:

```powershell
Set-Location E:\Projects\ULP_Project
git status
git checkout -b system-finalization-no-label-touch
```

Jika branch sudah ada:

```powershell
git checkout system-finalization-no-label-touch
```

Setelah Codex selesai:

```powershell
git status
python -m pytest tests
```

---

## 23. Command Setelah User Selesai Labeling di makesense.ai

Nanti, setelah export YOLO dari makesense.ai selesai, jalankan:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\Activate.ps1

python scripts\import_makesense_yolo.py --point V001_pohon_sono --export-dir E:\Exports\makesense_v001_yolo --mode dry-run
python scripts\import_makesense_yolo.py --point V001_pohon_sono --export-dir E:\Exports\makesense_v001_yolo --mode copy

python scripts\validate_yolo_labels.py --point V001_pohon_sono

python scripts\build_field_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
python scripts\build_field_dataset.py --mode build --val-ratio 0.2 --seed 23050874166

python scripts\generate_data_yaml.py

python scripts\train_yolov8_field.py --mode dry-run
```

Training final hanya dijalankan jika validator PASS.

---

## 24. Prompt Deep Research Nanti

Deep Research **bukan untuk sekarang**. Gunakan nanti setelah sistem dasar siap.

```text
Lakukan riset mendalam berbasis sumber resmi dan literatur untuk membangun variabel environmental risk model pada proyek monitoring vegetasi jaringan distribusi PT PLN UP3 Surabaya Utara ULP Perak.

Fokus lokasi: Surabaya Utara / ULP Perak / Kota Surabaya.
Fokus objek: pohon sono, struktur penyangga, konduktor jaringan distribusi.
Cari data dan literatur dari:
- BPS
- BMKG
- KLHK
- data.go.id
- OpenStreetMap
- dokumen PLN terkait inspeksi vegetasi / right of way / pemeliharaan jaringan
- jurnal atau publikasi tentang pertumbuhan pohon sono, pengaruh pH tanah, curah hujan, musim, kelembaban, suhu, dan risiko terhadap jaringan listrik.

Output yang diminta:
1. daftar variabel lingkungan yang realistis
2. sumber data resmi
3. cara pengambilan data
4. rentang nilai jika tersedia
5. keterbatasan data
6. bagaimana variabel itu masuk ke scoring risiko vegetasi
7. format CSV/YAML yang bisa dipakai sistem Python
8. semua klaim harus punya sitasi
```

---

## 25. Prinsip Utama

Sistem boleh maju paralel, tetapi tidak boleh berpura-pura bahwa label sudah selesai.

Kalimat kerja yang benar:

```text
READY_FOR_LABEL_HANDOFF
WAITING_FOR_LABELS
DRY_RUN_READY
MODEL_NOT_READY
DATA_SOURCE_PENDING_DEEP_RESEARCH
```

Kalimat yang salah:

```text
Training selesai
Akurasi tinggi
Model sudah final
Dataset sudah lengkap
Label sudah benar semua
```

Gunakan data nyata, validasi nyata, dan status jujur.

---

## 26. Acceptance Criteria

Codex dianggap berhasil jika:

```text
1. Tidak ada file labeling yang berubah tanpa izin.
2. dataset_botol tidak disentuh.
3. Script import makesense tersedia dan default dry-run.
4. Validator YOLO tersedia.
5. Dataset builder tersedia.
6. data.yaml generator tersedia.
7. Training launcher tersedia dan default dry-run.
8. Flask app bisa jalan walau model belum ada.
9. Folium map generator tersedia.
10. Spreadsheet export lokal tersedia.
11. Environmental risk skeleton tersedia tanpa angka palsu.
12. Test minimal tersedia.
13. Runbook tersedia.
14. Status WAITING_FOR_LABELS jelas.
```

---

## 27. Penutup untuk Codex

Kerjakan sistem lanjutan yang bisa dikerjakan sekarang. Jangan menyentuh labeling aktif. Jangan membuat klaim hasil model sebelum label, training, dan evaluasi benar-benar selesai. Fokus pada pipeline yang siap menerima hasil makesense.ai.
