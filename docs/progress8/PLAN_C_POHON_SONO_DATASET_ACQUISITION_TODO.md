# Plan C Pohon Sono Dataset Acquisition TODO

Dokumen ini hanya daftar kebutuhan akuisisi data legal. Tidak ada image internet yang dimasukkan otomatis ke dataset training.

## Kebutuhan Data

- Foto pohon sono/angsana di area jaringan distribusi 20 kV.
- Foto pohon non-sono yang sering muncul di area lapangan sebagai negative species comparison.
- Foto konduktor udara dengan variasi jarak, sudut, dan pencahayaan.
- Foto struktur penyangga: tiang, crossarm, bracket, dan struktur jaringan relevan.
- Foto negative object untuk validasi filter: manusia, kendaraan, dinding, atap, lampu, jendela, dan furniture.

## Syarat Sumber

- Sumber harus legal dan dapat diverifikasi.
- Izin penggunaan dataset harus jelas.
- Metadata sumber harus dicatat sebelum image dipakai.
- Dataset internet tidak boleh langsung menjadi dataset resmi tanpa review manual.

## Alur Aman

1. Kumpulkan kandidat sumber legal.
2. Catat metadata sumber dan izin.
3. Review manual kualitas dan relevansi.
4. Label dengan class order Plan C.
5. Jalankan `scripts/plan_c_yolo_dataset_gate.py`.
6. Training hanya dijalankan setelah gate menyatakan data ready.

## Batasan

Runtime `/plan-c` tidak bergantung pada proses training ini. Sistem field trial tetap berjalan dengan detection adapter, geometry, growth proxy, dan review operator.
