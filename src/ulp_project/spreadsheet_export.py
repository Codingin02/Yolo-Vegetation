"""Local CSV/XLSX scaffold for project metadata."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .metadata import list_images, list_label_files, parse_point_name
from .paths import GPS_FIELD_POINTS_DIR, PROJECT_ROOT, REVIEW_CANDIDATES_DIR


FIELDNAMES = [
    "job_id",
    "point_id",
    "object_type",
    "point_name",
    "lat",
    "lon",
    "timestamp",
    "source_device",
    "model_status",
    "environmental_data_status",
    "growth_pressure_score",
    "trimming_urgency_score",
    "electrical_clearance_risk",
    "confidence_level",
    "top_factors",
    "missing_sources",
    "operator_note",
    "image_filename",
    "result_json_path",
    "image_count",
    "label_count",
    "gps_available",
    "status",
    "notes",
]


def build_rows(review_dir: Path = REVIEW_CANDIDATES_DIR, gps_dir: Path = GPS_FIELD_POINTS_DIR) -> list[dict[str, object]]:
    if not review_dir.exists():
        return []
    gps_available_names = {path.stem for path in gps_dir.rglob("*") if path.is_file()} if gps_dir.exists() else set()
    rows: list[dict[str, object]] = []
    for point_dir in sorted(item for item in review_dir.iterdir() if item.is_dir()):
        parsed = parse_point_name(point_dir.name)
        image_count = len(list_images(point_dir / "images_selected"))
        label_count = len([path for path in list_label_files(point_dir / "labels_selected") if path.name != "classes.txt"])
        label_status = "WAITING_FOR_LABELS" if image_count != label_count else "LABEL_COUNT_MATCH"
        rows.append(
            {
                "job_id": "",
                "point_id": parsed.point_id,
                "object_type": parsed.object_type,
                "point_name": parsed.point_name,
                "lat": "",
                "lon": "",
                "timestamp": "",
                "source_device": "",
                "model_status": "MODEL_NOT_READY",
                "environmental_data_status": "ENVIRONMENTAL_DATA_NOT_READY",
                "growth_pressure_score": "",
                "trimming_urgency_score": "",
                "electrical_clearance_risk": "",
                "confidence_level": "UNKNOWN",
                "top_factors": "",
                "missing_sources": "",
                "operator_note": "",
                "image_filename": "",
                "result_json_path": "",
                "image_count": image_count,
                "label_count": label_count,
                "gps_available": parsed.point_name in gps_available_names or parsed.point_id in gps_available_names,
                "status": label_status,
                "notes": "dataset_botol_not_used",
            }
        )
    return rows


def write_csv(rows: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export local project metadata CSV.")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "docs" / "sample_project_points_manifest.csv")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    rows = build_rows()
    if args.mode == "write":
        write_csv(rows, args.output)
    print(f"status: {'READY' if rows else 'NO_REVIEW_POINTS_FOUND'}")
    print(f"rows: {len(rows)}")
    print(f"output: {args.output}")
    print(f"written: {args.mode == 'write'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
