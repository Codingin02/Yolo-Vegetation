# Progress 6.3 Field Acceptance Hardening

Status target:
`PROGRESS_6_3_FIELD_ACCEPTANCE_HARDENING_READY_HP_PHYSICAL_TEST_PENDING`

Progress 6.3 tidak mengulang Progress 5.4, 6.1, atau 6.2. Layer ini menambah acceptance flow untuk uji HP fisik, audit konsistensi status model, GPS reliability policy, page visibility warning, dan hardening report/result.

Arsitektur field tetap:

`HP browser -> Public HTTPS Ngrok/Cloudflare -> Flask laptop -> runtime YOLO/report/map`

LAN HTTP tetap debug lokal. Workflow field trial memakai:

`https://<public-tunnel-url>/field-capture`

Halaman acceptance:

`https://<public-tunnel-url>/field-acceptance`

Acceptance fisik tidak otomatis PASS. Tanpa submit bukti operator dari HP, status tetap:

`PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST`

Model state:

- `MODEL_NOT_READY`: custom YOLO belum valid, sistem tidak membuat deteksi palsu.
- `REAL_MODEL`: hanya boleh muncul jika `best.pt` valid dan class order cocok.
- Progress 6.1 pipeline ready bukan berarti custom model final.

No-regression lock:

- No fake GPS.
- No fake detection.
- No fake precision.
- No label touch.
- `dataset_botol` tidak dipakai sebagai dataset utama.
