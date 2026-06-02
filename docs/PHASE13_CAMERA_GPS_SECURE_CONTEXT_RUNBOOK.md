# Phase 13 Camera/GPS Secure Context Runbook

Sistem ini tetap field capture browser dari Flask laptop. HP hanya input foto/frame, GPS, dan metadata. Ini bukan aplikasi mobile, bukan APK, bukan Flutter, bukan React Native, dan bukan PWA standalone.

## Mode 1: LAN HTTP

```powershell
Set-Location E:\Projects\ULP_Project
.\venv\Scripts\python.exe scripts\run_field_capture_server.py --host 0.0.0.0 --port 5000
```

Buka dari HP:

```text
http://<IP-LAPTOP>:5000/field-capture
```

Fungsi utama LAN HTTP:

- upload file/foto,
- input point ID,
- input clearance/growth manual provisional,
- submit inspeksi,
- tulis CSV monitoring,
- buat marker peta jika GPS tersedia.

Catatan: Chrome HP dapat memblokir kamera/GPS otomatis pada HTTP LAN karena bukan secure context. Ini bukan error sistem. Gunakan upload file fallback atau mode HTTPS tunnel.

## Mode 2: HTTPS Tunnel Optional

Gunakan ngrok atau cloudflared secara manual bila perlu kamera/GPS browser aktif.

Contoh alur:

```powershell
.\venv\Scripts\python.exe scripts\run_field_capture_server.py --host 0.0.0.0 --port 5000
```

Lalu jalankan tunnel di terminal lain sesuai tool yang sudah operator miliki.

Jangan commit:

- authtoken ngrok,
- credential cloudflared,
- API key,
- secret tunnel.

## Mode 3: File Upload Fallback

Jika kamera browser tidak aktif:

1. Ambil foto dengan aplikasi kamera bawaan HP.
2. Buka `/field-capture`.
3. Pilih file foto.
4. Isi clearance dan growth rate manual provisional.
5. Submit inspection.

Jika GPS browser tidak aktif, latitude/longitude boleh dikosongkan. Sistem tidak membuat marker palsu. Jika koordinat nyata tersedia, operator boleh mengisi manual.

## Error Handling Phase 13

- Semua `/api/*` mengembalikan JSON walau terjadi error.
- Jika CSV utama terkunci Excel, server menulis fallback spool di `outputs/reports/spool/`.
- Submit berulang cepat dicegah oleh frontend dan dikoalesensi backend.

## Validasi

```powershell
.\venv\Scripts\python.exe scripts\print_secure_capture_options.py
.\venv\Scripts\python.exe scripts\phase13_field_capture_hardening_gate.py
```

Status yang diharapkan: `PHASE13_FIELD_CAPTURE_HARDENED_READY`.
