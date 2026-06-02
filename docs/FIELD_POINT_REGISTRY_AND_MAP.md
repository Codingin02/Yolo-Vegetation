# Field Point Registry And Map

Phase 5 menyiapkan registry titik lapangan tanpa mengubah naming convention.

## Naming

- `P001_struktur_penyangga`
- `K001_konduktor`
- `V001_pohon_sono`

Tidak ada konversi ke `T001`.

## Template

```text
data/templates/field_point_registry_template.csv
```

## Map Runtime

Default dry-run:

```powershell
.\venv\Scripts\python.exe scripts\build_system_map.py --mode dry-run
```

Write mode hanya menulis ke:

```text
outputs/maps/
```

Jika GPS belum lengkap, status `GPS_DATA_NOT_READY`.
