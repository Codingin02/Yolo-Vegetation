from __future__ import annotations

import json
from pathlib import Path

from ulp_project.field_trial_evidence import build_field_trial_evidence_pack, load_latest_hp_result, record_hp_result


def test_evidence_pack_dry_run_keeps_hp_physical_pending(tmp_path: Path) -> None:
    result = build_field_trial_evidence_pack(evidence_dir=tmp_path, dry_run=True)

    assert result["status"] == "FIELD_TRIAL_EVIDENCE_READY"
    assert result["evidence_written"] is False
    assert result["hp_physical_confirmation_status"] == "HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION"
    assert result["model_status"] == "MODEL_NOT_READY"
    assert "HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION" in result["known_blockers"]
    assert "CALIBRATION_NOT_READY_EXPECTED" in result["known_blockers"]


def test_hp_result_recording_sanitizes_screenshot_and_writes_runtime_json(tmp_path: Path) -> None:
    result = record_hp_result(
        {
            "operator_name": "operator",
            "network_type": "paket_data",
            "public_url_opened": True,
            "server_connection_ok": True,
            "camera_ok": True,
            "gps_ok": False,
            "manual_prediction_ok": True,
            "snapshot_report_ok": True,
            "map_report_ok": True,
            "screenshot_base64": "SHOULD_NOT_BE_STORED",
        },
        evidence_dir=tmp_path,
    )

    path = Path(result["path"])
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "HP_RESULT_RECORDED"
    assert result["hp_physical_confirmation_status"] == "HP_CONFIRMED"
    assert "screenshot_base64" not in stored
    assert str(path).startswith(str(tmp_path))
    assert load_latest_hp_result(tmp_path)["hp_physical_confirmation_status"] == "HP_CONFIRMED"
