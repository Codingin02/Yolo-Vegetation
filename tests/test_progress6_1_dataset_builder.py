from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_1_labeling import build_yolo_dataset


def _pair(root: Path, index: int, class_id: int = 2) -> None:
    image = root / "images" / f"sample_{index}.jpg"
    label = root / "labels" / f"sample_{index}.txt"
    image.parent.mkdir(parents=True, exist_ok=True)
    label.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(f"jpg-{index}".encode("ascii"))
    label.write_text(f"{class_id} 0.5 0.5 0.2 0.2\n", encoding="utf-8")


def test_progress6_1_dataset_builder_dry_run_and_build(tmp_path: Path) -> None:
    export = tmp_path / "export"
    for index in range(5):
        _pair(export, index)
    output = tmp_path / "field_multiclass_v1"

    dry = build_yolo_dataset(mode="dry-run", output_dir=output, export_roots=[export])
    built = build_yolo_dataset(mode="build", output_dir=output, export_roots=[export])

    assert dry["status"] == "DATASET_BUILD_DRY_RUN_READY"
    assert built["status"] == "DATASET_BUILD_READY"
    assert built["split_policy"] == "TEST_SPLIT_SKIPPED_SMALL_DATASET"
    assert (output / "data.yaml").is_file()
    assert (output / "dataset_manifest.csv").is_file()
