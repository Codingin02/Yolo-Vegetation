# CODEX PROMPT — Progress 8 Plan C

Baca:
- AGENTS.md
- .codex/progress8_plan_c_master_context.json
- .codex/progress8_route_storage_contract.json
- .codex/progress8_acceptance_contract.json

Implementasikan Plan C sebagai sistem baru.

Jangan menambal Plan A/B. Jangan menghapus Plan A/B. Jangan memperbaiki UI realtime lama. Jangan gunakan YOLO-FIRST. Jangan gunakan AI realtime switch.

Buat route baru /plan-c dan /api/plan-c.

Core flow:
HP capture snapshot -> upload to Flask -> store original.jpg -> run YOLO post-capture -> run optional AI validator -> run Python geometry -> create annotated.jpg -> create result.json -> append CSV/JSONL -> append map marker -> render result page.

Prioritas:
1. backend/session/storage stabil,
2. snapshot upload stabil,
3. YOLO/AI fallback tidak crash,
4. spreadsheet/map append-only,
5. result page minimal berfungsi,
6. frontend animasi 3D ditunda.

Jalankan acceptance tests dari .codex/progress8_acceptance_contract.json. Jangan klaim selesai jika test belum PASS.
