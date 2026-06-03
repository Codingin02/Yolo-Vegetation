# Field Trial Quickstart HP Browser ke Laptop

1. Jalankan server laptop:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

2. Buat tunnel HTTPS manual:

```powershell
ngrok http 5000
```

atau:

```powershell
cloudflared tunnel --url http://localhost:5000
```

3. HP membuka:

```text
https://<public-tunnel-url>/field-capture
```

4. Tekan `Mulai Deteksi Pohon`.

5. Jika model belum ada, sistem tetap menguji kamera/GPS/tunnel/latency tetapi menampilkan `MODEL_NOT_READY`.

6. Tekan `Kirim Snapshot Report` untuk menulis CSV/map snapshot.

HP hanya browser input. Laptop tetap server pemrosesan. Monitoring resmi tetap CSV/Sheets-ready dan map.
