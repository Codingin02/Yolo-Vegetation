# Phase 18 Field Calibration Workflow

Kalibrasi memakai referensi nyata:

- `struktur_penyangga_20kv`
- `known_marker`
- `manual_reference`

Runtime profile ditulis ke `data/runtime/calibration/` dan tidak boleh masuk Git.

Command:

```powershell
.\venv\Scripts\python.exe scripts\phase18_calibration_gate.py
```
