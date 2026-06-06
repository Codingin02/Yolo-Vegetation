from __future__ import annotations

from pathlib import Path

from ulp_project.yolo_label_audit import (
    audit_yolo_folder,
    compute_box_area_stats,
    detect_class_coverage_risk,
    read_yolo_label_file,
)


def test_read_yolo_label_file_flags_huge_box(tmp_path: Path) -> None:
    label = tmp_path / "sample.txt"
    label.write_text("2 0.5 0.5 0.99 0.99\n", encoding="utf-8")

    result = read_yolo_label_file(label)

    assert result["status"] == "VALID"
    assert result["class_counts"][2] == 1
    assert any(item["code"] == "HUGE_BOX_DOMINANCE" for item in result["warnings"])


def test_audit_yolo_folder_detects_multiclass_not_ready(tmp_path: Path) -> None:
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    for index in range(3):
        (images / f"sample_{index}.jpg").write_bytes(b"jpg")
    (labels / "sample_0.txt").write_text("0 0.5 0.5 0.1 0.1\n", encoding="utf-8")
    (labels / "sample_1.txt").write_text("1 0.5 0.5 0.1 0.1\n", encoding="utf-8")
    (labels / "sample_2.txt").write_text("2 0.5 0.5 0.1 0.1\n", encoding="utf-8")

    result = audit_yolo_folder(images, labels, {0: "struktur_penyangga", 1: "konduktor", 2: "pohon_sono"})

    codes = {item["code"] for item in result["warnings"]}
    assert "CLASS_UNDERREPRESENTED" in codes
    assert "MULTICLASS_NOT_READY" in codes


def test_detect_class_coverage_risk_flags_missing_validation(tmp_path: Path) -> None:
    train = tmp_path / "train"
    val = tmp_path / "val"
    train.mkdir()
    val.mkdir()
    (train / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n2 0.5 0.5 0.1 0.1\n", encoding="utf-8")
    (val / "b.txt").write_text("2 0.5 0.5 0.1 0.1\n", encoding="utf-8")

    result = detect_class_coverage_risk(train, val, min_instances_per_class=2)

    codes = {item["code"] for item in result["warnings"]}
    assert "CLASS_MISSING_IN_VALIDATION" in codes
    assert result["status"] == "MULTICLASS_NOT_READY"


def test_compute_box_area_stats_reports_huge_box(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("2 0.5 0.5 0.95 0.95\n", encoding="utf-8")

    stats = compute_box_area_stats(tmp_path)

    assert stats["huge_box_count"] == 1
    assert any(item["code"] == "HUGE_BOX_DOMINANCE" for item in stats["warnings"])
