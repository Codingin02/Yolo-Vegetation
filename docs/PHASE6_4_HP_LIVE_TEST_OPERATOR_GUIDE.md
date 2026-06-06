# Phase 6.4 HP Live Test Operator Guide

Jalankan dari laptop server.

Terminal 1:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
```

Terminal 2:

```powershell
ngrok http 5000
```

Terminal 3:

```powershell
.\venv\Scripts\python.exe scripts\progress6_4_live_field_acceptance_preflight.py
.\venv\Scripts\python.exe scripts\operator_command_center.py --print-field-acceptance-url
```

Di HP, gunakan paket data atau Wi-Fi berbeda dari laptop, lalu buka:

```text
https://<public-tunnel-url>/field-capture
https://<public-tunnel-url>/field-acceptance
```

Langkah HP:

1. Buka public HTTPS URL.
2. Tekan Start.
3. Izinkan kamera dan lokasi dari prompt browser.
4. Tunggu status GPS_READY, GPS_ACTIVE, atau GPS_ACCURACY_LOW.
5. Pastikan preview kamera muncul.
6. Tekan Shutter.
7. Buka Report.
8. Buka Result.
9. Buka Acceptance.
10. Isi operator/device/network/note.
11. Centang bukti yang benar-benar terjadi.
12. Submit Acceptance.

Jika server atau Ngrok belum running, preflight akan menampilkan command yang perlu dijalankan. Kondisi itu bukan kegagalan kode.
