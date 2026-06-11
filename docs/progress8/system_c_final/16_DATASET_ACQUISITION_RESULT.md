# Dataset Acquisition Result

## Tujuan

Pipeline akuisisi System C disiapkan untuk memprioritaskan:

1. `pohon_sono` / Angsana / Pterocarpus indicus / Narra / Sonokembang
2. `konduktor` jaringan distribusi / overhead conductor / power line
3. `struktur_penyangga` / utility pole / concrete pole / crossarm
4. `pohon_non_sono` sebagai negative vegetation
5. non-target negative sample

## Source Registry

Registry berisi 25 sumber/adaptor, termasuk Wikimedia Commons, GBIF, iNaturalist, dan sumber legal manual yang wajib diverifikasi.

## Download

Download hanya berjalan jika user menjalankan:

```powershell
.\venv\Scripts\python.exe scripts\plan_c_system_c_run_all_dataset_pipeline.py --download
```

Pipeline mencatat source yang rate-limited atau gagal sebagai status terkontrol, bukan kandidat palsu.

## License Policy

Training hanya menerima CC0, Public Domain, CC BY, dan CC BY-SA dengan attribution.

Lisensi NC/restricted hanya masuk reference-only. Lisensi unknown, all rights reserved, Google Images langsung, dan metadata tidak jelas ditolak.

## Status Saat Ini

Dataset final belum boleh dianggap siap training sampai training gate menyatakan `YOLO_TRAINING_READY`.
