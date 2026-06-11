"""Build Roboflow review packages from legal priority manifests."""

from __future__ import annotations

import csv
from datetime import datetime
import shutil
from pathlib import Path
from typing import Any
import zipfile

from .plan_c_priority_acquisition_config import CLASS_MAPPING, ROBOFLOW_PACKAGE_ROOT, ensure_priority_acquisition_dirs
from .plan_c_priority_pseudo_labeler import empty_label_for_manual_review
from .plan_c_priority_source_manifest import accepted_for_packaging, latest_manifest_rows


def build_roboflow_priority_package(
    *,
    mode: str = "dry-run",
    rows: list[dict[str, Any]] | None = None,
    output_root: Path | None = None,
    make_zip: bool = False,
) -> dict[str, Any]:
    ensure_priority_acquisition_dirs()
    rows = accepted_for_packaging(rows if rows is not None else latest_manifest_rows())
    local_rows = [row for row in rows if row.get("local_path") and Path(str(row.get("local_path"))).exists()]
    if mode == "dry-run":
        return {
            "ok": True,
            "status": "ROBOFLOW_PRIORITY_PACKAGE_DRY_RUN_READY",
            "accepted_manifest_rows": len(rows),
            "local_images_available": len(local_rows),
            "zip_created": False,
        }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = (output_root or ROBOFLOW_PACKAGE_ROOT) / f"plan_c_priority_roboflow_{timestamp}"
    images_dir = root / "images"
    labels_dir = root / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    package_rows: list[dict[str, Any]] = []
    for index, row in enumerate(local_rows):
        source_path = Path(str(row["local_path"]))
        image_name = f"{index:05d}_{source_path.name}"
        image_path = images_dir / image_name
        shutil.copy2(source_path, image_path)
        label_path = labels_dir / (Path(image_name).stem + ".txt")
        empty_label_for_manual_review(label_path)
        package_row = dict(row)
        package_row["package_image"] = str(image_path)
        package_row["package_label"] = str(label_path)
        package_row["review_only"] = "true"
        package_rows.append(package_row)

    _write_manifest(root / "manifest.csv", package_rows)
    _write_attribution(root / "ATTRIBUTION.csv", package_rows)
    _write_data_yaml(root / "data.yaml")
    _write_readme(root / "README_ROBOFLOW_REVIEW.md")
    _write_license_summary(root / "LICENSE_SUMMARY.md", package_rows)
    zip_path = ""
    if make_zip:
        zip_path = str(_zip_package(root))
    return {
        "ok": True,
        "status": "ROBOFLOW_PRIORITY_PACKAGE_CREATED_REVIEW_ONLY",
        "package_root": str(root),
        "image_count": len(package_rows),
        "label_count": len(package_rows),
        "zip_created": bool(zip_path),
        "zip_path": zip_path,
        "not_final_training_dataset": True,
    }


def _write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row.keys()} | {"review_only"})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_attribution(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = ["source_site", "source_page_url", "image_url", "license", "license_url", "author", "attribution", "rights_holder"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_data_yaml(path: Path) -> None:
    lines = ["path: .", "train: images", "val: images", "names:"]
    lines.extend(f"  {index}: {name}" for index, name in CLASS_MAPPING.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_readme(path: Path) -> None:
    path.write_text(
        """# Plan C Priority Roboflow Review Package

Upload this folder to a Roboflow Object Detection project.

Class order:

0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono

All labels are draft review-only. Review every bounding box manually before training. For conductor images, if there are 3 visible cables, create 3 separate `konduktor` boxes, not one wide box. For `pohon_sono`, box the visible target tree, not the whole background. For `struktur_penyangga`, box only utility pole, crossarm, or electrical support structure. Negative samples may stay unlabeled.
""",
        encoding="utf-8",
    )


def _write_license_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        license_name = str(row.get("license") or "")
        counts[license_name] = counts.get(license_name, 0) + 1
    lines = ["# License Summary", "", "Only allowed-license rows should be packaged for Roboflow review.", ""]
    lines.extend(f"- {name or 'missing'}: {count}" for name, count in sorted(counts.items()))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _zip_package(root: Path) -> Path:
    zip_path = root.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in root.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(root.parent))
    return zip_path
