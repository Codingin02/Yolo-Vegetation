from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.classes import CLASS_ORDER  # noqa: E402
from ulp_project.metadata import IMAGE_EXTENSIONS  # noqa: E402
from ulp_project.paths import (  # noqa: E402
    DEFAULT_IMAGE_DIR,
    DEFAULT_LABEL_DIR,
    FIELD_DATA_YAML,
    MAKESENSE_EXPORT_DIR,
    PROJECT_ROOT,
)

EXPECTED_BRANCH = "system-finalization-no-label-touch"


@dataclass(frozen=True)
class Phase3Readiness:
    branch: str
    branch_ok: bool
    class_order_ok: bool
    images_selected_exists: bool
    image_count: int
    labels_selected_exists: bool
    label_count: int
    missing_label_count: int
    orphan_label_count: int
    labels_ready: bool
    export_exists: bool
    export_label_count: int
    data_yaml_exists: bool
    import_status: str
    build_dataset_status: str
    train_dry_run_status: str
    final_status: str


def current_branch(root: Path = PROJECT_ROOT) -> str:
    completed = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.stdout.strip()


def read_class_order(config_path: Path) -> dict[int, str]:
    if not config_path.exists():
        return {}
    parsed: dict[int, str] = {}
    for line in config_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*(\d+)\s*:\s*([A-Za-z0-9_]+)\s*$", line)
        if match:
            parsed[int(match.group(1))] = match.group(2)
    return parsed


def count_images(image_dir: Path) -> tuple[int, set[str]]:
    if not image_dir.exists():
        return 0, set()
    images = [
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return len(images), {path.stem for path in images}


def count_labels(label_dir: Path) -> tuple[int, set[str]]:
    if not label_dir.exists():
        return 0, set()
    labels = [
        path
        for path in label_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".txt" and path.name.lower() != "classes.txt"
    ]
    return len(labels), {path.stem for path in labels}


def count_export_labels(export_dir: Path) -> int:
    if not export_dir.exists():
        return 0
    return sum(
        1
        for path in export_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".txt" and path.name.lower() != "classes.txt"
    )


def evaluate_readiness(
    root: Path = PROJECT_ROOT,
    branch: str | None = None,
    image_dir: Path | None = None,
    label_dir: Path | None = None,
    export_dir: Path | None = None,
    data_yaml: Path | None = None,
    class_config: Path | None = None,
) -> Phase3Readiness:
    image_dir = image_dir or DEFAULT_IMAGE_DIR
    label_dir = label_dir or DEFAULT_LABEL_DIR
    export_dir = export_dir or MAKESENSE_EXPORT_DIR
    data_yaml = data_yaml or FIELD_DATA_YAML
    class_config = class_config or (root / "configs" / "classes.yaml")
    branch = branch if branch is not None else current_branch(root)

    image_count, image_stems = count_images(image_dir)
    label_count, label_stems = count_labels(label_dir)
    missing_label_count = len(image_stems - label_stems)
    orphan_label_count = len(label_stems - image_stems)
    labels_ready = image_count > 0 and missing_label_count == 0 and orphan_label_count == 0

    export_label_count = count_export_labels(export_dir)
    export_exists = export_dir.exists()
    data_yaml_exists = data_yaml.exists()
    class_order_ok = read_class_order(class_config) == CLASS_ORDER
    branch_ok = branch == EXPECTED_BRANCH

    if labels_ready:
        import_status = "SKIPPED_LABELS_ALREADY_READY"
    elif export_label_count > 0:
        import_status = "READY_FOR_LABEL_IMPORT"
    else:
        import_status = "BLOCKED_WAITING_FOR_MAKESENSE_EXPORT"

    build_dataset_status = "READY_FOR_DATASET_BUILD" if labels_ready else "BLOCKED_WAITING_FOR_LABELS"
    train_dry_run_status = "READY_FOR_TRAIN_DRY_RUN" if data_yaml_exists else "BLOCKED_DATASET_NOT_READY"

    final_status = (
        "PHASE3_READY_FOR_LABEL_IMPORT"
        if branch_ok and class_order_ok and image_count > 0 and export_label_count > 0 and not labels_ready
        else "PHASE3_READY_WAITING_FOR_LABELS"
    )

    return Phase3Readiness(
        branch=branch,
        branch_ok=branch_ok,
        class_order_ok=class_order_ok,
        images_selected_exists=image_dir.exists(),
        image_count=image_count,
        labels_selected_exists=label_dir.exists(),
        label_count=label_count,
        missing_label_count=missing_label_count,
        orphan_label_count=orphan_label_count,
        labels_ready=labels_ready,
        export_exists=export_exists,
        export_label_count=export_label_count,
        data_yaml_exists=data_yaml_exists,
        import_status=import_status,
        build_dataset_status=build_dataset_status,
        train_dry_run_status=train_dry_run_status,
        final_status=final_status,
    )


def format_readiness(readiness: Phase3Readiness) -> str:
    lines = [
        f"branch: {readiness.branch}",
        f"branch_ok: {readiness.branch_ok}",
        f"class_order_ok: {readiness.class_order_ok}",
        f"images_selected_exists: {readiness.images_selected_exists}",
        f"image_count: {readiness.image_count}",
        f"labels_selected_exists: {readiness.labels_selected_exists}",
        f"label_count: {readiness.label_count}",
        f"missing_label_count: {readiness.missing_label_count}",
        f"orphan_label_count: {readiness.orphan_label_count}",
        f"labels_ready: {readiness.labels_ready}",
        f"export_exists: {readiness.export_exists}",
        f"export_label_count: {readiness.export_label_count}",
        f"data_yaml_exists: {readiness.data_yaml_exists}",
        f"import_status: {readiness.import_status}",
        f"build_dataset_status: {readiness.build_dataset_status}",
        f"train_dry_run_status: {readiness.train_dry_run_status}",
        readiness.final_status,
    ]
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 3 read-only readiness gate.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--image-dir", type=Path)
    parser.add_argument("--label-dir", type=Path)
    parser.add_argument("--export-dir", type=Path)
    parser.add_argument("--data-yaml", type=Path)
    parser.add_argument("--class-config", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    readiness = evaluate_readiness(
        root=args.root,
        image_dir=args.image_dir,
        label_dir=args.label_dir,
        export_dir=args.export_dir,
        data_yaml=args.data_yaml,
        class_config=args.class_config,
    )
    print(format_readiness(readiness))
    if not readiness.branch_ok or not readiness.class_order_ok or readiness.image_count == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
