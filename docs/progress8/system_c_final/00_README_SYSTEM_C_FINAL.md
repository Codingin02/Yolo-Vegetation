# SYSTEM C FINAL — README UTAMA

Dokumen ini adalah acuan tunggal untuk Codex dalam menyelesaikan sistem final Plan C pada proyek ULP_Project.

Project root:

```text
E:\Projects\ULP_Project
```

Folder dokumen acuan:

```text
E:\Projects\ULP_Project\docs\progress8\system_c_final
```

Folder download sumber gambar yang diminta:

```text
D:\Users\All Users\Downloads\ULP_Project_PlanC_Dataset_Downloads
```

Folder dataset YOLO final:

```text
E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1
```

## Definisi sistem yang benar

Sistem final yang harus diselesaikan adalah **Plan C**, bukan Plan A dan bukan Plan B.

Plan A adalah riwayat riset YOLO-only realtime. Plan B adalah riwayat riset YOLO + AI realtime. Keduanya tidak boleh dihapus, tetapi tidak boleh menjadi jalur final. Plan C adalah jalur final laporan akhir: snapshot/manual capture dari HP, backend processing di laptop, YOLO post-capture, validator visual opsional, Python geometry, growth-risk prediction, spreadsheet append-only, dan map marker append-only.

## Target akhir

Target akhir bukan sekadar membuat file. Target akhir adalah sistem yang bisa:

1. HP membuka `/plan-c` melalui HTTPS tunnel.
2. Operator mengambil snapshot dari HP.
3. Backend menyimpan foto.
4. YOLOv8 mendeteksi objek setelah snapshot.
5. Bounding box muncul pada `annotated.jpg`.
6. Objek prioritas terdeteksi: `pohon_sono`, `konduktor`, `struktur_penyangga`.
7. Negative object tidak salah masuk bbox.
8. Python geometry menghitung zona berdasarkan konduktor dan ground reference.
9. Growth model memberi prediction window.
10. Hasil masuk CSV/JSONL append-only.
11. Map marker append-only.
12. Result page menampilkan output operator yang ringkas.
13. Developer page menyimpan detail internal.
14. Model registry memilih model valid.
15. Sistem tidak membuat fake detection, fake GPS, fake clearance, fake mAP, atau fake best.pt.

## Class final dataset

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono
```

## Status terakhir yang harus diselesaikan

Kondisi terakhir yang menjadi alasan tahap ini dibuat:

```text
TOTAL_IMAGE_FILES     : 3
TOTAL_LABEL_TXT_FILES : 0
TOTAL_MANIFEST_FILES  : 10
STATUS                : GAMBAR_ADA_TAPI_BOUNDING_LABEL_BELUM_ADA
```

Artinya dataset belum siap training. Masalah sekarang bukan UI, tetapi dataset, label, training, model registry, dan integrasi model ke Plan C final.

## Aturan utama

Jangan mengulang yang sudah benar. Jangan menyentuh Plan A/B. Jangan menambal `/field-camera` lama. Jangan membuat route final di luar `/plan-c`. Jangan `git add .`. Jangan commit file gambar, zip, model, token, `.env`, runtime data, atau URL ngrok.

## Urutan kerja final

1. Dataset final.
2. Pseudo-label dan review package.
3. Roboflow package.
4. Dataset gate.
5. Training YOLOv8 jika dataset siap.
6. Model registry.
7. Integrasi model ke Plan C.
8. Field test HP + ngrok.
9. Laporan akhir.
