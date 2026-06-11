# Runtime Final Result

## Integrasi Plan C

Runtime Plan C sekarang dapat memilih model dari System C model registry jika registry valid.

Jika registry belum valid, `plan_c_yolo.py` tetap memakai jalur fallback kandidat lama tanpa mengaktifkan realtime loop lama.

## Aturan

- Tidak ada fake detection.
- Tidak ada fake bbox.
- Tidak ada klaim akurasi final PLN.
- Tidak menghidupkan `/field-camera`, `/field-capture`, YOLO-FIRST, atau realtime loop lama.

## Status

Runtime selector mengembalikan registry model hanya jika registry menyatakan `runtime_allowed = true` dan file model ada.
