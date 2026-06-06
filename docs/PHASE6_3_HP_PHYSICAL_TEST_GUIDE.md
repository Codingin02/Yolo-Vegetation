# Phase 6.3 HP Physical Test Guide

1. Jalankan Flask di laptop:

   `.\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000`

2. Jalankan tunnel:

   `ngrok http 5000`

3. Buka HP dari paket data atau Wi-Fi berbeda:

   `https://<public-tunnel-url>/field-capture`

4. Tekan `Start`.

5. Izinkan kamera dan lokasi dari prompt resmi browser.

6. Pastikan kamera preview muncul, GPS aktif, dan recording foreground.

7. Tekan `Stop Record`.

8. Buka:

   `https://<public-tunnel-url>/field-report`

   `https://<public-tunnel-url>/field-result`

   `https://<public-tunnel-url>/field-acceptance`

9. Di `/field-acceptance`, isi checklist manual operator dan submit evidence.

Acceptance baru boleh `PHYSICAL_HP_ACCEPTANCE_PASS` jika bukti HP fisik lengkap. Jika belum, status yang benar adalah:

`PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST`
