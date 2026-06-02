# HP to Laptop Field Workflow

## Jalankan Laptop Server

```powershell
.\venv\Scripts\python.exe scripts\run_field_capture_server.py
```

## Buka dari HP

```text
http://<IP-LAPTOP>:5000/field-capture
```

## Alur

1. HP membuka kamera lewat browser.
2. Operator capture frame atau upload foto.
3. Browser mengambil GPS jika izin tersedia.
4. HP mengirim foto, GPS, point_id, jenis objek manual, dan catatan.
5. Laptop menyimpan job runtime di `data/runtime/`.
6. Jika model belum siap, hasil ringkas tetap jujur: `MODEL_NOT_READY`.
7. Jika data manual cukup, risk calculator bisa diuji tanpa fake detection.
8. Report dan peta ditulis hanya saat mode write diminta.

## Setelah Labeling Selesai

Jalankan import dry-run, validate, build dataset dry-run, lalu training hanya dengan izin operator.
