# PROGRESS 6.27–6.29 FINAL ROUTE — KELOMPOK 2

Project: ULP_Project / PT PLN UP3 Surabaya Utara ULP Perak
Root: E:\Projects\ULP_Project
Branch: system-finalization-no-label-touch
Mode: No label touch

## Progress 6.27 — Lock Runtime YOLO-First dan Repo Hygiene

Tujuan:
- /api/field/session/frame menjadi core realtime YOLO-first.
- /api/field/session/vision-analyze hanya validator atau reviewer opsional.
- /api/field/session/shutter hanya evidence/documentation.
- field_camera.html bersih dari blank line EOF dan script duplication.
- Route session tidak boleh 404/405/500.
- No label/raw/dataset/runs/weights touch.

Deliverable:
- src/ulp_project/static/progress6_27_yolo_first_lock.js
- scripts/progress6_27_yolo_first_route_smoke.py
- reports/progress6_27_yolo_first_route_smoke.json
- git diff --check PASS

## Progress 6.28 — Measurement dan Output Session

Tujuan:
- Tracking tree candidate distabilkan.
- Edge refinement menjadi diagnostic overlay, bukan klaim final.
- Candidate conductor path dibuat local-first.
- Monocular scaling hanya aktif jika reference geometry valid.
- Clearance/ETA tetap non-final jika pole/conductor/reference geometry belum sah.
- Map dan spreadsheet menjadi output session, bukan dashboard panjang.

Status yang benar:
- TREE_MODEL_READY_CANDIDATE jika best.pt terbaca.
- POLE_MODEL_NOT_READY sampai model valid tersedia.
- CONDUCTOR_MODEL_NOT_READY sampai model valid tersedia.
- CLEARANCE_NOT_FINAL jika reference geometry belum sah.
- ETA_NOT_FINAL jika clearance final belum sah.

## Progress 6.29 — Field Acceptance dan Laporan Akhir

Tujuan:
- Uji HP melalui HTTPS tunnel.
- Kamera belakang aktif.
- GPS evidence masuk bila izin tersedia.
- Shutter menyimpan evidence.
- Map marker hanya jika GPS valid.
- Spreadsheet local-first tetap berjalan tanpa Google credential.
- Laporan akhir membekukan narasi sebagai prototype decision-support, bukan produksi final.

Yang tidak masuk klaim akhir:
- Cloud vision sebagai realtime core.
- Generic object detection.
- Clearance final tanpa geometri.
- ETA final tanpa clearance final.
- Growth final tanpa observasi lapangan.
- UI glass sebagai kontribusi utama.
