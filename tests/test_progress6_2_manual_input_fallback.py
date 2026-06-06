from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress6_2_manual_input_is_operator_fallback_not_ai_detection(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    started = client.post("/api/field/session/start", json={"session_id": "TEST_MANUAL_INPUT"}).get_json()

    result = client.post(
        "/api/field/manual-input",
        json={
            "session_id": started["session_id"],
            "point_id": "V001_pohon_sono",
            "object_type": "pohon_sono",
            "estimated_distance_m": 8,
            "estimated_tree_height_m": 7,
            "estimated_conductor_height_m": 11,
            "obstruction_reason": "backlight parah",
            "operator_notes": "fallback lapangan",
        },
    ).get_json()

    assert result["status"] == "MANUAL_OPERATOR_INPUT_NOT_AI_DETECTION"
    assert result["manual_input_status"] == "MANUAL_OPERATOR_INPUT_NOT_AI_DETECTION"
    assert result["no_fake_detection"] is True
