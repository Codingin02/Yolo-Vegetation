# Legacy Scripts Audit

Audit ini mengklasifikasikan script lama yang masih untracked di `scripts/`. Tidak ada script lama yang dihapus, di-rename, atau otomatis distage pada Phase 2.

## Ringkasan Kategori

| File | Kategori | Alasan | Aksi Phase 2 |
|---|---|---|---|
| `scripts/auto_capture.py` | DO_NOT_STAGE_DATA_TOUCHING | Menulis gambar kamera langsung ke `dataset_botol/images/train`. | Jangan stage; hanya referensi sejarah Progress 1-3. |
| `scripts/check_env.py` | KEEP_AS_SOURCE_CANDIDATE | Audit environment dan package; tidak menulis data project, tetapi membuka cek kamera. | Jangan stage otomatis; bisa dibuat versi audit aman nanti. |
| `scripts/extract_video_frames.py` | DO_NOT_STAGE_DATA_TOUCHING | Mode `extract` menulis ke `data/processed/frames` dan manifest CSV. | Jangan stage; logika dapat direwrite menjadi tool dry-run yang lebih ketat jika dibutuhkan. |
| `scripts/patch_labelimg_qt_float_bug.py` | KEEP_AS_LEGACY_REFERENCE | Memodifikasi package LabelImg di venv; LabelImg bukan jalur utama sekarang. | Jangan stage; simpan sebagai referensi lama saja. |
| `scripts/prepare_v001_review_set.py` | DO_NOT_STAGE_DATA_TOUCHING | Mode `copy` menulis ke `data/dataset_yolo/00_review_candidates` dan `classes.txt`. | Jangan stage; folder labeling sedang aktif. |
| `scripts/sort_field_data.py` | DO_NOT_STAGE_DATA_TOUCHING | Mode `copy/move` menyentuh `data/raw` dan `data/gps`, serta menulis metadata. | Jangan stage; hanya referensi alur sorting lama. |
| `scripts/sort_field_data_old_buggy.py` | KEEP_AS_LEGACY_REFERENCE | Versi lama/buggy dari sorter; menyentuh raw/GPS jika dijalankan. | Jangan stage; jangan hapus tanpa konfirmasi user. |
| `scripts/tempCodeRunnerFile.py` | SAFE_TO_REWRITE_LATER | File sementara editor, bukan source final. | Jangan stage; hapus hanya dengan konfirmasi user. |
| `scripts/test_flask_ngrok.py` | KEEP_AS_LEGACY_REFERENCE | Membuka ngrok dan public tunnel; tidak cocok untuk scaffold lokal aman. | Jangan stage; scaffold Flask lokal sudah dibuat di `src/ulp_project/web/app.py`. |
| `scripts/test_folium_map.py` | KEEP_AS_LEGACY_REFERENCE | Membuat peta uji di `results/test_map.html` dengan koordinat placeholder. | Jangan stage; Phase 2 memakai `scripts/build_field_map.py`. |
| `scripts/test_yolo.py` | KEEP_AS_LEGACY_REFERENCE | Menjalankan model YOLO kamera dengan `yolov8n.pt`. | Jangan stage; bukan training/inference final field dataset. |
| `scripts/tracking_count_horizontal.py` | KEEP_AS_LEGACY_REFERENCE | Tracking kamera COCO/person, bukan dataset PLN final. | Jangan stage; referensi teknis lama. |
| `scripts/tracking_count_vertical.py` | KEEP_AS_LEGACY_REFERENCE | Tracking kamera COCO/person, bukan dataset PLN final. | Jangan stage; referensi teknis lama. |
| `scripts/uji_stability.py` | KEEP_AS_LEGACY_REFERENCE | Uji kamera/tracking COCO/person. | Jangan stage; referensi stabilizer lama. |

## Kebijakan

- `DELETE_NOT_ALLOWED_WITHOUT_USER_CONFIRMATION`: berlaku untuk semua file di atas.
- Script yang menyentuh `data/raw`, `data/gps`, `data/processed`, `data/dataset_yolo/00_review_candidates`, `dataset_botol`, atau `results` tidak boleh dijalankan dalam Phase 2.
- Jika logika lama masih berguna, pindahkan konsepnya ke script baru yang default-nya dry-run dan tidak menyentuh folder labeling.
