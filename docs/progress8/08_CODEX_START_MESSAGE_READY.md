# PROGRESS 8 / PLAN C — CODEX EXECUTION PROMPT

Bekerja hanya di folder:

E:\Projects\ULP_Project

Mode yang dipakai harus Work locally, bukan New worktree.

Branch aktif harus:

progress8-plan-c-snapshot-processing

Baca dulu file berikut sebelum mengubah kode:

- AGENTS.md
- docs/progress8/00_PROGRESS8_PLAN_C_OVERVIEW.md
- docs/progress8/01_PLAN_C_ARCHITECTURE.md
- docs/progress8/02_PLAN_C_ROUTES.md
- docs/progress8/03_PLAN_C_STORAGE_APPEND_ONLY.md
- docs/progress8/04_YOLO_AI_GEOMETRY_POLICY.md
- docs/progress8/05_UI_UX_CAPTURE_RESULT_RULES.md
- docs/progress8/06_CODEX_EXECUTION_PROMPT.md
- docs/progress8/07_ACCEPTANCE_CHECKLIST.md
- .codex/progress8_master_context.json
- .codex/progress8_route_contract.json
- .codex/progress8_storage_contract.json
- .codex/progress8_guardrails.json
- .codex/progress8_acceptance_contract.json
- .codex/progress8_task_files.json
- .codex/progress8_ui_contract.json
- .codex/progress8_codex_launch_profile.json

Tugas utama:

Implementasikan Progress 8 Plan C sebagai sistem baru berbasis snapshot/manual capture + backend processing.

Plan C adalah jalur final laporan akhir magang riset. Plan C bukan realtime.

Jangan lakukan ini:

- Jangan membuat folder project baru.
- Jangan memakai git worktree.
- Jangan menambal /field-camera lama.
- Jangan menghapus Plan A dan Plan B.
- Jangan memakai YOLO-FIRST.
- Jangan memakai AI realtime switch.
- Jangan membuat realtime detection loop.
- Jangan mengubah data/raw, dataset, labels, runs, weights, models, file .pt, file .onnx, atau secret.
- Jangan membuat fake detection, fake GPS, fake bounding box, fake prediction.
- Jangan menjalankan git add .

Buat route baru:

- GET /plan-c
- GET /plan-c/capture/<session_id>
- GET /plan-c/processing/<session_id>
- GET /plan-c/result/<session_id>
- GET /plan-c/map
- GET /plan-c/developer/<session_id>
- POST /api/plan-c/session/start
- POST /api/plan-c/session/tree-anchor
- POST /api/plan-c/session/snapshot
- GET /api/plan-c/session/<session_id>/status
- GET /api/plan-c/session/<session_id>/result

Core flow:

HP capture snapshot -> upload to Flask -> store original.jpg -> run YOLO post-capture -> run optional AI validator -> run Python geometry -> create annotated.jpg -> create result.json -> append CSV/JSONL -> append map marker -> render result page.

Prioritas implementasi:

1. session dan storage stabil,
2. snapshot upload stabil,
3. YOLO/AI fallback tidak crash,
4. geometry dan prediction,
5. spreadsheet CSV/JSONL append-only,
6. map marker append-only,
7. result page minimal berfungsi,
8. developer diagnostics page,
9. frontend animasi 3D ditunda sampai core stabil.

Wajib jalankan acceptance checklist dari:

docs/progress8/07_ACCEPTANCE_CHECKLIST.md
.codex/progress8_acceptance_contract.json

Sebelum mengklaim selesai, tampilkan:

- file yang dibuat/diubah,
- route yang aktif,
- hasil py_compile,
- hasil scripts/plan_c_smoke.py,
- hasil git diff --check,
- hasil git diff --stat,
- hasil git status --short --untracked-files=all.

Jangan klaim selesai jika test belum PASS.
