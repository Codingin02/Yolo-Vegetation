# LANGKAH BESAR 2 — Prediksi, Geometri, Clearance, ETA, Growth Prior

Status target:
PREDICTION_GEOMETRY_ETA_GUARDED_READY

Ruang lingkup:
- Route prediksi provisional: /api/field/session/final-step2-predict
- Route status prediksi: /api/field/session/final-step2-status
- Ambang clearance prototype: 3.0 m
- Contoh validasi wajib: clearance 5.0 m dan growth 0.01 m/hari menghasilkan ETA 200 hari
- Contoh validasi wajib: clearance 2.75 m menghasilkan ETA 0 dan display floor 2
- Growth prior pohon_sono tetap PROXY_NOT_FIELD_OBSERVED jika memakai dataset proxy
- Latency budget server-side: <= 1000 ms

Klaim yang boleh:
- Prediksi provisional/manual untuk field trial terbatas.
- ETA berbasis input clearance dan growth_rate yang tersedia.
- Growth prior sebagai baseline/proxy, bukan observasi biologis final.

Klaim yang tidak boleh:
- Tidak boleh menyebut clearance final jika pole, conductor, dan reference geometry belum sah.
- Tidak boleh menyebut ETA final jika clearance final belum sah.
- Tidak boleh membuat fake detection, fake GPS, atau fake clearance.
- Tidak boleh menyentuh label, dataset, runs, weights, raw images, raw GPS, atau model.

Catatan:
Langkah Besar 2 tidak mengulang deteksi/tracking. Langkah Besar 1 sudah mengunci jalur DETECTION_TRACKING_FIELD_CAMERA_LOCKED.
