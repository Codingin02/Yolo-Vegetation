from __future__ import annotations

from ulp_project.progress_status_consistency import build_status_consistency_audit


def test_progress6_3_status_consistency_does_not_confuse_pipeline_with_real_model() -> None:
    audit = build_status_consistency_audit()
    assert audit["no_fake_detection"] is True
    assert audit["class_order_status"] == "CLASS_ORDER_LOCKED"
    if audit["runtime_model_status"] == "MODEL_NOT_READY":
        assert audit["status_consistency"] in {
            "PIPELINE_READY_BUT_REAL_MODEL_NOT_AVAILABLE",
            "DATASET_PIPELINE_READY_TRAINING_OUTPUT_NOT_FOUND",
            "MODEL_NOT_READY_STATUS_CONSISTENT",
        }
        assert "REAL_MODEL" not in audit["progress_6_1_precise_status"] or audit["bestpt_status"] != "BESTPT_NOT_FOUND"
