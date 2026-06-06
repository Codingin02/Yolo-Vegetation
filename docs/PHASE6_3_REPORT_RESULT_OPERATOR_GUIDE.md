# Phase 6.3 Report Result Operator Guide

Report page:

`/field-report`

Report dibagi menjadi:

1. Session Evidence
2. GPS Evidence
3. Camera/Frame Evidence
4. AI/Model Evidence
5. Geometry/Measurement Evidence
6. Operator Notes
7. CSV/Map Links
8. Limitations

Result page:

`/field-result`

Status penting:

- `MODEL_NOT_READY_NO_AI_DETECTION`: custom YOLO belum tersedia, tidak ada deteksi AI.
- `INSUFFICIENT_GEOMETRY_DATA`: objek/geometri belum cukup untuk clearance.
- `CALIBRATION_NOT_READY_CLEARANCE_NOT_FINAL`: clearance belum boleh dianggap final.
- `GPS_LOW_ACCURACY_DISTANCE_NOT_RELIABLE`: GPS aktif, tetapi jarak mundur belum reliabel.
- `FIELD_RESULT_PROVISIONAL`: hasil field awal, bukan klaim final PLN.

Manual input:

`/field-manual-input`

Semua hasil manual diberi status:

`MANUAL_OPERATOR_INPUT_NOT_AI_DETECTION`

Manual input tidak boleh dicampur sebagai hasil AI final.
