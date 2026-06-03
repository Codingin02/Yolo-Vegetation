# Operator Command Sequence

## Phase 10-12 Field Capture LAN Deploy dan Demo Kasar

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\diagnose_field_capture_deploy.py
.\venv\Scripts\python.exe scripts\run_field_capture_server.py --host 0.0.0.0 --port 5000
```

Buka dari HP browser:

```text
http://<IP-LAPTOP>:5000/field-capture
```

Tes tanpa HP:

```powershell
.\venv\Scripts\python.exe scripts\phase10_lan_deploy_smoke.py
.\venv\Scripts\python.exe scripts\phase11_provisional_eta_demo.py
.\venv\Scripts\python.exe scripts\phase12_end_to_end_rough_demo.py
.\venv\Scripts\python.exe scripts\print_secure_capture_options.py
.\venv\Scripts\python.exe scripts\phase13_field_capture_hardening_gate.py
.\venv\Scripts\python.exe scripts\phase14_auto_yolo_measurement_gate.py
.\venv\Scripts\python.exe scripts\phase15_realtime_eta_system_gate.py
.\venv\Scripts\python.exe scripts\phase15_rough_realtime_auto_demo.py --mode mock-auto
```

## Phase 15 Realtime ETA Monitoring

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\diagnose_field_capture_deploy.py
.\venv\Scripts\python.exe scripts\print_secure_capture_options.py
.\venv\Scripts\python.exe scripts\run_realtime_field_pipeline.py --mode server --host 0.0.0.0 --port 5000
```

HP buka:

```text
http://<IP-LAPTOP>:5000/field-capture
```

Demo rough auto:

```powershell
.\venv\Scripts\python.exe scripts\phase15_rough_realtime_auto_demo.py --mode mock-auto
.\venv\Scripts\python.exe scripts\export_vegetation_risk_report.py --mode dry-run
.\venv\Scripts\python.exe scripts\export_vegetation_risk_map.py --mode dry-run
```

Output utama:

- CSV monitoring: `outputs\reports\vegetation_risk_monitoring.csv`
- Map risiko: `outputs\reports\vegetation_risk_map.html`

Catatan: HP hanya field capture browser. Laptop adalah processing server. Jangan membuat APK/mobile app.

Semua command dijalankan dari:

```powershell
Set-Location E:\Projects\ULP_Project
```

Gunakan Python venv lokal:

```powershell
.\venv\Scripts\python.exe
```

## Phase 9 Rough Realtime Field Capture

HP hanya field capture browser. Laptop tetap processing server. Monitoring utama adalah CSV spreadsheet-ready dan peta.

1. Masuk folder project:

```powershell
Set-Location E:\Projects\ULP_Project
```

2. Jalankan diagnostic deploy:

```powershell
.\venv\Scripts\python.exe scripts\diagnose_field_capture_deploy.py
```

3. Jalankan server laptop:

```powershell
.\venv\Scripts\python.exe scripts\run_field_capture_server.py --host 0.0.0.0 --port 5000
```

4. Buka dari HP satu jaringan:

```text
http://<IP-LAPTOP>:5000/field-capture
```

5. Tes latency:

```text
http://<IP-LAPTOP>:5000/api/latency/ping
```

6. Submit data manual kasar di halaman:

- `point_id`: `V001_pohon_sono`
- `species`: `pohon_sono`
- `asset_type`: `span`
- `clearance_m`: contoh `0.3`
- `growth_rate_m_per_day`: contoh `0.01`

7. Cek report CSV:

```text
outputs\reports\vegetation_risk_monitoring.csv
```

8. Cek map jika GPS tersedia:

```text
outputs\reports\vegetation_risk_map.html
```

9. Smoke test tanpa HP:

```powershell
.\venv\Scripts\python.exe scripts\phase9_rough_realtime_smoke.py
```

Stop server dengan `Ctrl+C` di terminal server.

## Aman Dijalankan Sekarang

Command berikut tidak menulis label, tidak build dataset final, dan tidak training final.

```powershell
.\venv\Scripts\python.exe -m compileall src scripts tests
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe scripts\phase2_system_smoke_test.py
.\venv\Scripts\python.exe scripts\phase3_readiness_gate.py
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\train_yolov8_field_multiclass.py --dry-run
```

## Setelah Export YOLO makesense.ai Selesai

Letakkan export YOLO di:

```text
data\exports\make_sense\V001_pohon_sono
```

Lalu jalankan:

```powershell
.\venv\Scripts\python.exe scripts\phase3_readiness_gate.py
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode dry-run
.\venv\Scripts\python.exe scripts\import_makesense_yolo_export.py --point V001_pohon_sono --mode copy
.\venv\Scripts\python.exe scripts\validate_yolo_labels.py --point V001_pohon_sono
```

Gunakan `--overwrite` hanya jika benar-benar ingin mengganti label yang sudah ada.

## Setelah Validasi Label PASS

Command berikut belum boleh dijalankan sampai validator mengembalikan `VALID`.

```powershell
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode dry-run --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\build_field_multiclass_dataset.py --mode build --val-ratio 0.2 --seed 23050874166
.\venv\Scripts\python.exe scripts\generate_data_yaml.py --mode write
.\venv\Scripts\python.exe scripts\train_yolov8_field_multiclass.py --dry-run
```

## Training Final

Training final belum boleh dijalankan sebelum:

- Export YOLO makesense.ai selesai.
- Import label selesai.
- Validator label `VALID`.
- Dataset final `field_multiclass_v1` sudah dibangun.
- `data.yaml` tersedia.

Command training eksplisit nanti:

```powershell
.\venv\Scripts\python.exe scripts\train_yolov8_field_multiclass.py --run --model yolov8n.pt --epochs 50 --imgsz 640 --batch auto --device 0
```

Jangan klaim akurasi sampai training dan evaluasi nyata selesai.

## Phase 16 Remote Realtime Streaming

Phase 16 bukan aplikasi HP. HP tetap field capture browser, sedangkan laptop tetap processing server.

1. Diagnose dan tampilkan link:

```powershell
.\venv\Scripts\python.exe scripts\diagnose_field_capture_deploy.py
.\venv\Scripts\python.exe scripts\print_remote_realtime_links.py
```

2. Jalankan laptop processing server:

```powershell
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

3. Mode LAN debug:

```text
http://<IP-LAPTOP>:5000/field-capture
```

4. Mode remote HTTPS tunnel untuk kamera/GPS otomatis beda jaringan:

```powershell
ngrok http 5000
# atau
cloudflared tunnel --url http://localhost:5000
```

Lalu HP membuka:

```text
https://<public-tunnel-url>/field-capture
```

5. Di HP tekan:

```text
Mulai Deteksi Pohon
```

Realtime client mengirim maksimal 1 frame/detik. Jika latensi lebih dari 3 detik, frame lama di-drop. Spreadsheet/map ditulis hanya lewat tombol `Kirim Snapshot Report` atau snapshot stabil, bukan setiap frame mentah.
