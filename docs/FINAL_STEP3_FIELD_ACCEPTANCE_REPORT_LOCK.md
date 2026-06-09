# LANGKAH BESAR 3 — Field Acceptance, Output Operator, dan Laporan Final

Status target:
SYSTEM_FINAL_READY_FOR_LIMITED_FIELD_TRIAL_AND_REPORT

Baseline:
- Langkah Besar 1: DETECTION_TRACKING_FIELD_CAMERA_LOCKED.
- Langkah Besar 2: PREDICTION_GEOMETRY_ETA_GUARDED_READY.
- Branch tetap system-finalization-no-label-touch.
- No label touch tetap aktif.

Kontrak final sistem:
- HP membuka /field-capture melalui HTTPS tunnel.
- Setelah Start, HP masuk ke /field-camera?session_id=<session_id>.
- Kamera belakang/field camera menjadi input visual.
- Route realtime utama tetap /api/field/session/frame.
- Cloud vision hanya validator opsional, bukan realtime core.
- GPS disimpan sebagai evidence lokasi.
- Shutter menyimpan evidence session.
- Map hanya marker jika GPS valid.
- Spreadsheet/result menjadi output operator.
- Prediksi clearance/ETA memakai route final-step2 dan tetap provisional.

Kontrak latency:
- Backend route smoke untuk frame, GPS, shutter, map, spreadsheet, dan prediction harus berada dalam budget 1000 ms.
- Delay jaringan HP lewat tunnel tetap dapat dipengaruhi sinyal, browser, dan kualitas koneksi.
- Jika backend lebih dari 1000 ms, gate harus gagal.

Klaim yang boleh masuk laporan:
- Prototype monitoring vegetasi jaringan distribusi 20 kV untuk limited field trial.
- HP browser sebagai field client.
- Flask laptop server sebagai backend.
- HTTPS tunnel sebagai akses beda jaringan.
- YOLO-first sebagai core realtime.
- Deteksi pohon_sono sebagai candidate detection.
- Prediction/ETA sebagai provisional jika memakai input manual dan growth proxy.
- Map dan spreadsheet sebagai evidence output.

Klaim yang tidak boleh:
- Bukan sistem produksi final PLN.
- Bukan clearance final.
- Bukan ETA final.
- Bukan growth biologis final.
- Bukan multi-class final penuh.
- Cloud vision bukan core realtime.
- GPS bukan alat ukur pixel-to-meter.
