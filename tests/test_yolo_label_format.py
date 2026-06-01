from pathlib import Path

from ulp_project.yolo_validate import validate_label_file


def test_yolo_width_height_must_be_positive(tmp_path: Path):
    label = tmp_path / "zero_width.txt"
    label.write_text("1 0.5 0.5 0 0.2\n", encoding="utf-8")
    issues, _, _ = validate_label_file(label)
    assert any(issue.issue == "NON_POSITIVE_SIZE" for issue in issues)
