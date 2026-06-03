# Troubleshooting Camera, GPS, dan Tunnel

## Kamera/GPS Tidak Aktif

- Gunakan URL HTTPS tunnel, bukan HTTP LAN.
- Cek permission browser HP.
- Gunakan upload file fallback jika kamera browser tetap diblokir.

## HP Tidak Bisa Akses Laptop

- Cek server bind `0.0.0.0`.
- Cek firewall Windows private network.
- Cek tunnel `ngrok http 5000` atau `cloudflared tunnel --url http://localhost:5000`.

## Latensi Tinggi

Sistem membatasi 1 FPS dan drop frame lama jika umur frame lebih dari 3 detik.

## Token

Token session dibuat runtime di folder ignored. Jangan commit token, credential, service account JSON, atau API key.
