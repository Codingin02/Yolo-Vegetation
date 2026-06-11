# Plan C Roboflow Review Steps Priority

## Setup Project

1. Buka Roboflow.
2. Buat project baru dengan tipe `Object Detection`.
3. Upload package dari:

```text
data/runtime/plan_c_dataset_acquisition/roboflow_package/
```

4. Pastikan class order:

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono
```

Jangan share Roboflow API key dan jangan commit key ke repo.

## Review Pohon Sono Dulu

- Review `pohon_sono` lebih dulu.
- Hapus bbox yang salah.
- Jika pohon terlihat tetapi bukan Angsana/Pterocarpus indicus atau tidak yakin, ubah label menjadi `pohon_non_sono`.
- Bbox mengikuti pohon target yang terlihat, bukan seluruh background.

## Review Konduktor

- Jika ada 3 kabel, buat 3 bbox `konduktor`.
- Jika lebih dari 3 kabel, bbox tiap kabel yang terlihat.
- Jangan membuat satu bbox lebar untuk semua kabel jika tiap kabel bisa dipisahkan.
- Jangan label tepi atap, bayangan, pagar, atau kabel indoor sebagai konduktor.

## Review Struktur Penyangga

- Bbox hanya untuk tiang listrik, crossarm, bracket, atau struktur listrik relevan.
- Jangan label tiang lampu, pipa, pagar, dinding, kusen, atau objek indoor sebagai `struktur_penyangga`.

## Negative Sample

- Jika tidak ada target, biarkan tanpa label.
- Negative sample membantu filter false positive seperti manusia, wajah, mobil, tembok, ruangan, atap, dan kabel kecil indoor.

## Export

1. Setelah review selesai, generate version.
2. Export format YOLOv8.
3. Simpan zip export ke:

```text
data/external_dataset_inbox/roboflow_yolov8_export/
```

4. Jangan commit zip export.
5. Jalankan gate sebelum training:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_priority_dataset_gate.py
```
