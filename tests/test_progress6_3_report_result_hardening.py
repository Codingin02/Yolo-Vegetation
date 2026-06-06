from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_3_report_page_has_evidence_sections() -> None:
    html = (ROOT / "src" / "ulp_project" / "templates" / "field_report.html").read_text(encoding="utf-8")
    for label in [
        "Session Evidence",
        "GPS Evidence",
        "Camera/Frame Evidence",
        "AI/Model Evidence",
        "Geometry/Measurement Evidence",
        "Operator Notes",
        "CSV/Map Links",
        "Limitations",
    ]:
        assert label in html


def test_progress6_3_result_page_and_api_do_not_claim_final_without_model(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    page = client.get("/field-result")
    assert page.status_code == 200
    result = client.get("/api/field/latest-result").get_json()
    assert result["model_status"] == "MODEL_NOT_READY"
    assert result["status"] == "MODEL_NOT_READY_NO_FAKE_DETECTION"
    assert result["result_status"] == "MODEL_NOT_READY_NO_AI_DETECTION"
    assert result["zone_status"] == "INSUFFICIENT_DATA"
    assert "CALIBRATION_NOT_READY_CLEARANCE_NOT_FINAL" in result["reason_codes"]
