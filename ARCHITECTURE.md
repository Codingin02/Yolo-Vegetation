# Arsitektur Sistem Monitoring Vegetasi

## Realtime flow

```text
browser camera
  -> JPEG frame
  -> canonical Flask application on the edge host
  -> OpenCV decode
  -> YOLOv8 segmentation + ByteTrack identity
  -> calibrated geometry + compatible network thresholds
  -> evidence-backed prediction per detected tree
  -> detection metadata JSON
  -> geometry and status on the browser canvas
```

`app.py` membuat satu Flask application. `routes.py` mengekspos `/vegetation` dan `/api/vegetation`. `pipeline.py` adalah jalur detector dan prediction canonical untuk realtime maupun snapshot. Realtime tidak mengirim annotated JPEG; renderer tetap digunakan saat hasil tersimpan memang memerlukan image annotation.

## Detection and tracking

`detection.py` memuat satu model Ultralytics. Runtime memprioritaskan `models/detector.pt` dan hanya memakai `models/yolov8n.pt` sebagai baseline COCO bila weight produksi belum tersedia. Realtime menjalankan `YOLO.track(..., tracker="bytetrack.yaml", persist=True)`; kegagalan tracking turun ke `YOLO.predict` pada model yang sama. Missing model atau inference error menghasilkan status eksplisit tanpa fabricated detection.

Target model produksi adalah `YOLOv8m-seg` dengan class `0: angsana`, `1: konduktor`, dan `2: struktur_penyangga_sutm` untuk jaringan SUTM 20 kV 3 fasa. Metadata Angsana adalah `Pterocarpus indicus`. Baseline `models/yolov8n.pt` dipakai bila tersedia lokal sampai `models/detector.pt` diterima dan dipromosikan. Weight tidak masuk Git; detector produksi dan trained growth predictor belum tersedia. Data yang species-nya belum terverifikasi tidak boleh menjadi label Angsana.

## Segmentation dataset and training

`data/dataset` adalah satu dataset canonical dengan split `train`, `val`, dan `test`. Label memakai polygon YOLO segmentation; mask mengikuti bagian pohon, masing-masing konduktor, dan struktur penyangga yang terlihat tanpa area kosong berlebihan. Mask bantuan SAM/SAM2 harus direview manusia dan SAM tidak menjadi runtime dependency.

Manifest acquisition mempertahankan provenance dan lisensi setiap sumber. Data lokal Surabaya Utara, Timur, dan Barat adalah authoritative; data eksternal yang license-compatible hanya supplemental. Held-out validation/test memakai scene ground-level lokal dan split berdasarkan capture session/lokasi.

`scripts/train_detector.py` menggunakan satu pretrained `YOLOv8m-seg` dan mengevaluasi mask precision, recall, mAP50, mAP50-95, serta hasil per class. Training tidak berjalan tanpa polygon dataset yang nyata, dan weight tidak dipromosikan ke `models/detector.pt` sebelum evaluasi numerik serta visual diterima.

## Prediction

`growth.py` menyediakan satu contract non-blocking untuk edge overlay dan endpoint `/api/vegetation/prediction`. Status operasional memerlukan geometry dari server dengan confidence yang memadai dan action threshold yang compatible dari konfigurasi lokal. Clearance pada atau di bawah threshold menghasilkan `TEBANG`; clearance di atasnya memerlukan evidence laju positif untuk menghasilkan `PANTAU` dengan estimasi hari menuju threshold. Kekurangan input atau evidence tidak menghentikan deteksi.

`predictor.py` menangani evidence dan estimasi laju. Pengamatan berulang untuk pohon, konduktor, dan tahap pertumbuhan yang sama didahulukan, lalu predictor yang telah diterima bila tersedia, lalu prior yang compatible. Target adalah penutupan clearance atau pemanjangan tajuk yang terverifikasi menuju konduktor; DBH dan pertumbuhan tinggi bukan penggantinya. Estimasi hari memakai `(clearance - action_threshold) / rate`, dengan uncertainty pengukuran terpisah dari uncertainty laju.

Training membandingkan `HistGradientBoostingRegressor` dan `MLP` pada kelompok pengamatan terpisah. Model dipilih pada validation dan dievaluasi pada held-out test; promotion ke `models/growth_predictor.pkl` memerlukan penerimaan eksplisit. Tanpa data longitudinal yang memadai, trained predictor tidak dibuat dan runtime dapat mengembalikan `insufficient_growth_reference`.

## Geometry and evidence boundary

`geometry.py` menghitung geometry dari mask, camera calibration (`fx`, `fy`, `cx`, `cy`, distortion coefficients), dan capture distance 10 meter ke pangkal pohon. Tinggi, ukuran tajuk, serta nearest clearance menggunakan pendekatan planar terkalibrasi. Struktur penyangga dapat menjadi cross-check ketika spesifikasi, pemasangan, dan visibility-nya memadai. Visibility pangkal pohon, orientasi kamera, hubungan kedalaman, dan uncertainty calibration memengaruhi confidence; tidak ada universal pixel-to-meter constant atau klaim rekonstruksi 3D.

Calibration dan kebijakan jaringan berasal dari `data/reference/camera_calibration.json` lokal. Threshold dicocokkan terhadap jaringan, tegangan, dan measurement basis pada `data/reference/electrical_clearance.csv`. Kandidat SUTM 20 kV memerlukan penerimaan kebijakan lokal; threshold vertikal transmisi tidak dapat menggantikan nearest clearance. Risk bands memerlukan action dan monitor threshold beserta sumber yang diterima. Input upload tidak dapat mengesahkan status operasional.

`data/prediction/prediction_evidence.csv` menyimpan evidence dengan provenance. Weather dan biology hanya digunakan sesuai dukungan datanya; nilai kosong dan coefficient biologis tidak dibuat-buat. Calibration, detector, atau evidence yang belum tersedia menghasilkan status eksplisit seperti `uncalibrated_device`, `model_not_ready`, atau `insufficient_growth_reference`.

## Edge and cloud boundary

Application dijalankan dekat kamera untuk frame handling, YOLO, tracking, dan overlay. Flask yang sama dapat melayani web dan enrichment prediction di deployment server; tidak ada provider AI eksternal, broker, atau microservice. Hanya frame dan input prediksi yang memang diperlukan yang melewati API.

## Storage and deployment

Snapshot yang disimpan menghasilkan `original.jpg`, `annotated.jpg`, `metadata.json`, `detections.json`, `growth.json`, dan `result.json` di `data/runtime`. Realtime frame tidak ditulis setiap request. Production memakai satu Waitress application process; health/readiness tersedia di `/api/vegetation/status`. Training terpisah dan dataset tidak diperlukan untuk production inference.
