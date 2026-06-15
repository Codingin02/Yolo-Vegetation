from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "data" / "dataset_yolo"
METADATA_DIR = ROOT / "data" / "metadata"
DOCS_DIR = ROOT / "docs" / "progress8"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
FINAL_CLASS_NAMES = {
    0: "struktur_penyangga",
    1: "konduktor",
    2: "pohon_sono",
    3: "pohon_non_sono",
}
REQUIRED_COUNTS = {
    "struktur_penyangga": 100,
    "konduktor": 100,
    "pohon_sono": 100,
}


def main() -> int:
    audit = build_audit()
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = audit["created_at_compact"]
    json_path = METADATA_DIR / f"plan_c_training_dataset_audit_{timestamp}.json"
    md_path = DOCS_DIR / f"PLAN_C_TRAINING_DATASET_AUDIT_{timestamp}.md"
    audit["report_json_path"] = str(json_path)
    audit["report_markdown_path"] = str(md_path)
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown_report(audit), encoding="utf-8")
    summary = {
        "status": audit["status"],
        "ready_for_training": audit["ready_for_training"],
        "image_count": audit["image_count"],
        "label_file_count": audit["label_file_count"],
        "valid_label_lines": audit["valid_label_lines"],
        "invalid_label_lines": audit["invalid_label_lines"],
        "class_counts": audit["class_counts"],
        "recommended_classes": audit["recommended_classes"],
        "report_json_path": str(json_path),
        "report_markdown_path": str(md_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def build_audit() -> dict[str, Any]:
    created_at = datetime.now().isoformat(timespec="seconds")
    roots = _candidate_roots()
    aggregate_class_counts: Counter[str] = Counter()
    aggregate_image_paths: set[str] = set()
    aggregate_label_paths: set[str] = set()
    valid_records: list[dict[str, Any]] = []
    source_summaries: list[dict[str, Any]] = []
    invalid_label_lines = 0
    empty_label_files = 0
    missing_image_for_label = 0
    missing_label_for_image = 0
    duplicate_filenames: dict[str, list[str]] = {}

    for root in roots:
        summary = _audit_source(root)
        source_summaries.append(summary)
        aggregate_class_counts.update(summary["class_counts"])
        aggregate_image_paths.update(summary["image_paths"])
        aggregate_label_paths.update(summary["label_paths"])
        valid_records.extend(summary["valid_records"])
        invalid_label_lines += int(summary["invalid_label_lines"])
        empty_label_files += int(summary["empty_label_files"])
        missing_image_for_label += int(summary["missing_image_for_label"])
        missing_label_for_image += int(summary["missing_label_for_image"])
        duplicate_filenames.update(summary["duplicate_filenames"])

    recommended_classes = [
        name
        for name in ("struktur_penyangga", "konduktor", "pohon_sono")
        if aggregate_class_counts.get(name, 0) >= REQUIRED_COUNTS[name]
    ]
    if aggregate_class_counts.get("pohon_non_sono", 0) >= 100:
        recommended_classes.append("pohon_non_sono")

    ready_for_training = (
        all(aggregate_class_counts.get(name, 0) >= minimum for name, minimum in REQUIRED_COUNTS.items())
        and len(aggregate_image_paths) >= 300
    )
    status = "DATASET_READY_FOR_SYSTEM_C_TRAINING" if ready_for_training else "DATASET_NOT_READY"
    shortfalls = {
        name: max(0, minimum - aggregate_class_counts.get(name, 0))
        for name, minimum in REQUIRED_COUNTS.items()
        if aggregate_class_counts.get(name, 0) < minimum
    }
    if len(aggregate_image_paths) < 300:
        shortfalls["total_valid_images"] = 300 - len(aggregate_image_paths)

    return {
        "status": status,
        "created_at": created_at,
        "created_at_compact": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "candidate_sources": [
            {
                "path": item["path"],
                "image_count": item["image_count"],
                "label_file_count": item["label_file_count"],
                "valid_label_lines": item["valid_label_lines"],
                "class_counts": item["class_counts"],
                "class_mapping": item["class_mapping"],
            }
            for item in source_summaries
        ],
        "image_count": len(aggregate_image_paths),
        "label_file_count": len(aggregate_label_paths),
        "valid_label_lines": sum(aggregate_class_counts.values()),
        "invalid_label_lines": invalid_label_lines,
        "class_counts": dict(sorted(aggregate_class_counts.items())),
        "empty_label_files": empty_label_files,
        "missing_image_for_label": missing_image_for_label,
        "missing_label_for_image": missing_label_for_image,
        "duplicate_filename_count": len(duplicate_filenames),
        "duplicate_filenames": duplicate_filenames,
        "ready_for_training": ready_for_training,
        "recommended_classes": recommended_classes,
        "shortfalls": shortfalls,
        "valid_records": valid_records,
        "class_policy": "0 struktur_penyangga, 1 konduktor, 2 pohon_sono, optional 3 pohon_non_sono jika cukup",
        "no_scraping": True,
        "source_data_modified": False,
    }


def _candidate_roots() -> list[Path]:
    explicit = [
        DATASET_ROOT / "plan_c_ai_detector_v1",
        DATASET_ROOT / "plan_c_final_v1",
        DATASET_ROOT / "00_review_candidates",
        DATASET_ROOT / "00_review_candidates" / "system_c_real_pk_ai_labeling_v1",
        ROOT / "labels_ai_review",
        ROOT / "json_ai_review",
        ROOT / "review",
        ROOT / "exports",
        ROOT / "datasets",
    ]
    discovered: list[Path] = []
    if DATASET_ROOT.exists():
        for candidate in DATASET_ROOT.rglob("*"):
            if candidate.is_dir() and candidate.name == "labels":
                discovered.append(candidate.parent)
    roots: list[Path] = []
    seen: set[Path] = set()
    for root in [*explicit, *discovered]:
        if not root.exists() or not root.is_dir():
            continue
        if root.name.startswith("plan_c_system_c_detector_v2"):
            continue
        resolved = root.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if any(root.rglob("*.txt")) and any(path.suffix.lower() in IMAGE_EXTS for path in root.rglob("*")):
            roots.append(root)
    return roots


def _audit_source(root: Path) -> dict[str, Any]:
    class_mapping = _read_class_mapping(root)
    image_paths = sorted([path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTS])
    label_paths = sorted(
        [
            path
            for path in root.rglob("*.txt")
            if path.is_file() and path.name.lower() != "classes.txt" and not path.name.lower().endswith(".cache")
        ]
    )
    image_by_stem: dict[str, list[Path]] = defaultdict(list)
    for path in image_paths:
        image_by_stem[path.stem].append(path)

    label_stems = {path.stem for path in label_paths}
    missing_label_for_image = sum(1 for path in image_paths if path.stem not in label_stems)
    duplicate_filenames = {stem: [str(item) for item in paths] for stem, paths in image_by_stem.items() if len(paths) > 1}

    class_counts: Counter[str] = Counter()
    valid_records: list[dict[str, Any]] = []
    invalid_label_lines = 0
    empty_label_files = 0
    missing_image_for_label = 0
    image_paths_with_valid_label: set[str] = set()

    for label_path in label_paths:
        image_path = _match_image(label_path, image_by_stem)
        if image_path is None:
            missing_image_for_label += 1
        lines = label_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if not [line for line in lines if line.strip()]:
            empty_label_files += 1
        valid_lines: list[dict[str, Any]] = []
        for line_number, line in enumerate(lines, start=1):
            parsed = _parse_yolo_line(line, class_mapping)
            if not parsed:
                if line.strip():
                    invalid_label_lines += 1
                continue
            class_counts[parsed["class_name"]] += 1
            valid_lines.append({"line_number": line_number, **parsed})
        if image_path is not None and valid_lines:
            image_paths_with_valid_label.add(str(image_path))
            valid_records.append(
                {
                    "source_root": str(root),
                    "image_path": str(image_path),
                    "label_path": str(label_path),
                    "valid_lines": valid_lines,
                }
            )

    return {
        "path": str(root),
        "image_count": len(image_paths),
        "label_file_count": len(label_paths),
        "valid_label_lines": sum(class_counts.values()),
        "invalid_label_lines": invalid_label_lines,
        "class_counts": dict(sorted(class_counts.items())),
        "class_mapping": class_mapping,
        "empty_label_files": empty_label_files,
        "missing_image_for_label": missing_image_for_label,
        "missing_label_for_image": missing_label_for_image,
        "duplicate_filenames": duplicate_filenames,
        "image_paths": sorted(image_paths_with_valid_label),
        "label_paths": [str(path) for path in label_paths],
        "valid_records": valid_records,
    }


def _read_class_mapping(root: Path) -> dict[str, str]:
    default = {str(key): value for key, value in FINAL_CLASS_NAMES.items()}
    for name in ("data.yaml", "dataset.yaml"):
        path = root / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        mapping: dict[str, str] = {}
        in_names = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("names:"):
                in_names = True
                inline = line.partition(":")[2].strip()
                if inline.startswith("[") and inline.endswith("]"):
                    values = [item.strip().strip("'\"") for item in inline.strip("[]").split(",")]
                    mapping.update({str(index): _normalize_name(value) for index, value in enumerate(values) if value})
                continue
            if in_names:
                match = re.match(r"^(\d+)\s*:\s*['\"]?([^'\"]+)['\"]?\s*$", line)
                if match:
                    mapping[match.group(1)] = _normalize_name(match.group(2))
                elif line and not line.startswith("#") and not raw_line.startswith(" "):
                    break
        if mapping:
            return mapping
    return default


def _match_image(label_path: Path, image_by_stem: dict[str, list[Path]]) -> Path | None:
    candidates = image_by_stem.get(label_path.stem, [])
    if not candidates:
        return None
    label_parts = {part.lower() for part in label_path.parts}
    for image in candidates:
        image_parts = {part.lower() for part in image.parts}
        if label_parts.intersection({"train", "val", "test"}) == image_parts.intersection({"train", "val", "test"}):
            return image
    return candidates[0]


def _parse_yolo_line(line: str, class_mapping: dict[str, str]) -> dict[str, Any] | None:
    parts = line.strip().split()
    if len(parts) < 5:
        return None
    try:
        source_class_id = int(float(parts[0]))
        values = [float(item) for item in parts[1:5]]
    except ValueError:
        return None
    x, y, w, h = values
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
        return None
    class_name = _normalize_name(class_mapping.get(str(source_class_id), FINAL_CLASS_NAMES.get(source_class_id, "")))
    if class_name not in FINAL_CLASS_NAMES.values():
        return None
    return {
        "source_class_id": source_class_id,
        "class_name": class_name,
        "x": round(x, 8),
        "y": round(y, 8),
        "w": round(w, 8),
        "h": round(h, 8),
    }


def _normalize_name(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _markdown_report(audit: dict[str, Any]) -> str:
    lines = [
        "# Plan C Training Dataset Audit",
        "",
        f"- status: `{audit['status']}`",
        f"- ready_for_training: `{audit['ready_for_training']}`",
        f"- image_count: `{audit['image_count']}`",
        f"- label_file_count: `{audit['label_file_count']}`",
        f"- valid_label_lines: `{audit['valid_label_lines']}`",
        f"- invalid_label_lines: `{audit['invalid_label_lines']}`",
        f"- class_counts: `{audit['class_counts']}`",
        f"- recommended_classes: `{audit['recommended_classes']}`",
        f"- shortfalls: `{audit['shortfalls']}`",
        "",
        "Catatan: audit ini read-only. Tidak ada scraping, labeling ulang, atau perubahan source dataset.",
        "",
        "## Candidate Sources",
    ]
    for source in audit["candidate_sources"]:
        lines.append(
            f"- `{source['path']}` images={source['image_count']} labels={source['label_file_count']} "
            f"valid={source['valid_label_lines']} class_counts={source['class_counts']}"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
