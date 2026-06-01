# Status Uji Teknologi Dasar ULP Project

## Environment

- Python venv aktif di E:\Projects\ULP_Project\venv
- CUDA aktif pada NVIDIA GeForce RTX 3050 6GB Laptop GPU
- YOLOv8n berhasil dijalankan dari kamera laptop
- Kamera aktif pada index 0

## Tracking

- Uji stability berhasil setelah memakai confidence 0.50 dan IoU 0.60
- Double person sudah berkurang
- Tracker yang dipakai: botsort.yaml

## Flask dan Ngrok

- Flask berhasil berjalan di port 5000
- Ngrok berhasil membuka akses dari laptop dan HP
- favicon.ico 404 diabaikan karena bukan error sistem

## Folium Map

- Peta berhasil dibuat di results\test_map.html
- Tile sudah diganti ke CartoDB Positron agar tidak terkena blokir OpenStreetMap

## Node.js

- Node.js v24.15.0 terdeteksi
- npm 11.12.1 terdeteksi
- Belum ada package.json karena project utama masih Python
