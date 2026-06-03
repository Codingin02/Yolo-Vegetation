# Phase 5.3 Operator Evidence Pack Guide

Evidence pack mencatat status runtime yang bisa diverifikasi dari laptop dan hasil uji HP yang diinput manual oleh operator.

## Command

Dry-run tanpa menulis file:

```powershell
.\venv\Scripts\python.exe scripts\progress5_3_evidence_pack.py --dry-run
```

Tulis evidence pack runtime:

```powershell
.\venv\Scripts\python.exe scripts\operator_command_center.py --evidence-pack
```

Lokasi output:

```text
data\runtime\field_trial_evidence\
```

Folder ini di-ignore Git.

## Isi Minimal

Evidence pack memuat:

- timestamp
- branch
- HEAD
- local URL
- LAN URL kandidat
- public tunnel URL bila ngrok aktif
- status ngrok
- status model
- status kalibrasi
- status transport
- health route lokal
- manual prediction smoke status
- snapshot report smoke status
- map policy status
- status konfirmasi HP fisik
- known blockers
- next operator command

## Yang Tidak Disimpan

- foto
- video
- base64 image penuh
- token
- credential
- ngrok/cloudflared authtoken
- service account JSON

## Status

- `FIELD_TRIAL_EVIDENCE_READY`: evidence pack siap.
- `HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION`: HP fisik belum dikonfirmasi operator.
- `HP_CONFIRMED`: operator sudah submit hasil checklist HP minimal.
- `PUBLIC_TUNNEL_NOT_RUNNING`: ngrok HTTPS belum aktif.
- `MODEL_NOT_READY_EXPECTED`: model custom belum tersedia.
- `CALIBRATION_NOT_READY_EXPECTED`: kalibrasi lapangan belum tersedia.
