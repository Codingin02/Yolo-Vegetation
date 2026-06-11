# SYSTEM C FINAL — Failure Recovery dan Anti-Repeat Rules

## Aturan utama

Jika sudah benar, jangan diulang. Jika belum benar, koreksi sampai benar. Jangan terburu-buru.

## Jangan ulang

Jangan ulang:

```text
Plan A realtime lama
Plan B AI realtime lama
/field-camera patch lama
UI indikator lama
script progress6 lama
smoke lama yang sudah tidak relevan
```

## Jika download gagal

Jika HTTP 429:

```text
SOURCE_RATE_LIMITED
```

Tindakan:

```text
- jangan retry tanpa batas
- pindah sumber lain
- lanjut manifest
- catat failure
```

## Jika gambar ada tetapi label belum ada

Status benar:

```text
GAMBAR_ADA_TAPI_BOUNDING_LABEL_BELUM_ADA
```

Tindakan:

```text
- jalankan pseudo-labeler
- build review package
- jangan training
```

## Jika label ada tetapi belum review

Status benar:

```text
REVIEW_PACKAGE_READY_NOT_FINAL_TRAINING
```

Tindakan:

```text
- buka di Roboflow
- review manual
- export YOLOv8
```

## Jika dataset belum cukup

Status benar:

```text
PLAN_C_8_6_DATASET_NOT_READY
YOLO_TRAINING_SKIPPED_DATASET_NOT_READY
```

## Jika model belum siap

Status benar:

```text
YOLO_MODEL_NOT_READY
DATA_TIDAK_CUKUP
```

## Jika runtime tidak berubah di HP

Cek:

```text
- browser cache
- route yang dibuka harus /plan-c
- server sudah restart
- file static version query berubah
- ngrok URL benar
- HP membuka HTTPS URL terbaru
```

Jangan langsung menambal UI lama.

## Jika result page tidak ada deteksi

Cek:

```text
- model registry ada
- best.pt ada
- data.yaml class order benar
- inference route membaca model registry
- foto memang berisi target
- confidence threshold tidak terlalu tinggi
- annotated.jpg dibuat
- developer.json berisi alasan
```

## Jika zona salah

Cek:

```text
- conductor_y tervalidasi
- ground_reference_y bukan bawah foto sembarang
- meter_per_pixel valid
- ZONA_TEBANG 0–3 m dari konduktor ke bawah
- ZONA_PANTAU 3–6 m dari konduktor ke bawah
- ZONA_AMAN dari batas 6 m ke ground_reference_y
```

## Jika ingin domain mudah diingat

Gunakan reserved domain ngrok atau Cloudflare Tunnel dengan domain sendiri. Jangan hard-code domain sementara ke repo.
