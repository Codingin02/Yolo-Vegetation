from pathlib import Path

from ulp_project.model_handoff import check_model_handoff, verify_model_class_order


def test_model_missing_not_ready(monkeypatch):
    monkeypatch.delenv("ULP_YOLO_MODEL_PATH", raising=False)
    result = check_model_handoff(model_path=Path("missing_best.pt"))
    assert result["model_status"] == "MODEL_NOT_READY"
    assert result["inference_status"] == "SKIPPED_NO_MODEL"


def test_model_path_detected_without_committing_pt(tmp_path):
    model = tmp_path / "best.pt"
    model.write_bytes(b"x" * 2048)
    result = check_model_handoff(model_path=model)
    assert result["model_status"] == "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED"


def test_class_order_mismatch_rejected():
    result = verify_model_class_order({0: "pohon_sono", 1: "konduktor", 2: "struktur_penyangga"})
    assert result["status"] == "MODEL_REJECTED_CLASS_ORDER_MISMATCH"
