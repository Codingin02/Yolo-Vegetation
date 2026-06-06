# Phase 6.3 Status Consistency And Model State

Progress 6.1 dapat menunjukkan bahwa pipeline labeling/training siap. Itu bukan berarti model custom sudah siap.

Status dipisah:

- `label_export_status`: export MakeSense tersedia atau belum.
- `dataset_yaml_status`: dataset YOLO sudah dibangun atau belum.
- `bestpt_status`: `best.pt` tersedia dan valid atau belum.
- `runtime_model_status`: runtime 5.4 membaca `MODEL_NOT_READY` atau `REAL_MODEL`.
- `status_consistency`: audit gabungan agar operator tidak salah membaca pipeline sebagai model final.

Jika pipeline siap tetapi `best.pt` belum valid:

`PIPELINE_READY_BUT_REAL_MODEL_NOT_AVAILABLE`

Pesan operator:

`Training pipeline/code siap, tetapi custom YOLO belum menjadi REAL_MODEL.`

Jika `best.pt` ada tetapi class order belum diverifikasi:

`BESTPT_PRESENT_CLASS_ORDER_NOT_VERIFIED`

Class order tetap:

0. `struktur_penyangga`
1. `konduktor`
2. `pohon_sono`

Runtime baru boleh disebut `REAL_MODEL` jika model valid dan tidak melanggar class order.
