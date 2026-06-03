# Calibration Field Guide

Kalibrasi dibutuhkan sebelum angka tinggi/jarak dianggap layak field trial.

Template:

```text
data\templates\calibration_session_template.csv
```

Contoh dry-run:

```powershell
.\venv\Scripts\python.exe scripts\create_calibration_session.py --point-id V001_pohon_sono --reference-type manual_reference --known-height-m 12 --reference-bbox-height-px 400 --image-width-px 1280 --image-height-px 720 --dry-run
```

Jangan mengarang tinggi tiang. `known_height_m` harus berasal dari PLN/manual lapangan/dokumen acuan.

Status:

- `CALIBRATION_NOT_READY`
- `CALIBRATION_READY_MANUAL_REFERENCE`
- `CALIBRATION_LOW_CONFIDENCE`
- `CALIBRATION_REJECTED_BAD_REFERENCE`
- `CALIBRATION_READY_FIELD_CONFIRMED`
