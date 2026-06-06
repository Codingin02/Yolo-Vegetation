from __future__ import annotations

import csv
import time
from pathlib import Path

from ulp_project.field_session_runtime import PROGRESS5_4_REPORT_CSV, SESSION_SMOKE_REPORT_CSV
from ulp_project.flask_app import create_app


def test_progress6_5_smoke_rows_do_not_enter_live_csv_and_duplicate_key_once(tmp_path: Path) -> None:
    key = f"P65_CSV_SPLIT_{int(time.time() * 1000)}"
    client = create_app(runtime_root=tmp_path).test_client()
    start = client.post(
        "/api/field/session/start",
        json={"session_id": f"P65_CSV_{int(time.time())}", "source_mode": "SMOKE_TEST", "operator_name": "operator-smoke"},
    ).get_json()
    payload = {"session_id": start["session_id"], "source_mode": "SMOKE_TEST", "idempotency_key": key}

    client.post("/api/field/session/shutter", json=payload)
    client.post("/api/field/session/shutter", json=payload)

    assert _count_key(SESSION_SMOKE_REPORT_CSV, key) == 1
    assert _count_key(PROGRESS5_4_REPORT_CSV, key) == 0


def _count_key(path: Path, key: str) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for row in csv.DictReader(handle) if row.get("idempotency_key") == key)
