# 04 — YOLO, AI, and Geometry Policy

## YOLO

YOLO hanya jalan setelah snapshot diterima backend. YOLO menghasilkan bounding box, class, confidence, dan annotated image.

Target:
- pohon_sono
- konduktor
- struktur_penyangga

Jika YOLO tidak siap:
- jangan crash,
- jangan fake detection,
- return YOLO_MODEL_NOT_READY,
- risk_status DATA_TIDAK_CUKUP,
- manual_review_required true.

## AI Vision

AI vision hanya validator tambahan. AI boleh memberi second opinion dan ringkasan visual.

AI tidak boleh menggantikan YOLO bounding box, menggantikan Python geometry, membuat fake box, atau menghitung final clearance.

Jika API key tidak ada:
- return AI_VALIDATOR_DISABLED,
- pipeline tetap lanjut.

## Python Geometry

Python geometry adalah sumber utama perhitungan:
- distance,
- height,
- clearance,
- risk status,
- prediction window.

Default:
- pole height 10.5 sampai 12 meter,
- default 11 meter,
- clearance threshold 3 meter.
