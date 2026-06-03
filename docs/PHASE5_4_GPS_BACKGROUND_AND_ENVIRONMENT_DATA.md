# Phase 5.4 GPS Background And Environment Data

## GPS Background

Setelah operator menekan `Izinkan GPS`, browser menjalankan `watchPosition`.

GPS dipakai untuk metadata lokasi, grouping titik, map/report, evidence posisi, validasi titik, dan future spatial calibration. GPS tidak mengganti pixel-to-meter scaling kamera.

Jika accuracy `> 20 m`, status:

`LOW_ACCURACY`

Jika GPS tidak ada, shutter tetap tersimpan tetapi map marker tidak dibuat:

`NO_GPS_NO_MARKER`

## Environment

Default tidak melakukan live fetch.

Status default:

- `ENVIRONMENT_NOT_AVAILABLE`
- `RAINFALL_DATA_NOT_AVAILABLE`
- `SOIL_DATA_NOT_AVAILABLE`
- `SOIL_DATA_NOT_AVAILABLE` untuk pH tanah
- `SEASON_DATA_NOT_AVAILABLE`

Open-Meteo, NASA POWER, SoilGrids, atau manual CSV boleh ditambahkan nanti dengan flag eksplisit. Data lingkungan tidak boleh dikarang.
