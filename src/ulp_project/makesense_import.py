"""Dry-run-first importer for makeSense.ai YOLO exports."""

from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .metadata import list_images, list_label_files
from .paths import DEFAULT_POINT, METADATA_DIR, export_dir_for_point, image_dir_for_point, label_dir_for_point
from .yolo_validate import validate_label_file


@dataclass
class ImportSummary:
    images_found: int = 0
    labels_found_in_export: int = 0
    matched_labels: int = 0
    missing_labels: list[str] = field(default_factory=list)
    orphan_labels: list[str] = field(default_factory=list)
    copied_labels: list[str] = field(default_factory=list)
    skipped_existing_labels: list[str] = field(default_factory=list)
    invalid_export_labels: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.invalid_export_labels:
            return "EXPORT_LABELS_INVALID"
        if self.missing_labels:
            return "LABELS_NOT_READY"
        return "READY"


def _label_files(export_dir: Path) -> list[Path]:
    return [path for path in list_label_files(export_dir) if path.name.lower() != "classes.txt"]


def import_makesense_export(
    export_dir: Path,
    image_dir: Path,
    output_label_dir: Path,
    mode: str = "dry-run",
    overwrite: bool = False,
) -> ImportSummary:
    if mode not in {"dry-run", "copy"}:
        raise ValueError("mode must be dry-run or copy")

    images = list_images(image_dir)
    labels = _label_files(export_dir)
    image_stems = {path.stem for path in images}
    label_by_stem = {path.stem: path for path in labels}
    label_stems = set(label_by_stem)

    summary = ImportSummary(
        images_found=len(images),
        labels_found_in_export=len(labels),
        matched_labels=len(image_stems & label_stems),
        missing_labels=sorted(image_stems - label_stems),
        orphan_labels=sorted(label_stems - image_stems),
    )

    for stem in sorted(image_stems & label_stems):
        source = label_by_stem[stem]
        issues, _, has_rows = validate_label_file(source, allow_empty=False)
        if issues or not has_rows:
            summary.invalid_export_labels.append(source.name)
            continue
        target = output_label_dir / source.name
        if target.exists() and not overwrite:
            summary.skipped_existing_labels.append(source.name)
            continue
        if mode == "copy":
            output_label_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            summary.copied_labels.append(source.name)

    return summary


def write_import_manifest(summary: ImportSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["category", "filename"])
        for name in summary.missing_labels:
            writer.writerow(["missing_label", f"{name}.txt"])
        for name in summary.orphan_labels:
            writer.writerow(["orphan_label", f"{name}.txt"])
        for name in summary.invalid_export_labels:
            writer.writerow(["invalid_export_label", name])
        for name in summary.skipped_existing_labels:
            writer.writerow(["skipped_existing_label", name])
        for name in summary.copied_labels:
            writer.writerow(["copied_label", name])


def format_summary(summary: ImportSummary) -> str:
    return "\n".join(
        [
            f"status: {summary.status}",
            f"images_found: {summary.images_found}",
            f"labels_found_in_export: {summary.labels_found_in_export}",
            f"matched_labels: {summary.matched_labels}",
            f"missing_labels: {len(summary.missing_labels)}",
            f"orphan_labels: {len(summary.orphan_labels)}",
            f"copied_labels: {len(summary.copied_labels)}",
            f"skipped_existing_labels: {len(summary.skipped_existing_labels)}",
            f"invalid_export_labels: {len(summary.invalid_export_labels)}",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import makeSense.ai YOLO labels, dry-run by default.")
    parser.add_argument("--point", default=DEFAULT_POINT)
    parser.add_argument("--export-dir", type=Path)
    parser.add_argument("--image-dir", type=Path)
    parser.add_argument("--output-label-dir", type=Path)
    parser.add_argument("--mode", choices=["dry-run", "copy"], default="dry-run")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--no-manifest", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    export_dir = args.export_dir or export_dir_for_point(args.point)
    image_dir = args.image_dir or image_dir_for_point(args.point)
    output_label_dir = args.output_label_dir or label_dir_for_point(args.point)

    summary = import_makesense_export(
        export_dir=export_dir,
        image_dir=image_dir,
        output_label_dir=output_label_dir,
        mode=args.mode,
        overwrite=args.overwrite,
    )
    print(format_summary(summary))
    if not args.no_manifest:
        manifest = args.manifest or METADATA_DIR / f"makesense_import_{args.point}.csv"
        write_import_manifest(summary, manifest)
        print(f"manifest: {manifest}")
    if summary.invalid_export_labels:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
