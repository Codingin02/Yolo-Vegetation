# 06 — Codex Execution Prompt Progress 8 Plan C

Baca AGENTS.md dan seluruh file berikut sebelum mengubah kode:
- docs/progress8/00_PROGRESS8_PLAN_C_OVERVIEW.md
- docs/progress8/01_PLAN_C_ARCHITECTURE.md
- docs/progress8/02_PLAN_C_ROUTES.md
- docs/progress8/03_PLAN_C_STORAGE_APPEND_ONLY.md
- docs/progress8/04_YOLO_AI_GEOMETRY_POLICY.md
- docs/progress8/05_UI_UX_CAPTURE_RESULT_RULES.md
- .codex/progress8_master_context.json
- .codex/progress8_route_contract.json
- .codex/progress8_storage_contract.json
- .codex/progress8_guardrails.json
- .codex/progress8_acceptance_contract.json
- .codex/progress8_task_files.json
- .codex/progress8_ui_contract.json

Implementasikan Progress 8 Plan C sebagai sistem baru di folder E:\Projects\ULP_Project.

Jangan gunakan git worktree.
Jangan membuat folder project baru.
Jangan menambal /field-camera lama.
Jangan menghapus Plan A atau Plan B.
Jangan edit dataset/raw/labels/runs/weights/models.
Jangan gunakan YOLO-FIRST.
Jangan gunakan AI realtime switch.
Jangan realtime detection loop.
Jangan fake detection, fake GPS, fake bounding box, atau fake prediction.

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

Prioritas:
1. session dan storage,
2. snapshot upload,
3. YOLO/AI fallback,
4. geometry dan prediction,
5. append CSV/JSONL/map,
6. result page minimal,
7. frontend animasi 3D nanti setelah core stabil.

Jalankan acceptance checklist sebelum klaim selesai.
