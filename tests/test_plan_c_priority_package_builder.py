from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_roboflow_priority_package import build_roboflow_priority_package  # noqa: E402
from ulp_project.plan_c_yolov8_priority_review_package import build_yolov8_priority_review_package  # noqa: E402


def test_roboflow_package_created_in_runtime_folder(tmp_path: Path) -> None:
    image = tmp_path / "pohon.jpg"
    image.write_bytes(b"dummy-image")
    rows = [_row(image, "pohon_sono")]
    result = build_roboflow_priority_package(mode="build", rows=rows, output_root=tmp_path / "roboflow")
    assert result["status"] == "ROBOFLOW_PRIORITY_PACKAGE_CREATED_REVIEW_ONLY"
    package_root = Path(result["package_root"])
    assert (package_root / "data.yaml").exists()
    assert (package_root / "README_ROBOFLOW_REVIEW.md").exists()
    assert (package_root / "ATTRIBUTION.csv").exists()
    assert result["not_final_training_dataset"] is True


def test_yolov8_review_package_is_not_final_dataset(tmp_path: Path) -> None:
    image = tmp_path / "line.jpg"
    image.write_bytes(b"dummy-image")
    rows = [_row(image, "konduktor")]
    result = build_yolov8_priority_review_package(mode="build", rows=rows, output_root=tmp_path / "yolo")
    assert result["status"] == "YOLOV8_PRIORITY_REVIEW_PACKAGE_CREATED_NOT_FINAL_DATASET"
    package_root = Path(result["package_root"])
    assert (package_root / "data.yaml").exists()
    assert (package_root / "README_REVIEW_ONLY.md").exists()
    assert result["not_final_training_dataset"] is True


def _row(image: Path, target_class: str) -> dict[str, str]:
    status = {
        "pohon_sono": "ACCEPT_POSITIVE_POHON_SONO_REFERENCE",
        "konduktor": "ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION",
        "struktur_penyangga": "ACCEPT_STRUCTURE_REFERENCE",
    }[target_class]
    return {
        "source_site": "unit-test",
        "source_page_url": "https://commons.wikimedia.org/wiki/File:test.jpg",
        "image_url": "https://upload.wikimedia.org/test.jpg",
        "local_path": str(image),
        "target_class": target_class,
        "accepted_status": status,
        "license": "CC BY-SA 4.0",
        "author": "Tester",
        "attribution": "Tester / CC BY-SA",
    }
