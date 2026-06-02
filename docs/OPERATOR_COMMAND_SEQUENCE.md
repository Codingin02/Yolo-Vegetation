# Operator Command Sequence

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
