from __future__ import annotations

from pathlib import Path

from ulp_project.growth_prediction_runtime import predict_growth_prior

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_6_growth_prior_no_fake_final_claim() -> None:
    prediction = predict_growth_prior({"point_id": "V001_pohon_sono", "clearance_m": 4.5})
    text = "\n".join(
        [
            (ROOT / "src" / "ulp_project" / "growth_prediction_runtime.py").read_text(encoding="utf-8"),
            (ROOT / "src" / "ulp_project" / "pohon_sono_growth_model.py").read_text(encoding="utf-8"),
        ]
    )
    assert prediction["source_status"] == "PROXY_NOT_FIELD_OBSERVED"
    assert prediction["no_fake_final_claim"] is True
    assert "bukan final claim" in text.lower() or "not_final_accuracy_claim" in text
    assert "SURVEY_GRADE" not in text
