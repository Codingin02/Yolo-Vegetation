# Flask API Contract

Flask scaffold Phase 4 bersifat kontrak lokal dan belum menjalankan inference final.

## Endpoint

| Method | Path | Status |
|---|---|---|
| GET | `/health` | Mengecek service scaffold. |
| GET | `/status` | Mengembalikan status project dari `collect_project_status`. |
| GET | `/classes` | Mengembalikan class order terkunci. |
| GET | `/points` | Ringkasan titik review aktif. |
| GET | `/map` | Status kontrak peta. |
| POST | `/predict-image` | Mengembalikan `MODEL_NOT_READY` sampai model final ada. |

## Aturan

- Tidak ada upload ke `data/raw`.
- Tidak ada hasil deteksi palsu.
- Tidak ada klaim akurasi.
- Jika Flask belum tersedia, runner harus menampilkan `FLASK_NOT_INSTALLED`.

## Run Lokal

```powershell
.\venv\Scripts\python.exe scripts\run_flask_dev.py
```

Server hanya untuk pengujian lokal `127.0.0.1:5000`.
