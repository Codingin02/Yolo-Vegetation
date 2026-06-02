# Phase 9 Status Report

## Status

- `FIELD_CAPTURE_BROWSER_READY`
- `PHASE9_ROUGH_REALTIME_READY` jika diagnostic dan smoke test pass.
- `MODEL_NOT_READY`: YOLO final masih menunggu label dan training.
- `CALIBRATION_NOT_READY`: tinggi/clearance presisi masih menunggu data lapangan.
- `ENVIRONMENTAL_DATA_NOT_READY`: data lingkungan real/manual CSV masih perlu integrasi lanjutan.

## Yang Siap Dicoba

- Server Flask laptop bind `0.0.0.0:5000`.
- HP membuka `/field-capture`.
- Upload foto atau fallback file galeri.
- GPS browser opsional.
- Input manual clearance/growth untuk demo ETA.
- CSV monitoring lokal.
- Map HTML bila GPS tersedia.

## Batasan

- Tidak ada training aktual.
- Tidak ada label palsu.
- Tidak ada model palsu.
- Tidak ada klaim akurasi.
- Tidak ada aplikasi mobile.
