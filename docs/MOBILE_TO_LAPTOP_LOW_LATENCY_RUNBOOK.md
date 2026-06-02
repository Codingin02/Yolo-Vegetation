# Mobile to Laptop Low Latency Runbook

## Same LAN Mode

Gunakan saat HP dan laptop satu WiFi atau hotspot.

```powershell
.\venv\Scripts\python.exe scripts\run_flask_dev.py
```

Buka dari HP:

```text
http://<laptop-ip>:5000/mobile
```

## Tunnel Mode

Gunakan saat HP memakai jaringan seluler dan laptop tetap online di rumah/kampus. Tunnel boleh memakai ngrok atau cloudflared secara manual.

Aturan:

- Jangan simpan token/auth tunnel di Git.
- Token hanya boleh lewat environment variable atau konfigurasi lokal yang tidak di-commit.
- Jangan membuka tunnel otomatis dari script project.

## Offline Queue Mode

Jika sinyal buruk, halaman `/mobile` menyimpan status antrean sederhana di browser. Saat koneksi kembali, operator dapat upload ulang.

## Low Latency Defaults

Konfigurasi ada di `configs/runtime_network.yaml`:

- `max_upload_image_mb: 8`
- `prefer_image_resize_width: 1280`
- `job_poll_interval_ms: 1000`
- `request_timeout_sec: 20`
- `allow_async_processing: true`
- `allow_sync_small_image: true`

## Endpoint Uji Aman

```powershell
.\venv\Scripts\python.exe scripts\phase6_mobile_environmental_gate.py
```

Endpoint:

- `GET /mobile`
- `GET /api/mobile/network/status`
- `GET /api/latency/ping`
- `POST /api/mobile/upload-inspection`
- `GET /api/mobile/job/<job_id>`
- `GET /api/mobile/result/<job_id>`
