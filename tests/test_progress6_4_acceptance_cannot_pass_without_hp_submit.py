from __future__ import annotations

from ulp_project.field_acceptance_validation import validate_acceptance_payload


def test_progress6_4_acceptance_cannot_pass_without_hp_submit() -> None:
    result = validate_acceptance_payload({"acceptance_id": "NO_SUBMIT"})
    assert result["acceptance_status"] == "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"
    assert "submit_acceptance_from_hp" in result["missing_requirements"]
