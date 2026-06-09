# LANGKAH BESAR 1 — Deteksi Realtime dan Tracking Field Camera

Status target:
DETECTION_TRACKING_FIELD_CAMERA_LOCKED

Ruang lingkup:
- /field-capture sebagai preflight ringkas.
- /field-camera?session_id=<session_id> sebagai halaman kamera utama.
- /api/field/session/start sebagai pembuat session.
- /api/field/session/frame sebagai realtime core YOLO-first.
- /api/field/session/progress6-28-diagnostic-frame sebagai diagnostic tracking/measurement.
- /api/field/session/vision-analyze hanya validator/review opsional.
- /api/field/session/shutter hanya evidence.

Keputusan final:
- Deteksi/tracking core tidak boleh bergantung pada cloud vision.
- Cloud vision tidak boleh menjadi loop realtime.
- Jika YOLO tidak mendeteksi, sistem harus menampilkan NO_PROJECT_OBJECT_DETECTED atau TRACKING_READY_NO_DETECTION.
- Tidak boleh ada fake detection.
- Tidak boleh ada fake GPS.
- Tidak boleh ada fake clearance.
- Tree model tetap TREE_MODEL_READY_CANDIDATE jika best.pt V001 tersedia.
- Pole/conductor tetap NOT_READY sampai model sah tersedia.
- Clearance dan ETA tetap non-final.

Yang tidak boleh diulang setelah gate ini PASS:
- Rebuild field camera route.
- Rebuild YOLO-first JS lock.
- Rebuild session start/frame/GPS/shutter route.
- Rebuild tracking diagnostic bridge.
- Menjadikan vision-analyze sebagai realtime core.
