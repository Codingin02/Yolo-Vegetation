from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_1_labeling import validate_label_export
from ulp_project.progress6_2_training import progress6_2_export_audit, validate_export_class_order


def test_progress6_2_invalid_class_order_fails(tmp_path: Path) -> None:
    (tmp_path / "classes.txt").write_text("pole\ncable\ntree\n", encoding="utf-8")
    result = validate_export_class_order([tmp_path])

    assert result["status"] == "CLASS_ORDER_INVALID_REVIEW_REQUIRED"
    assert result["class_order_ok"] is False


def test_progress6_2_bbox_outside_image_is_invalid(tmp_path: Path) -> None:
    image = tmp_path / "images" / "sample.jpg"
    label = tmp_path / "labels" / "sample.txt"
    image.parent.mkdir()
    label.parent.mkdir()
    image.write_bytes(b"jpg")
    label.write_text("2 0.95 0.5 0.2 0.2\n", encoding="utf-8")

    result = validate_label_export([tmp_path])

    assert result["status"] == "LABEL_EXPORT_INVALID_REVIEW_NEEDED"
    assert result["issues"][0]["issue"] == "BBOX_EXTENDS_OUTSIDE_IMAGE"


def test_progress6_2_audit_reports_bbox_warning_without_fake_label(tmp_path: Path) -> None:
    image = tmp_path / "images" / "sample.jpg"
    label = tmp_path / "labels" / "sample.txt"
    image.parent.mkdir()
    label.parent.mkdir()
    image.write_bytes(b"jpg")
    label.write_text("2 0.5 0.5 0.01 0.01\n", encoding="utf-8")

    result = progress6_2_export_audit([tmp_path])

    assert result["status"] == "PROGRESS_6_2_LABEL_EXPORT_VALID_INSUFFICIENT_DATA_FOR_REAL_TRAINING"
    assert result["validation"]["warning_count"] == 1
    assert result["no_fake_label"] is True
