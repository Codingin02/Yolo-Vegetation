# AGENTS.md — ULP Project Progress 8 / Plan C

Dokumen ini adalah instruksi utama untuk Codex.

Project:
ULP_Project / Progress 8 / Plan C Snapshot Processing

Repository:
E:\Projects\ULP_Project

Worktree Progress 8:
E:\Projects\ULP_Project_PROGRESS8_PLAN_C_CONTEXT

Branch kerja:
progress8-plan-c-snapshot-processing

Branch dasar:
system-finalization-no-label-touch

Tujuan utama:
Membangun Plan C sebagai sistem final laporan akhir magang riset. Plan C memakai snapshot capture dari HP, backend processing di laptop, YOLO post-capture, AI vision validator, Python geometry engine, growth model, spreadsheet append-only, dan map marker append-only.

Definisi cabang:
Plan A = YOLO-only realtime. Simpan sebagai history riset. Jangan dihapus.
Plan B = YOLO + AI realtime. Simpan sebagai history riset. Jangan dihapus.
Plan C = snapshot/manual capture + backend processing. Ini jalur utama final.

Aturan mutlak:
1. Jangan mengulangi hal yang sudah benar.
2. Jangan menambal UI realtime lama.
3. Jangan menghapus Plan A dan Plan B.
4. Jangan mengubah dataset/raw/labels/runs/weights/models.
5. Jangan menjalankan git add .
6. Jangan membuat fake detection, fake GPS, fake bounding box, fake model readiness, fake mAP, fake best.pt, atau fake prediction.
7. Jangan menyimpan API key di repository.
8. Jangan mengklaim akurasi final PLN.
9. Jangan commit sebelum test dan diff diringkas.
10. Semua implementasi Progress 8 harus memakai route baru /plan-c dan /api/plan-c.

Teknologi final:
- Flask backend.
- Browser HP sebagai kamera dan GPS client.
- HTTPS tunnel untuk HP beda jaringan.
- YOLO untuk deteksi snapshot setelah shutter.
- AI vision sebagai validator tambahan, bukan pengganti YOLO.
- Python geometry engine sebagai penghitung utama.
- Growth model dari Excel/data lokal jika tersedia.
- Spreadsheet append-only.
- Map marker append-only.

Objek target:
- pohon_sono
- konduktor
- struktur_penyangga

Objek lain seperti orang, mobil, keyboard, ruangan, meja, tas, dan laptop boleh diabaikan untuk core result.

Output risiko:
- AMAN
- PANTAU
- SIAGA
- PERLU_PEMANGKASAN
- DATA_TIDAK_CUKUP

Bahasa:
Gunakan Bahasa Indonesia untuk penjelasan. Nama file, command, route, enum, function, class, dan path tetap teknis sesuai kode.
