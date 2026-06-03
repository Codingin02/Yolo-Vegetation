# Phase 18 Environmental Data Runbook

Layer lingkungan siap menerima:

- BMKG/manual weather observation.
- NASA POWER/Open-Meteo style weather features nanti.
- SoilGrids/manual soil features nanti.
- Manual CSV untuk pH, kelembapan, curah hujan, suhu, musim.

Validasi:

```powershell
.\venv\Scripts\python.exe scripts\validate_environmental_manual_csv.py
.\venv\Scripts\python.exe scripts\phase18_environmental_gate.py
```

Jika data belum tersedia, status tetap jujur: `ENVIRONMENT_NOT_READY` atau `ENVIRONMENT_MANUAL_TEMPLATE_PARTIAL`.
