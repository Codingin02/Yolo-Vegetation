# SYSTEM C FINAL — Arsitektur Teknis

## Jalur final

```text
HP Browser
  -> /plan-c
  -> start session
  -> capture snapshot
  -> POST /api/plan-c/session/snapshot
  -> Flask backend
  -> save original.jpg
  -> YOLOv8 post-capture
  -> optional visual validator
  -> Python geometry
  -> growth-risk prediction
  -> annotated.jpg + result.json + developer.json
  -> CSV/JSONL append-only
  -> map marker append-only
  -> result page
```

## Komponen teknis

### Flask backend

Flask tetap menjadi server backend lokal pada laptop.

Target:

```text
host = 0.0.0.0
port = 5000
```

HP field client mengakses melalui HTTPS tunnel.

### Browser HP

HP adalah kamera, GPS, dan shutter client. HP tidak menjalankan training dan tidak menjalankan model berat. HP hanya mengambil gambar, GPS, dan membuka result.

### HTTPS tunnel

Ngrok atau Cloudflare Tunnel boleh dipakai. LAN `192.168.x.x` hanya debug. Jalur field test beda jaringan harus menggunakan HTTPS public tunnel.

### YOLOv8

YOLOv8 adalah pendeteksi utama setelah snapshot. YOLO tidak boleh diganti oleh model AI generatif. Validator AI boleh membantu review, tetapi tidak boleh menggantikan bbox YOLO.

### Python geometry

Python geometry menghitung jarak, zona, clearance estimate, dan prediction window. Perhitungan geometri bukan tugas AI validator.

### Growth model

Growth model menggunakan data proxy Pterocarpus indicus/angsana. Growth output harus tetap diberi status proxy jika belum ada data observasi lapangan.

## Route final Plan C

Route halaman:

```text
GET /plan-c
GET /plan-c/capture/<session_id>
GET /plan-c/processing/<session_id>
GET /plan-c/result/<session_id>
GET /plan-c/map
GET /plan-c/developer/<session_id>
```

Route API:

```text
POST /api/plan-c/session/start
POST /api/plan-c/session/tree-anchor
POST /api/plan-c/session/snapshot
GET  /api/plan-c/session/<session_id>/status
GET  /api/plan-c/session/<session_id>/result
POST /api/plan-c/operator-feedback
```

## Status wajib

```text
PLAN_C_SESSION_STARTED
TREE_ANCHOR_SAVED
TREE_ANCHOR_PENDING
PLAN_C_SNAPSHOT_ACCEPTED
PLAN_C_PROCESSING
PLAN_C_RESULT_READY
YOLO_MODEL_NOT_READY
AI_VALIDATOR_DISABLED
DATA_TIDAK_CUKUP
MODEL_READY_FOR_FIELD_TRIAL
```

## Zona fisik yang benar

Zona tidak dihitung dari bawah foto. Zona dihitung berdasarkan posisi konduktor dan ground reference.

Definisi:

```text
ZONA_TEBANG : 0–3 meter di bawah konduktor
ZONA_PANTAU : 3–6 meter di bawah konduktor
ZONA_AMAN   : area di bawah batas 6 meter sampai ground_reference_y
```

Jika konduktor tidak tervalidasi, sistem tidak boleh menggambar zona presisi palsu. Tampilkan `DATA_TIDAK_CUKUP`.

## Output result page

Result page harus menampilkan:

```text
risk_status
prediction_window
clearance_estimate_m
tree_height_estimate_m
detection_count
YOLO summary
geometry summary
GPS summary
growth profile summary
map link
developer link
operator review
```

Operator page tidak boleh menampilkan API key, provider, raw JSON panjang, atau debug internal.
