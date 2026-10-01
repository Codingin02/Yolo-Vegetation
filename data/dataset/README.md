# Canonical Segmentation Dataset

Dataset ini adalah satu-satunya dataset segmentasi untuk target produksi
`YOLOv8m-seg` pada jaringan SUTM 20 kV 3 fasa. Status saat ini hanya struktur, aturan label, dan manifest
sumber; belum ada gambar atau label yang dinyatakan siap training. Selama
model segmentasi belum diterima, aplikasi memakai baseline
`models/yolov8n.pt` jika tersedia lokal. Weight tidak masuk Git; baseline bukan
detector produksi dan `models/detector.pt` belum tersedia.

## Class map

Class map tidak boleh diperluas pada tahap ini:

```text
0: angsana
1: konduktor
2: struktur_penyangga_sutm
```

`angsana` berarti `Pterocarpus indicus`. Semua label harus berupa polygon
YOLO segmentation, bukan bounding box saja:

```text
<class_id> <x1> <y1> <x2> <y2> ... <xn> <yn>
```

Koordinat harus ternormalisasi ke `[0, 1]`, memiliki sedikitnya tiga titik,
dan mengikuti pasangan `(x, y)`.

## Aturan polygon

- `angsana`: label satu instance pohon dengan silhouette bagian pohon yang
  benar-benar terlihat di atas tanah, termasuk batang, cabang, dan tajuk yang
  dapat diatribusikan ke pohon tersebut. Jangan menebak bagian yang tertutup,
  dan jangan memasukkan tanah, bayangan, langit, atau vegetasi lain.
- `konduktor`: label setiap konduktor fisik sebagai instance terpisah dengan
  polygon sempit yang mengikuti ketebalan dan lintasan piksel yang benar-benar
  terlihat. Jangan menggabungkan kabel paralel dan jangan membuat polygon lebar
  berisi langit kosong. Lewati objek yang tidak dapat ditinjau dengan yakin.
- `struktur_penyangga_sutm`: label silhouette struktur penyangga SUTM yang
  terlihat sebagai instance terpisah. Jangan memasukkan konduktor atau area
  langit di sekitarnya, dan jangan menebak bagian yang tertanam atau tertutup.
- Occlusion dan clipping hanya menutup piksel yang terlihat. Polygon tidak
  boleh diperpanjang secara imajinatif ke luar frame atau di balik objek lain.
- Polygon hasil konversi dari polyline eksternal wajib ditinjau manusia;
  ketebalan tidak boleh ditentukan dengan konstanta yang mengubah geometri
  secara sewenang-wenang.

SAM2 boleh dipakai hanya sebagai asisten anotasi. Mask yang dihasilkan SAM2
belum menjadi ground truth sampai ditinjau dan disetujui manusia. SAM2 tidak
menjadi dependency runtime atau production.

## Struktur dan split

```text
data/dataset/
  data.yaml
  acquisition_manifest.csv
  images/{train,val,test}/
  labels/{train,val,test}/
```

- Split dilakukan menurut `capture_session_id` dan `scene_id`; frame dari
  sesi atau scene yang sama tidak boleh tersebar ke split berbeda.
- Data eksternal hanya boleh masuk `train` dan tetap berstatus supplemental.
- `val` dan `test` harus berupa foto lokal ground-level dari Surabaya Utara,
  Surabaya Timur, atau Surabaya Barat yang cocok dengan kamera aplikasi.
- Sidoarjo tidak termasuk scope.
- Frame video harus dijarakkan secara temporal dan diperiksa terhadap near
  duplicate sebelum split.

Baris source-level awal dalam `acquisition_manifest.csv` hanya kandidat riset:
`image_path` kosong dan `download_status=not_downloaded`. Setiap gambar yang
kelak dimasukkan harus memiliki tepat satu baris asset-level dengan provenance,
hak penggunaan, session/scene, split, review manusia, dan SHA-256 lengkap.
Asset baru siap training hanya jika `annotation_type=yolo_segmentation`,
`rights_status=approved`, `download_status=downloaded`, dan
`human_review_status=approved`.

## Quality gate

Sebelum training, pastikan pasangan image/label lengkap, class hanya `0`, `1`,
atau `2`, semua polygon valid, attribution tersimpan di manifest, dan tidak ada
session/scene yang bocor antar-split. Model tidak boleh dipromosikan ke
`models/detector.pt` sebelum evaluasi mask dan inspeksi visual pada held-out
local test diterima secara eksplisit. `scripts/train_detector.py` melaporkan
hasil evaluasi dan path `best.pt` tanpa promotion otomatis.
