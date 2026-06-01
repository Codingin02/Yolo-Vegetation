"""YOLO label validator for locked class order 0/1/2."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from pathlib import Path

from .classes import CLASS_ORDER, validate_class_id
from .metadata import list_images, list_label_files
from .paths import DEFAULT_POINT, image_dir_for_point, label_dir_for_point


@dataclass
class LabelIssue:
    file: str
    line: int
    issue: str
    detail: str = ""


@dataclass
class ValidationResult:
    image_count: int = 0
    label_count: int = 0
    missing_labels: list[str] = field(default_factory=list)
    orphan_labels: list[str] = field(default_factory=list)
    bad_rows: list[LabelIssue] = field(default_factory=list)
    empty_labels: list[str] = field(default_factory=list)
    class_counts: dict[int, int] = field(default_factory=lambda: {key: 0 for key in CLASS_ORDER})

    @property
    def valid(self) -> bool:
        return not (self.missing_labels or self.orphan_labels or self.bad_rows or self.empty_labels)

    @property
    def status(self) -> str:
        return "VALID" if self.valid else "INVALID"


def _parse_label_line(line: str, path: Path, line_number: int) -> tuple[int, list[float]] | LabelIssue:
    parts = line.strip().split()
    if len(parts) != 5:
        return LabelIssue(str(path), line_number, "BAD_COLUMN_COUNT", f"expected 5 got {len(parts)}")
    try:
        class_id = int(parts[0])
    except ValueError:
        return LabelIssue(str(path), line_number, "BAD_CLASS_ID", parts[0])
    if not validate_class_id(class_id):
        return LabelIssue(str(path), line_number, "CLASS_ID_OUT_OF_RANGE", str(class_id))
    try:
        values = [float(value) for value in parts[1:]]
    except ValueError:
        return LabelIssue(str(path), line_number, "BAD_FLOAT", " ".join(parts[1:]))
    x_center, y_center, width, height = values
    if not all(0.0 <= value <= 1.0 for value in values):
        return LabelIssue(str(path), line_number, "COORDINATE_OUT_OF_RANGE", " ".join(parts[1:]))
    if width <= 0.0 or height <= 0.0:
        return LabelIssue(str(path), line_number, "NON_POSITIVE_SIZE", f"{width} {height}")
    return class_id, [x_center, y_center, width, height]


def validate_label_file(path: Path, allow_empty: bool = False) -> tuple[list[LabelIssue], dict[int, int], bool]:
    issues: list[LabelIssue] = []
    counts = {key: 0 for key in CLASS_ORDER}
    if not path.exists():
        return [LabelIssue(str(path), 0, "LABEL_FILE_NOT_FOUND")], counts, False
    content = path.read_text(encoding="utf-8").splitlines()
    non_empty_lines = [line for line in content if line.strip()]
    if not non_empty_lines:
        return ([], counts, True) if allow_empty else ([], counts, False)
    for line_number, line in enumerate(content, start=1):
        if not line.strip():
            continue
        parsed = _parse_label_line(line, path, line_number)
        if isinstance(parsed, LabelIssue):
            issues.append(parsed)
        else:
            class_id, _ = parsed
            counts[class_id] += 1
    return issues, counts, True


def validate_dataset(
    image_dir: Path,
    label_dir: Path,
    allow_missing: bool = False,
    allow_empty: bool = False,
) -> ValidationResult:
    images = list_images(image_dir)
    labels = [path for path in list_label_files(label_dir) if path.name.lower() != "classes.txt"]
    image_stems = {path.stem for path in images}
    label_stems = {path.stem for path in labels}

    result = ValidationResult(image_count=len(images), label_count=len(labels))
    missing = sorted(image_stems - label_stems)
    result.missing_labels = [] if allow_missing else missing
    result.orphan_labels = sorted(label_stems - image_stems)

    for label_path in labels:
        issues, counts, has_rows = validate_label_file(label_path, allow_empty=allow_empty)
        result.bad_rows.extend(issues)
        if not has_rows and not allow_empty:
            result.empty_labels.append(label_path.name)
        for class_id, count in counts.items():
            result.class_counts[class_id] += count
    return result


def write_validation_manifest(result: ValidationResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["category", "file", "line", "issue", "detail"])
        for stem in result.missing_labels:
            writer.writerow(["missing_label", f"{stem}.txt", "", "MISSING_LABEL", ""])
        for stem in result.orphan_labels:
            writer.writerow(["orphan_label", f"{stem}.txt", "", "ORPHAN_LABEL", ""])
        for filename in result.empty_labels:
            writer.writerow(["empty_label", filename, "", "EMPTY_LABEL", ""])
        for issue in result.bad_rows:
            writer.writerow(["bad_row", issue.file, issue.line, issue.issue, issue.detail])


def format_summary(result: ValidationResult) -> str:
    lines = [
        f"status: {result.status}",
        f"images: {result.image_count}",
        f"labels: {result.label_count}",
        f"missing_labels: {len(result.missing_labels)}",
        f"orphan_labels: {len(result.orphan_labels)}",
        f"bad_rows: {len(result.bad_rows)}",
        f"empty_labels: {len(result.empty_labels)}",
        "class_counts:",
    ]
    for class_id, name in CLASS_ORDER.items():
        lines.append(f"  {class_id} {name}: {result.class_counts.get(class_id, 0)}")
    if not result.valid:
        lines.append("result: LABELS_NOT_READY")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate YOLO labels without touching images.")
    parser.add_argument("--point", default=DEFAULT_POINT)
    parser.add_argument("--image-dir", type=Path)
    parser.add_argument("--label-dir", type=Path)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    image_dir = args.image_dir or image_dir_for_point(args.point)
    label_dir = args.label_dir or label_dir_for_point(args.point)
    result = validate_dataset(
        image_dir=image_dir,
        label_dir=label_dir,
        allow_missing=args.allow_missing,
        allow_empty=args.allow_empty,
    )
    print(format_summary(result))
    if args.manifest:
        write_validation_manifest(result, args.manifest)
        print(f"manifest: {args.manifest}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
