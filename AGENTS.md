# AGENTS.md — ULP Project Progress 8 / Plan C

Instruksi ini wajib dibaca Codex sebelum mengubah kode.

Folder kerja tunggal:
E:\Projects\ULP_Project

Branch kerja:
progress8-plan-c-snapshot-processing

## Keputusan Final

Progress 8 adalah Plan C.

Plan A = YOLO-only realtime. Simpan sebagai history riset. Jangan dihapus.  
Plan B = YOLO + AI realtime. Simpan sebagai history riset. Jangan dihapus.  
Plan C = snapshot/manual capture + backend processing. Ini jalur utama untuk laporan akhir magang riset.

Plan C tidak realtime. HP hanya menjadi kamera, GPS client, dan uploader foto. Laptop/Flask backend memproses foto setelah shutter.

## Larangan Mutlak

Jangan membuat folder project baru di luar E:\Projects\ULP_Project.  
Jangan memakai git worktree.  
Jangan menambal /field-camera lama.  
Jangan menghapus Plan A atau Plan B.  
Jangan memakai YOLO-FIRST.  
Jangan memakai AI realtime switch.  
Jangan membuat realtime detection loop.  
Jangan menyentuh data/raw, dataset, labels, runs, weights, models, file .pt, file .onnx, atau secret.  
Jangan membuat fake detection.  
Jangan membuat fake GPS.  
Jangan membuat fake bounding box.  
Jangan membuat fake prediction.  
Jangan menjalankan git add .  
Jangan commit API key.  
Jangan mengklaim akurasi absolut PLN.

## Definisi Sistem Plan C

Flow:
1. Operator membuka /plan-c.
2. Operator membaca instruksi.
3. Operator klik Get Started.
4. Browser meminta izin kamera dan GPS.
5. Operator berdiri dekat atau bawah pohon untuk mengambil tree anchor.
6. Operator mundur agar pohon, konduktor, dan struktur penyangga terlihat.
7. Operator menekan shutter.
8. Foto dikirim ke Flask backend.
9. Backend menyimpan original.jpg.
10. Backend menjalankan YOLO post-capture.
11. Backend menjalankan AI vision validator jika tersedia.
12. Backend menjalankan Python geometry.
13. Backend menjalankan growth prediction.
14. Backend membuat annotated.jpg, result.json, developer.json.
15. Backend append CSV, append JSONL, append map marker.
16. Result page menampilkan ringkasan risiko.

## Peran Teknologi

YOLO:
- deteksi objek setelah foto diambil,
- bounding box,
- class confidence,
- annotated image.

AI vision:
- validator visual tambahan,
- second opinion,
- narasi ringkas,
- rekomendasi ambil ulang foto jika objek tidak jelas.

Python geometry:
- sumber utama perhitungan,
- estimasi jarak,
- estimasi tinggi,
- clearance,
- risk status,
- prediksi kuartal.

AI tidak boleh menggantikan Python geometry.

## Objek Target

- pohon_sono
- konduktor
- struktur_penyangga

Objek lain seperti orang, mobil, keyboard, meja, tas, ruangan, laptop, dan dompet diabaikan untuk core result.

## Status Risiko

- AMAN
- PANTAU
- SIAGA
- PERLU_PEMANGKASAN
- DATA_TIDAK_CUKUP

## Prinsip UI

Capture page harus bersih:
- instruksi singkat,
- camera preview,
- shutter,
- retry,
- processing/loading.

Tidak boleh ada:
- YOLO-FIRST,
- AI realtime switch,
- lens selector custom,
- debug chips,
- MODEL_STATUS_UNKNOWN,
- realtime bounding overlay.

Developer page boleh menampilkan debug.
Frontend animasi 3D ditunda sampai core system stabil.
