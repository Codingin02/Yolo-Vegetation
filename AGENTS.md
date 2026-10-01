# Vegetation_Monitoring

Canonical project: `E:\Projects\Vegetation_Monitoring`

Product: Sistem Monitoring Vegetasi

## Engineering Style

- Gunakan prinsip Ponytail.
- Prioritas: correctness > simplicity > maintainability > performance > feature count.
- Gunakan satu canonical implementation dan jangan overengineering.
- Jangan membuat abstraction, manager, provider, service layer, adapter, factory, validator, atau wrapper jika implementasi langsung yang kecil sudah cukup.
- Reuse file dan dependency yang sudah ada bila sehat.
- Komentar hanya untuk constraint, formula, unit, security issue, atau workaround yang tidak obvious.
- Jangan menulis tutorial comment atau development diary di source code.

## Product Scope

Kemampuan utama:

1. deteksi pohon realtime menggunakan OpenCV, YOLOv8, dan ByteTrack melalui Ultralytics;
2. prediksi waktu menuju pemangkasan menggunakan data yang dapat dipertanggungjawabkan.

Core runtime:

- Python
- Flask
- OpenCV
- YOLOv8
- ByteTrack melalui Ultralytics
- prediction logic

Canonical web route: `/vegetation`

Canonical API root: `/api/vegetation`

Canonical production detector: `models/detector.pt`

Deployment model dapat diekspor ke ONNX tanpa membuat pipeline kedua.

## Vision Classes

Canonical segmentation classes for SUTM 20 kV, 3 fasa:

- `0: angsana`
- `1: konduktor`
- `2: struktur_penyangga_sutm`

Scientific metadata:

- `angsana = Pterocarpus indicus`

Jangan gunakan `pohon_sono` sebagai canonical production class.

Species baru harus memperluas dataset, biology data, dan detector yang sama, bukan membuat sistem atau model paralel.

## Geographic Dataset Scope

Dataset lapangan difokuskan pada Surabaya Utara, Surabaya Timur, dan Surabaya Barat. Surabaya Selatan yang terlalu dekat atau beririsan dengan arah Sidoarjo tidak masuk acquisition scope.

Acquisition mencakup Angsana, konduktor, dan struktur penyangga SUTM. Species lain tidak masuk class map produksi.

Jangan mengarang persentase populasi wilayah tanpa census yang memadai.

## Prediction Integrity

- Jangan membuat data biologis, growth rate, climate value, training label, atau prediction accuracy palsu.
- Jangan menganggap DBH increment sama dengan branch-extension rate.
- Jangan menggunakan satu growth rate universal untuk semua species atau tahap pertumbuhan.
- Local repeated observations mempunyai prioritas tertinggi.
- Literature prior hanya fallback ketika compatible.
- Jika evidence tidak cukup, hasil yang benar adalah `insufficient_growth_reference`.
- Month, temperature, humidity, dan rainfall boleh menjadi context atau data feature, tetapi multiplier atau coefficient biologis harus didukung data.
- Jangan menggunakan generic `0.50 m/quarter` sebagai universal growth constant.

## Scope Lock

Jangan menambah atau mengaktifkan kembali tanpa instruksi eksplisit:

- GPS, Google Maps, maps, atau Google Sheets;
- Gemini, Groq, OpenRouter, atau external generative AI;
- MQTT atau Digital Twin integration;
- multi-agent runtime;
- database tambahan;
- monocular distance estimation;
- microservices.

External AI tetap disabled.

Gunakan OpenCV secara sederhana untuk decode, resize bila perlu, image handling, dan annotation.

Realtime menggunakan satu detector dan pipeline canonical. Tracking hanya menstabilkan identity; kegagalannya tidak boleh menghentikan deteksi YOLO.

## Validation Discipline

- Jangan audit repository berulang kali atau memvalidasi ulang komponen yang belum berubah.
- Jangan melakukan validation setelah setiap langkah kecil.
- Lakukan satu coherent validation pada jalur yang berubah; ulangi hanya untuk memperbaiki error nyata.
- Jangan membuat validator, gate, checker, atau framework validation baru untuk membuktikan pekerjaan sendiri.
- Gunakan canonical tests yang sudah ada.

## Git

- Jangan membuat branch otomatis.
- Jangan commit kecuali diminta eksplisit oleh user.
- Jangan push atau force push.
- Jangan rebase, merge, cherry-pick, amend, atau rewrite history tanpa instruksi eksplisit.
- Jangan gunakan `git add .` atau `git add -A` secara otomatis.
- Pertahankan perubahan user yang sudah ada.
