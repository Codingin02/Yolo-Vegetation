from pathlib import Path

from ulp_project.system_status import collect_project_status, render_status_text


def write_classes(root: Path) -> None:
    config = root / "configs" / "classes.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "names:\n"
        "  0: struktur_penyangga\n"
        "  1: konduktor\n"
        "  2: pohon_sono\n",
        encoding="utf-8",
    )


def test_collect_project_status_waits_for_labels(tmp_path: Path):
    write_classes(tmp_path)
    image_dir = tmp_path / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "images_selected"
    label_dir = tmp_path / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "labels_selected"
    export_dir = tmp_path / "data" / "exports" / "make_sense" / "V001_pohon_sono"
    image_dir.mkdir(parents=True)
    label_dir.mkdir(parents=True)
    export_dir.mkdir(parents=True)
    (image_dir / "V001_sample.jpg").write_bytes(b"placeholder")

    status = collect_project_status(tmp_path)

    assert status["class_order_ok"] is True
    assert status["images_selected"]["image_count"] == 1
    assert status["labels_selected"]["status"] == "WAITING_FOR_LABELS"
    assert status["overall_status"] == "WAITING_FOR_LABELS"
    assert "WAITING_FOR_LABELS" in render_status_text(status)
