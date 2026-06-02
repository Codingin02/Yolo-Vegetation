# Phase 8 PLN Realtime Risk Runbook

Phase 8 menegaskan arsitektur yang benar: HP hanya field capture browser, laptop menjadi processing server, dan monitoring utama adalah spreadsheet plus peta.

## Jalankan Server Laptop

```powershell
.\venv\Scripts\python.exe scripts\run_field_capture_server.py
```

Buka dari HP:

```text
http://<IP-LAPTOP>:5000/field-capture
```

## Alur

1. HP mengirim foto/frame, GPS, point_id, dan metadata.
2. Laptop menerima upload, membuat job, dan memberi hasil ringkas.
3. Jika model belum ada, status tetap `MODEL_NOT_READY`.
4. Jika input manual clearance dan growth rate tersedia, ETA bisa dihitung sebagai estimasi manual/provisional.
5. Report ditulis ke CSV/XLSX-ready output.
6. Peta risiko dibuat dari GPS nyata saja.

## Command Aman

```powershell
.\venv\Scripts\python.exe scripts\phase8_pln_realtime_risk_gate.py
.\venv\Scripts\python.exe scripts\run_manual_risk_estimate.py --sample pohon_sono --mode dry-run
.\venv\Scripts\python.exe scripts\export_vegetation_risk_report.py --mode dry-run
.\venv\Scripts\python.exe scripts\export_vegetation_risk_map.py --mode dry-run
```

Jangan import label copy, jangan build dataset final, dan jangan training aktual sebelum label valid dan operator memberi izin.
