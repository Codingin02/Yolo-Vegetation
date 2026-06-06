# Phase 6.4 Troubleshooting Live Ngrok HP

Jika HP tidak bisa membuka halaman:

1. Pastikan Flask server hidup di laptop.
2. Pastikan Ngrok berjalan dengan `ngrok http 5000`.
3. Pastikan HP membuka `https://<public-tunnel-url>/field-capture`, bukan LAN `http://192.168.x.x`.
4. Jalankan preflight:

```powershell
.\venv\Scripts\python.exe scripts\progress6_4_live_field_acceptance_preflight.py
```

Jika kamera atau GPS tidak muncul:

- Pastikan URL memakai HTTPS public tunnel.
- Cek permission browser untuk kamera dan lokasi.
- Jangan gunakan LAN HTTP untuk field trial.
- Pastikan halaman tetap foreground karena browser bisa membatasi timer/kamera/lokasi saat halaman disembunyikan.

Jika map NO_GPS_NO_MARKER:

- Itu valid jika GPS belum punya lat/lon.
- Jika GPS valid tetapi marker tidak muncul, catat problem_note dan ulangi preflight/report.

Jika model masih MODEL_NOT_READY:

- Itu status aman sampai `best.pt` custom tersedia dan valid.
- Jangan klaim deteksi AI final.
- Labeling/training tetap jalur terpisah dari acceptance live HP.
