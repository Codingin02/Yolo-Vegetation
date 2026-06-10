# CODEX TASK PROMPT — Progress 8 Plan C Snapshot Processing

Gunakan prompt ini setelah Codex limit reset.

Anda bekerja di repository:
E:\Projects\ULP_Project

Branch kerja:
progress8-plan-c-snapshot-processing

Worktree:
E:\Projects\ULP_Project_PROGRESS8_PLAN_C_CONTEXT

Baca dulu:
- AGENTS.md
- .codex/progress8_master_context.json
- .codex/progress8_guardrails.json
- .codex/progress8_route_storage_schema.json
- .codex/progress8_acceptance_matrix.json
- .codex/progress8_task_graph.json

Tugas:
Implementasikan Progress 8 Plan C sebagai sistem baru. Jangan lanjutkan realtime Plan A/B. Jangan menambal /field-camera lama. Buat jalur baru /plan-c.

Plan C adalah:
snapshot capture dari HP -> upload foto ke laptop -> YOLO post-capture -> AI validator optional -> Python geometry -> growth prediction -> result page -> spreadsheet append-only -> map marker append-only.

File baru yang disarankan:
src/ulp_project/plan_c_routes.py
src/ulp_project/plan_c_session.py
src/ulp_project/plan_c_storage.py
src/ulp_project/plan_c_yolo.py
src/ulp_project/plan_c_ai_validator.py
src/ulp_project/plan_c_geometry.py
src/ulp_project/plan_c_growth_model.py
src/ulp_project/plan_c_processor.py
src/ulp_project/plan_c_map.py

src/ulp_project/templates/plan_c_home.html
src/ulp_project/templates/plan_c_capture.html
src/ulp_project/templates/plan_c_processing.html
src/ulp_project/templates/plan_c_result.html
src/ulp_project/templates/plan_c_map.html
src/ulp_project/templates/plan_c_developer.html

src/ulp_project/static/plan_c.css
src/ulp_project/static/plan_c_capture.js
src/ulp_project/static/plan_c_result.js

scripts/plan_c_smoke.py
docs/progress8/PLAN_C_IMPLEMENTATION_REPORT.md

Route wajib:
GET  /plan-c
GET  /plan-c/capture/<session_id>
GET  /plan-c/processing/<session_id>
GET  /plan-c/result/<session_id>
GET  /plan-c/map
GET  /plan-c/developer/<session_id>
POST /api/plan-c/session/start
POST /api/plan-c/session/tree-anchor
POST /api/plan-c/session/snapshot
GET  /api/plan-c/session/<session_id>/status
GET  /api/plan-c/session/<session_id>/result

Larangan:
- Jangan edit dataset/raw/labels/runs/weights/models.
- Jangan hapus Plan A dan Plan B.
- Jangan gunakan realtime YOLO loop.
- Jangan gunakan AI realtime switch.
- Jangan tampilkan YOLO-FIRST.
- Jangan tampilkan debug bertumpuk di operator page.
- Jangan membuat fake bounding box.
- Jangan membuat fake GPS.
- Jangan git add .

Acceptance:
1. /plan-c bisa dibuka.
2. session start membuat session_id.
3. tree-anchor menyimpan GPS jika tersedia, tetapi kamera tidak boleh diblokir jika GPS gagal.
4. capture page bersih.
5. snapshot upload menyimpan original.jpg.
6. pipeline membuat result.json.
7. jika YOLO tidak siap, status YOLO_MODEL_NOT_READY dan DATA_TIDAK_CUKUP, bukan crash.
8. jika AI key tidak ada, status AI_VALIDATOR_DISABLED, bukan crash.
9. spreadsheet CSV dan JSONL append-only.
10. map marker append-only.
11. result page menampilkan foto/result.
12. developer page menampilkan debug.
13. py_compile PASS.
14. scripts/plan_c_smoke.py PASS.
15. git diff --check PASS.

Sebelum selesai:
- tampilkan file yang dibuat,
- tampilkan route yang aktif,
- tampilkan test yang dijalankan,
- tampilkan git diff --stat,
- tampilkan git status --short,
- jangan klaim selesai jika masih ada fail.
