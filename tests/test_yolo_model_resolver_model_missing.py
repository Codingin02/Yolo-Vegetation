from __future__ import annotations

from pathlib import Path

from ulp_project.yolo_model_resolver import normalize_yolo_class_name, resolve_yolo_model


def test_yolo_model_resolver_missing_model_is_safe(tmp_path, monkeypatch) -> None:
    missing = tmp_path / "models" / "field" / "best.pt"
    monkeypatch.setenv("ULP_YOLO_MODEL_PATH", str(missing))
    result = resolve_yolo_model()
    assert result["status"] == "MODEL_NOT_READY"
    assert result["not_accuracy_claim"] is True
    assert "download" in result["reason"].lower()


def test_yolo_class_mapping_preserves_pkv_convention() -> None:
    assert normalize_yolo_class_name("P001_struktur_penyangga") == "struktur_penyangga"
    assert normalize_yolo_class_name("k001_konduktor") == "konduktor"
    assert normalize_yolo_class_name("V001_pohon_sono") == "pohon_sono"
