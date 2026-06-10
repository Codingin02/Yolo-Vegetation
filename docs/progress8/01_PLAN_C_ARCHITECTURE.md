# 01 — Plan C Architecture

## Arsitektur Utama

Plan C terdiri dari:

1. HP browser client.
2. Flask backend.
3. YOLO post-capture processor.
4. AI vision validator.
5. Python geometry engine.
6. Growth prediction engine.
7. Append-only storage.
8. Result page.
9. Map page.
10. Developer diagnostics page.

## HP Browser Client

HP bertugas membuka /plan-c, meminta izin kamera/GPS, mengambil tree anchor, mengambil snapshot, lalu upload foto dan metadata.

HP tidak menjalankan YOLO. HP tidak menjalankan AI. HP tidak menghitung geometry final.

## Backend Laptop

Backend bertugas membuat session, menerima snapshot, menyimpan original.jpg, memproses YOLO, memproses AI validator jika aktif, menghitung geometry, menghitung risk prediction, menyimpan result, append spreadsheet, dan append map marker.

## Non-Realtime Rule

Tidak ada realtime detection loop.  
Tidak ada YOLO-FIRST.  
Tidak ada AI realtime switch.  
Polling status processing boleh karena hanya mengecek apakah snapshot processing selesai.
