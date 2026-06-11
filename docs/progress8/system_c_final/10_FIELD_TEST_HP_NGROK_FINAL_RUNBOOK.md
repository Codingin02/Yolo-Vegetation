# SYSTEM C FINAL — Field Test HP + Ngrok Final Runbook

## Tujuan

Menguji sistem Plan C di kondisi jaringan berbeda:

```text
Laptop: Wi-Fi kantor/rumah
HP: paket data atau Wi-Fi berbeda
Akses: HTTPS public tunnel
```

## Start server

Dari PowerShell:

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_plan_c_final_server.py --host 0.0.0.0 --port 5000
```

Jika script server final belum ada, gunakan runner Plan C yang tersedia di repo.

## Start ngrok

Di terminal lain:

```powershell
ngrok http 5000
```

Ambil URL Forwarding:

```text
https://<url-ngrok>/plan-c
```

Contoh format:

```text
https://xxxx.ngrok-free.dev/plan-c
```

## HP test

Di HP:

1. Buka URL `/plan-c`.
2. Klik Start.
3. Izinkan kamera.
4. Izinkan GPS.
5. Ambil foto pohon/kabel/tiang.
6. Tunggu processing.
7. Buka result.
8. Cek annotated image.
9. Cek risk status.
10. Cek map.
11. Klik operator feedback benar/salah.

## Validasi jaringan berbeda

HP harus tetap bisa akses walau tidak satu Wi-Fi dengan laptop. Jika tidak bisa, masalah ada di tunnel/server/firewall, bukan di YOLO.

## Jika kamera/GPS gagal

Pastikan:

```text
- URL HTTPS, bukan HTTP
- browser HP memberi izin kamera
- browser HP memberi izin lokasi
- bukan mode incognito yang memblokir izin
- tunnel masih online
- server Flask masih hidup
```

## Domain mudah diingat

Ngrok free biasanya memberi domain acak. Untuk domain tetap dan mudah diingat, pakai reserved domain jika akun mendukung, atau Cloudflare Tunnel dengan domain sendiri. Jangan hard-code URL ngrok ke repo.

## Bukti field test

Simpan bukti:

```text
session_id
waktu
URL mode
GPS status
camera status
original.jpg
annotated.jpg
result.json
map marker
screenshot HP
```

## Status field acceptance

```text
PLAN_C_FIELD_TEST_HP_HTTPS_PASS
PLAN_C_FIELD_TEST_GPS_PASS
PLAN_C_FIELD_TEST_CAMERA_PASS
PLAN_C_FIELD_TEST_RESULT_PASS
PLAN_C_FIELD_TEST_MAP_PASS
```
