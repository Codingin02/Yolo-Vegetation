# PROGRESS 6.26 Dataset Expansion Plan

Status: planning-only, bukan training otomatis.

Prinsip:
1. Data lapangan user tetap prioritas utama.
2. Data internet hanya kandidat referensi, bukan ground-truth final.
3. Tidak ada gambar internet yang otomatis dicampur ke dataset training final.
4. Semua kandidat harus review manual sebelum menjadi label YOLO.
5. Tidak menyentuh data/raw, data/gps, data/dataset_yolo, runs, weights, models, dataset_botol.

Sumber kandidat:
- pohon_sono / angsana / sonokembang / Pterocarpus indicus:
  GBIF, iNaturalist, Wikimedia Commons.
- konduktor / utility line / power line:
  dataset umum hanya kandidat, wajib review karena tidak selalu konduktor distribusi PLN.
- struktur_penyangga / utility pole:
  dataset umum hanya kandidat, wajib disesuaikan dengan bentuk struktur PLN lapangan.
- Open Images:
  boleh sebagai kandidat class umum, bukan final otomatis.

Folder kandidat yang harus diabaikan Git:
data/external_candidate_sources/

Runtime 6.26 tidak melakukan download dataset dan tidak melakukan training.
