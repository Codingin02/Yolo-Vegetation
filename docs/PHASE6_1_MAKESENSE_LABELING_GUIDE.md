# Phase 6.1 MakeSense Labeling Guide

1. Buka `https://www.makesense.ai/`.
2. Klik `Get Started`.
3. Upload gambar kandidat dari folder review lokal.
4. Pilih `Object Detection`.
5. Masukkan class sesuai urutan:
   ```text
   struktur_penyangga
   konduktor
   pohon_sono
   ```
6. Buat bounding box rapat pada objek.
7. Jangan membuat bbox asal untuk objek yang tidak jelas.
8. Jangan membuat label palsu atau label otomatis sebagai ground truth.
9. Export annotations.
10. Pilih format YOLO.
11. Simpan hasil export ke:
    ```text
    data/dataset_yolo/01_makesense_export/
    ```
12. Jalankan validator:
    ```powershell
    .\venv\Scripts\python.exe scripts\progress6_1_label_export_validator.py --write-reports
    ```

Label ragu harus masuk review, bukan dipaksakan menjadi ground truth.
