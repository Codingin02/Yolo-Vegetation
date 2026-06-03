# Phase 5.3 Field Trial Checklist

Halaman checklist:

```text
http://127.0.0.1:5000/field-trial-checklist
https://<ngrok-public-url>/field-trial-checklist
```

## Sebelum HP

Laptop:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\operator_command_center.py --diagnose
.\venv\Scripts\python.exe scripts\operator_command_center.py --print-links
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Terminal kedua:

```powershell
ngrok http 5000
```

Laptop:

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --ngrok-probe
```

## Di HP

1. Buka `https://<ngrok-public-url>/field-capture`.
2. Tekan Test koneksi laptop/server.
3. Tekan Ambil GPS HP.
4. Tekan Start kamera.
5. Isi input manual:
   - point_id: `V001_pohon_sono`
   - species: `pohon_sono`
   - asset_type: `span`
   - clearance_m: `5.0`
   - growth_rate_m_per_day: `0.01`
6. Jalankan Prediksi Manual/Provisional.
7. Pastikan ETA 200 hari untuk clearance 5.0 dan growth 0.01.
8. Kirim Snapshot Report.
9. Buka map bila GPS valid. Jika GPS kosong, status harus `NO_GPS_NO_MARKER`.
10. Buka `/field-trial-checklist`.
11. Isi hasil uji HP dan catatan operator.

## Bukti Yang Dicatat

- public URL bisa dibuka atau tidak
- test koneksi berhasil atau tidak
- kamera preview berhasil atau alasan gagal
- GPS berhasil atau alasan gagal
- manual prediction berhasil
- snapshot report berhasil
- map report berhasil atau `NO_GPS_NO_MARKER`
- screenshot evidence dicatat manual, bukan di-upload ke Git

## Setelah HP

Laptop:

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --evidence-pack
.\venv\Scripts\python.exe scripts\operator_command_center.py --progress5-3-gate
```

Jika checklist HP belum di-submit, status akhir tetap:

```text
HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION
```
