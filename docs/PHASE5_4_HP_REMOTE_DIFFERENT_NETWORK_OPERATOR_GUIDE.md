# Phase 5.4 HP Remote Different Network Operator Guide

Gunakan panduan ini saat HP tidak satu jaringan dengan laptop.

1. Laptop:
   ```powershell
   Set-Location E:\Projects\ULP_Project
   .\venv\Scripts\python.exe scripts\operator_command_center.py --diagnose
   .\venv\Scripts\python.exe scripts\run_remote_realtime_server.py --host 0.0.0.0 --port 5000
   ```
2. Terminal kedua:
   ```powershell
   ngrok http 5000
   ```
3. Laptop:
   ```powershell
   .\venv\Scripts\python.exe scripts\operator_command_center.py --public-tunnel-smoke
   ```
4. HP buka `https://<public-tunnel-url>/field-capture`.
5. Tekan `Izinkan Kamera`, `Izinkan GPS`, `Mulai Deteksi`, lalu `Jepret / Shutter`.
6. Buka `Buka Spreadsheet/CSV` dan `Buka Map`.

Jika HP membuka `http://192.168.x.x:5000/field-capture`, itu debug LAN. Untuk field trial beda jaringan, buka public HTTPS URL.
