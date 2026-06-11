"""Build the System C Roboflow manual review package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ulp_project.plan_c_system_c_download_manager import ensure_system_c_dirs  # noqa: E402
from ulp_project.plan_c_system_c_roboflow_package import build_roboflow_package  # noqa: E402
from ulp_project.plan_c_system_c_yolo_exporter import DATASET_FINAL_ROOT, read_manifest_csv  # noqa: E402


def _latest_manifest() -> Path | None:
    review_dir = DATASET_FINAL_ROOT / "review"
    manifests = sorted(review_dir.glob("*.csv"), key=lambda path: path.stat().st_mtime, reverse=True) if review_dir.exists() else []
    return manifests[0] if manifests else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build System C Roboflow review package")
    parser.add_argument("--manifest", default="", help="Optional manifest CSV path.")
    args = parser.parse_args()
    ensure_system_c_dirs()
    manifest_path = Path(args.manifest) if args.manifest else _latest_manifest()
    rows = read_manifest_csv(manifest_path) if manifest_path else []
    result = build_roboflow_package(rows)
    result["manifest_used"] = str(manifest_path) if manifest_path else ""
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
