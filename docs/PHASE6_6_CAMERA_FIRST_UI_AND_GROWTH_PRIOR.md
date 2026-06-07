# Phase 6.6 Camera-First UI And Growth Prior

Progress 6.6 memindahkan workflow operator ke pola camera-first.

Alur HP:

1. Buka public HTTPS tunnel ke `/field-capture`.
2. Isi `point_id` dan operator opsional.
3. Tekan `Start` saat berdiri di bawah pohon.
4. Browser meminta izin lokasi dan kamera.
5. Setelah session backend mulai, UI berpindah ke `/field-camera?session_id=...`.
6. `/field-camera` adalah layar kamera penuh dengan tombol bawah horizontal: Stop, Map, Report, Shutter, Result, Manual.

`/field-capture` bukan dashboard panjang lagi. Detail runtime dan debug dipindah ke `Developer Debug` yang default tertutup.

Backend session route harus aman:

- `/api/field/session/start` tidak boleh 500 untuk payload HP realistis.
- `/api/field/session/shutter` idempotent dan tidak append CSV duplikat.
- `/api/field/session/stop` tetap JSON meskipun session kosong.

Growth prior pohon sono:

- Dataset Excel lokal berada di `data/growth_model/pohon_sono/`.
- File Excel tidak di-commit.
- Source status selalu `PROXY_NOT_FIELD_OBSERVED`.
- Growth prior hanya baseline ETA, bukan klaim akurasi biologis final.
- Jika geometry/clearance belum cukup, ETA tetap `INSUFFICIENT_GEOMETRY_DATA`.

Model runtime:

- `MODEL_NOT_READY` tetap mode aman.
- Sistem tidak membuat fake detection, fake GPS, fake precision, fake label, atau fake best.pt.
