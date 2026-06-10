# 03 — Plan C Storage Append Only

Storage Plan C harus append-only.

## Root

data/runtime/plan_c

## Session Folder

data/runtime/plan_c/sessions/<session_id>

File wajib:
- original.jpg
- annotated.jpg
- result.json
- developer.json
- metadata.json
- yolo_raw.json
- ai_raw.json
- geometry.json

## Spreadsheet

data/runtime/plan_c/spreadsheet/plan_c_records.csv  
data/runtime/plan_c/spreadsheet/plan_c_records.jsonl

Setiap shutter menambah satu record. Jangan reset. Jangan overwrite tanpa preserve row lama.

## Map

data/runtime/plan_c/map/plan_c_markers.json

Setiap result menambah satu marker. Marker lama harus tetap ada.

## Anti Reset

Jika user jepret dua kali, CSV punya dua row.  
Jika user buka ulang server, data lama tetap ada.  
Jika map dibuka ulang, marker lama tetap ada.
