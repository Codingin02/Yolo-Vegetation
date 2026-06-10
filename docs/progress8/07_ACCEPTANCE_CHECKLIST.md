# 07 — Acceptance Checklist

## Wajib PASS

- /plan-c return 200.
- session start return session_id prefix PC_.
- tree-anchor tidak memblokir kamera saat GPS gagal.
- capture page bersih.
- snapshot upload menyimpan original.jpg.
- result.json dibuat.
- developer.json dibuat.
- YOLO missing tidak crash.
- AI key missing tidak crash.
- CSV append-only.
- JSONL append-only.
- map marker append-only.
- result page menampilkan risk_status dan prediction_window.
- developer page menampilkan diagnostics.
- py_compile PASS.
- scripts/plan_c_smoke.py PASS.
- git diff --check PASS.

## Wajib Tidak Muncul

- MODEL_STATUS_UNKNOWN
- YOLO-FIRST
- AI realtime switch
- fake_detection
- fake_gps
- git add .
