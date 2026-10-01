# Sistem Monitoring Vegetasi

Sistem Monitoring Vegetasi memantau Angsana di sekitar jaringan SUTM 20 kV 3 fasa melalui OpenCV, YOLOv8, ByteTrack, calibrated geometry, dan prediksi berbasis evidence. Realtime mengirim metadata sebagai JSON dan menggambar overlay pada canvas browser. Flask menyediakan operator flow di `/vegetation` dan API di `/api/vegetation`.

## Runtime

- `models/detector.pt` adalah path model segmentasi produksi untuk `angsana`, `konduktor`, dan `struktur_penyangga_sutm`, setelah evaluasi data lokal diterima.
- `models/yolov8n.pt` dipakai sebagai baseline inference bila detector produksi belum tersedia dan weight baseline tersedia lokal. Class COCO tidak diperlakukan sebagai deteksi pohon produksi; tanpa weight, statusnya `model_not_ready`.
- Tracking memakai ByteTrack melalui Ultralytics. Jika tracking gagal, frame tetap diproses dengan deteksi YOLO biasa.
- Prediksi memerlukan geometry yang andal, threshold jaringan yang compatible, dan evidence laju perubahan clearance untuk estimasi waktu. Kekurangan input atau evidence menghasilkan status eksplisit dan tidak menghentikan deteksi.
- External generative AI tidak diinisialisasi dan tetap disabled.

## Setup dan development

```powershell
Set-Location E:\Projects\Vegetation_Monitoring
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\run_server.py --dev
```

Buka `http://127.0.0.1:5000/vegetation`. Akses kamera browser memerlukan `localhost` atau HTTPS.

Weight di `models/` tidak masuk Git. Sediakan pretrained `yolov8n.pt` dari sumber Ultralytics tepercaya untuk baseline; training memerlukan `yolov8m-seg.pt`. Instalasi dependency tidak menyediakan weight. `detector.pt` dan trained growth predictor belum tersedia.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Production start

Isi environment dari `.env.example` pada runtime host, lalu jalankan satu application process:

```powershell
.\.venv\Scripts\python.exe scripts\run_server.py --host 0.0.0.0 --port 5000
```

Command tersebut menggunakan Waitress. Endpoint health/readiness aplikasi adalah `/api/vegetation/status`; response-nya juga menyatakan apakah detector produksi siap. TLS dapat diterminasi oleh reverse proxy platform deployment.

Endpoint realtime menerima satu frame JPEG/PNG per request di `/api/vegetation/realtime/frame`. Endpoint `/api/vegetation/prediction` menyediakan contract prediksi yang sama untuk enrichment server tanpa memanggil provider eksternal.

## Data dan model

```text
data/
  dataset/
    data.yaml
    acquisition_manifest.csv
    images/train
    images/val
    images/test
    labels/train
    labels/val
    labels/test
  raw/         media sumber yang tidak masuk Git
  reference/   reference geometri, jaringan, dan sumber evidence
  prediction/ evidence pertumbuhan dan clearance
  runtime/     session, hasil, dan records
models/        weight detector lokal
```

Production inference hanya memerlukan dependency runtime, model, dan reference yang dipakai; dataset training tidak diperlukan.

## Training detector

`data/dataset/data.yaml` adalah satu konfigurasi canonical dengan urutan class `0: angsana`, `1: konduktor`, `2: struktur_penyangga_sutm`. Annotation memakai polygon YOLO segmentation normalized:

```text
class_id x1 y1 x2 y2 ... xn yn
```

Setiap polygon memiliki sedikitnya tiga titik. Metadata acquisition pada `acquisition_manifest.csv` mempertahankan sumber, URL atau dataset identifier, lisensi, provider/author, tanggal acquisition, class asli, dan mapped class. Data eksternal hanya digunakan jika lisensinya compatible; held-out `val` dan `test` harus memakai kamera ground-level Surabaya dan dipisahkan per capture session/lokasi untuk mencegah leakage.

Setelah image dan label segmentasi yang sudah direview tersedia, jalankan:

```powershell
.\.venv\Scripts\python.exe scripts\train_detector.py
```

Training menggunakan pretrained `YOLOv8m-seg`, menyimpan satu output di `runs/detector`, dan mengevaluasi `best.pt` pada held-out `test`. Evaluasi melaporkan mask precision, recall, mAP50, dan mAP50-95 beserta hasil per class. Script tidak mempromosikan weight otomatis: salinan ke `models/detector.pt` hanya dilakukan setelah hasil numerik dan visual data lokal diterima secara eksplisit. Dataset saat ini belum memiliki image dan polygon yang siap training.

## Geometry dan evidence

Geometry sudah memakai mask Angsana dan konduktor, camera calibration (`fx`, `fy`, `cx`, `cy`, distortion coefficients), serta capture distance 10 meter ke pangkal pohon. Struktur penyangga dapat menjadi cross-check bila spesifikasi dan pemasangannya diketahui. Hasil merupakan pendekatan planar dari satu kamera, disertai confidence dan uncertainty; orientasi kamera, visibility pangkal pohon, dan kesesuaian kedalaman harus terkonfirmasi.

Threshold mengikuti jenis jaringan dan jenis pengukuran dalam konfigurasi lokal. Referensi SUTM 20 kV yang memerlukan penerimaan kebijakan lokal tidak aktif otomatis; threshold vertikal jaringan transmisi tidak berlaku untuk nearest clearance. Risk bands memerlukan action dan monitor threshold yang diterima beserta sumbernya.

Prediksi waktu menuju action threshold sudah tersedia. Urutan evidence adalah pengamatan berulang yang compatible, predictor yang diterima bila tersedia, lalu literature prior yang compatible dengan species dan tahap pertumbuhan. DBH, pertumbuhan tinggi, dan cuaca tidak diubah menjadi laju pemanjangan tajuk tanpa evidence. Tanpa calibration, threshold, atau laju yang memadai, hasil tetap seperti `uncalibrated_device`, `threshold_not_configured`, atau `insufficient_growth_reference`, bukan estimasi buatan. Training predictor memerlukan pengamatan longitudinal terverifikasi, evaluasi pada kelompok terpisah, dan penerimaan eksplisit sebelum promotion.
