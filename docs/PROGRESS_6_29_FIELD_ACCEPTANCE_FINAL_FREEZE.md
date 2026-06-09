# Progress 6.29 — Field Acceptance dan Final Report Freeze

Baseline:
- Progress 6.27B commit 32f50eb: YOLO-first runtime route locked.
- Progress 6.28B commit 4752e6d: tracking, edge diagnostic, measurement guard route registered and validated.

Status final Kelompok 2:
- HP browser client: field-capture, camera, GPS, shutter, map, spreadsheet.
- Flask backend laptop: tetap menjadi server.
- HTTPS public tunnel: wajib untuk field access berbeda jaringan.
- LAN 192.168.x.x hanya debug.
- Realtime core: /api/field/session/frame.
- Tracking/measurement diagnostic: /api/field/session/progress6-28-diagnostic-frame.
- Shutter: evidence only.
- Cloud vision: optional validator/review, bukan realtime core.

Klaim yang boleh masuk laporan akhir:
- Sistem prototipe monitoring vegetasi 20 kV berbasis kamera HP, GPS evidence, Flask backend, HTTPS tunnel, YOLO-first candidate runtime, map evidence, dan spreadsheet-ready output.
- Sistem berhasil mengunci alur field trial terbatas: Start Session, Camera Page, Frame Route, GPS Update, Shutter, Map, Spreadsheet.
- Sistem memiliki guard ilmiah: no fake detection, no fake GPS, no fake clearance.
- Deteksi pohon_sono masih candidate detection.
- Tracking dan edge refinement digunakan sebagai diagnostic runtime.
- Measurement/clearance/ETA dijaga non-final jika model pole/conductor dan reference geometry belum sah.

Klaim yang tidak boleh masuk laporan akhir:
- Tidak boleh mengklaim sistem produksi final PLN.
- Tidak boleh mengklaim clearance final.
- Tidak boleh mengklaim ETA final.
- Tidak boleh mengklaim pertumbuhan biologis final.
- Tidak boleh mengklaim multi-class final penuh.
- Tidak boleh menjadikan cloud vision sebagai core sistem.
- Tidak boleh menyebut GPS memperbaiki geometri piksel-ke-meter.

Status field acceptance:
- FIELD_ACCEPTANCE_READY_LIMITED_TRIAL jika gate 6.29 PASS.
