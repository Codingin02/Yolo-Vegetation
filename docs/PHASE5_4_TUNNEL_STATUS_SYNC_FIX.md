# Phase 5.4 Tunnel Status Sync Fix

Bug yang diperbaiki: UI menampilkan `NO_PUBLIC_TUNNEL_CONFIGURED` walau Ngrok HTTPS aktif.

Kontrak baru:

- `GET /api/runtime/tunnel-status` membaca `http://127.0.0.1:4040/api/tunnels`.
- `GET /api/runtime/public-links` memakai public HTTPS Ngrok jika tersedia.
- `GET /api/runtime/status` memakai sumber public link yang sama.
- Jika Ngrok HTTPS aktif, UI menampilkan `NGROK_HTTPS_TUNNEL_READY` dan tombol `Copy Public HTTPS URL` memakai URL tersebut.
- Jika Ngrok tidak aktif, status tetap jujur: `PUBLIC_TUNNEL_NOT_RUNNING` dan command operator `ngrok http 5000`.

Tunnel URL runtime tidak disimpan ke Git.
