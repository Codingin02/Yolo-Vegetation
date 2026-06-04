from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_1_labeling import parse_yolo_label_line, validate_label_export


def test_progress6_1_parse_yolo_label_line() -> None:
    assert parse_yolo_label_line("2 0.5 0.5 0.25 0.30")["status"] == "VALID"
    assert parse_yolo_label_line("3 0.5 0.5 0.25 0.30")["status"] == "CLASS_ID_OUT_OF_RANGE"
    assert parse_yolo_label_line("2 1.5 0.5 0.25 0.30")["status"] == "COORDINATE_OUT_OF_RANGE"
    assert parse_yolo_label_line("2 0.5 0.5 0 0.30")["status"] == "NON_POSITIVE_SIZE"


def test_progress6_1_validate_temp_export_counts_classes(tmp_path: Path) -> None:
    image = tmp_path / "images" / "V001_a.jpg"
    label = tmp_path / "labels" / "V001_a.txt"
    image.parent.mkdir()
    label.parent.mkdir()
    image.write_bytes(b"jpg")
    label.write_text("2 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    result = validate_label_export([tmp_path])

    assert result["status"] == "LABEL_EXPORT_VALID"
    assert result["class_counts"]["pohon_sono"] == 1
    assert result["no_fake_label"] is True
