# Progress 6.28 — Tracking + Measurement + Output Session

Status:
- Dibangun setelah Progress 6.27B commit 32f50eb.
- Tidak mengulang route 6.27.
- Tidak menyentuh label, raw data, dataset, runs, weights, atau model.

Tujuan:
- Menambahkan tracking diagnostic bridge.
- Menambahkan edge refinement diagnostic.
- Menambahkan measurement guard.
- Menjaga clearance dan ETA tetap non-final jika pole/conductor/reference geometry belum sah.
- Menjaga cloud vision tetap opsional, bukan realtime core.

Keputusan:
- YOLO-first tetap core.
- Tracking ID boleh diuji pada synthetic diagnostic frame.
- Edge refinement bukan bukti clearance final.
- GPS adalah evidence lokasi; GPS tidak boleh diklaim sebagai pengukur pixel-to-meter.
- Growth model tetap PROXY_NOT_FIELD_OBSERVED sampai ada observasi lapangan.

Status yang sah:
- TREE_MODEL_READY_CANDIDATE
- CONDUCTOR_MODEL_NOT_READY
- POLE_MODEL_NOT_READY
- CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR
- ETA_NOT_FINAL
- SPREADSHEET_READY_AFTER_SHUTTER
- MAP_READY_IF_GPS_VALID
