# Phase 6 Mobile Field Runtime and Environmental Risk

Phase 6 menyiapkan sistem lapangan tanpa menyentuh labeling. Operator masih bekerja di makesense.ai, sehingga sistem hanya menerima input runtime, membaca status, dan mengembalikan hasil jujur seperti `MODEL_NOT_READY`.

## Fitur Siap

- Halaman HP: `/mobile`
- Upload inspeksi: `/api/mobile/upload-inspection`
- Cek job: `/api/mobile/job/<job_id>`
- Cek hasil: `/api/mobile/result/<job_id>`
- Status jaringan: `/api/mobile/network/status`
- Ping latensi: `/api/latency/ping`
- Risk skeleton pohon_sono berbasis input eksplisit.
- Template input lingkungan manual.

## Alur Lapangan

1. HP operator membuka dashboard Flask dari laptop.
2. HP memilih foto, mengambil GPS browser, mengisi `point_id`, lalu upload.
3. Laptop menyimpan job ke `data/runtime/`, folder ini di-ignore Git.
4. Jika model belum ada, hasil tetap dibuat dengan status `MODEL_NOT_READY_DRY_RESULT`.
5. Risk engine memberi output rule-based jika input cukup, atau `ENVIRONMENTAL_DATA_NOT_READY` jika belum cukup.

## Status Jujur

Sistem ini belum mengklaim akurasi prediksi. Akurasi akhir tetap menunggu:

- label YOLO selesai,
- validasi label PASS,
- dataset final dibangun,
- training YOLO dengan izin operator,
- data lingkungan/GPS nyata,
- validasi ground truth lapangan.

## Larangan Tetap

- Jangan import label mode copy sebelum export makesense siap.
- Jangan build dataset final sebelum validator PASS.
- Jangan training aktual.
- Jangan memakai `dataset_botol` sebagai dataset utama.
- Jangan membuat angka akurasi, label, atau model palsu.
