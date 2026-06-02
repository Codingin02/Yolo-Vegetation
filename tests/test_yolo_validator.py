from pathlib import Path

from ulp_project.yolo_validate import validate_dataset, validate_label_file


def test_valid_yolo_label_file(tmp_path: Path):
    label = tmp_path / "sample.txt"
    label.write_text("2 0.5 0.5 0.2 0.3\n", encoding="utf-8")
    issues, counts, has_rows = validate_label_file(label)
    assert issues == []
    assert counts[2] == 1
    assert has_rows is True


def test_invalid_class_and_coordinate(tmp_path: Path):
    label = tmp_path / "bad.txt"
    label.write_text("4 1.2 0.5 0.2 0.3\n", encoding="utf-8")
    issues, _, has_rows = validate_label_file(label)
    assert has_rows is True
    assert issues


def test_missing_label_is_invalid(tmp_path: Path):
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    (images / "V001_a.jpg").write_bytes(b"fake")
    result = validate_dataset(images, labels)
    assert not result.valid
    assert result.missing_labels == ["V001_a"]


def test_importer_dry_run_does_not_copy_label(tmp_path: Path):
    from ulp_project.makesense_import import import_makesense_export

    image_dir = tmp_path / "images"
    export_dir = tmp_path / "export"
    label_dir = tmp_path / "labels"
    image_dir.mkdir()
    export_dir.mkdir()
    label_dir.mkdir()

    (image_dir / "V001_sample.jpg").write_bytes(b"placeholder")
    (export_dir / "V001_sample.txt").write_text("2 0.5 0.5 0.1 0.1\n", encoding="utf-8")

    summary = import_makesense_export(export_dir, image_dir, label_dir, mode="dry-run")

    assert summary.matched_labels == 1
    assert summary.copied_labels == []
    assert not (label_dir / "V001_sample.txt").exists()
