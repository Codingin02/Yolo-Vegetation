from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_2_training import progress6_2_dataset_build_status


def _pair(root: Path, index: int) -> None:
    image = root / "images" / f"sample_{index}.jpg"
    label = root / "labels" / f"sample_{index}.txt"
    image.parent.mkdir(parents=True, exist_ok=True)
    label.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(f"jpg-{index}".encode("ascii"))
    label.write_text("2 0.5 0.5 0.2 0.2\n", encoding="utf-8")


def test_progress6_2_dataset_build_from_valid_export(tmp_path: Path) -> None:
    export = tmp_path / "export"
    for index in range(5):
        _pair(export, index)
    output = tmp_path / "dataset"

    result = progress6_2_dataset_build_status(mode="build", export_roots=[export], output_dir=output)

    assert result["status"] == "DATASET_BUILD_READY"
    assert result["total_pairs"] == 5
    assert (output / "data.yaml").is_file()
    assert (output / "dataset_manifest.csv").is_file()
