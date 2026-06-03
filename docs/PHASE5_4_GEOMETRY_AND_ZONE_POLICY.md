# Phase 5.4 Geometry And Zone Policy

## Referensi Tiang

Config:

```text
configs/electrical_asset_geometry.yaml
```

Default:

```yaml
default_pole_visible_height_m: 10.8
default_pole_total_height_m: 11.0
source_status: FIELD_DEFAULT_NEEDS_PLN_CONFIRMATION
```

Nilai ini bukan kebenaran mutlak. Tinggi tiang harus bisa diganti dari data PLN/ULP atau calibration profile lapangan.

## Pixel-To-Meter

```text
meter_per_px = pole_reference_height_m / pole_pixel_height
```

Contoh:

```text
pole_pixel_height = 550 px
pole_reference_height_m = 11.0
meter_per_px = 0.02
```

Jika tiang tidak terdeteksi, status `REFERENCE_OBJECT_NOT_FOUND` atau `CALIBRATION_NOT_READY`.

## Clearance

Koordinat gambar memakai arah y turun ke bawah.

```text
cable_height_m = (pole_base_y - cable_y) * meter_per_px
tree_top_height_m = (pole_base_y - tree_top_y) * meter_per_px
clearance_m = (tree_top_y - cable_y) * meter_per_px
```

Jika ground line belum terverifikasi, reason code `GROUND_LINE_UNVERIFIED`.

## Zona

- `TEBANG` / `CRITICAL`: clearance `<= 3.0 m`
- `PANTAUAN`: clearance `> 3.0 m` sampai `<= 4.0 m`
- `AMAN`: clearance `> 4.0 m`
- `INSUFFICIENT_DATA`: objek/kalibrasi belum cukup

## Smoothing

Config:

```text
configs/realtime_stability.yaml
```

Aturan:

- stable update 1 detik
- smoothing window 5 sampel
- jump `> 0.75 m` diberi `JITTER_REJECTED`
- object hilang `< 2 detik` diberi `TRACK_HOLD`
- object hilang `> 2 detik` diberi `OBJECT_LOST`
- latency `> 3000 ms` diberi `HIGH_LATENCY`
