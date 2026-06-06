# V001 Model Failure Analysis And Recovery

Dokumen ini mencatat status teknis V001_pohon_sono setelah label MakeSense diimpor, dataset YOLO dibangun, dan smoke training menghasilkan `best.pt`.

## Yang sudah benar

- Label V001 sudah diimpor dari MakeSense.
- Pasangan `images_selected` dan `labels_selected` valid secara file: 19 image, 19 label, missing label 0, orphan label 0, bad row 0.
- Dataset `field_multiclass_v1` sudah berhasil dibangun dengan split 15 train dan 4 val.
- `data.yaml` tersedia.
- Smoke training berjalan dan menghasilkan `runs/detect/field_multiclass_v1/weights/best.pt`.

## Yang gagal

- Prediksi normal pada `conf=0.25` tidak menghasilkan deteksi pada seluruh 19 image.
- Prediksi `conf=0.01` juga tidak menghasilkan deteksi dan tidak menyimpan label prediksi.
- Prediksi ultra-rendah `conf=0.001` menghasilkan ledakan false positive, sekitar ratusan box per image, sehingga overlay tidak terbaca.
- Output `conf=0.001` tidak boleh dianggap deteksi valid, tidak boleh menjadi bukti model berhasil, dan tidak boleh dipakai sebagai prediksi operator.

## Mengapa folder prediksi tampak seperti raw image

Jika YOLO tidak menemukan deteksi pada threshold normal, visual hasil prediksi akan tampak seperti gambar asli karena tidak ada bounding box yang digambar. Itu bukan masalah transfer file atau folder output; itu tanda model belum cukup kuat pada confidence operasional.

## Mengapa `conf=0.001` terlihat buruk

Threshold `0.001` membuat hampir semua kandidat lemah lolos filter. Akibatnya model mengeluarkan banyak box berconfidence sangat rendah, sering menyentuh batas `max_det`, dan label seperti `struktur_penyangga`, `konduktor`, atau `pohon_sono` muncul dengan confidence mendekati 0.00. Ini adalah diagnostik kegagalan, bukan mode prediksi.

## Mengapa multiclass V001 belum siap

Dataset V001 terlalu kecil dan tidak seimbang untuk runtime multiclass:

- `struktur_penyangga` hanya memiliki 1 instance total dan 0 instance di validation.
- `konduktor` punya label, tetapi bukti validation dan variasi data belum cukup untuk runtime yang reliable.
- `pohon_sono` memiliki 19 label dan menjadi satu-satunya target realistis untuk siklus training awal.

Kesimpulan: `field_multiclass_v1` valid secara teknis, tetapi belum reliable untuk multiclass runtime.

## Keputusan recovery

Recovery dilakukan dengan membuat dataset turunan `v001_pohon_sono_only_v1`:

- Semua 19 image V001 tetap dipakai.
- Hanya class asli `2 pohon_sono` yang dipertahankan.
- Class asli `2` diremap menjadi class baru `0`.
- `struktur_penyangga` dan `konduktor` didrop untuk siklus single-class ini.
- Dataset multiclass existing tidak dihapus, tidak dioverwrite, dan tetap menjadi artefak audit.

## Kebutuhan data berikutnya

Sebelum multiclass final, perlu pengumpulan dan pelabelan tambahan yang sengaja memisahkan target:

- Lebih banyak image `struktur_penyangga` dengan variasi jarak, sudut, pencahayaan, dan occlusion.
- Lebih banyak image `konduktor` dengan variasi bentang kabel dan background.
- Validation set yang berisi setiap class, bukan hanya train.

Tidak ada klaim akurasi final dari smoke training atau dataset 19 image. Status model harus tetap research/smoke sampai evaluasi validasi memadai.
