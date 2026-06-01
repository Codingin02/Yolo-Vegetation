from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.dataset_split import write_data_yaml  # noqa: E402
from ulp_project.paths import FIELD_DATASET_DIR  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate data.yaml with locked class order.")
    parser.add_argument("--target-dir", type=Path, default=FIELD_DATASET_DIR)
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    args = parser.parse_args(argv)
    if args.mode == "dry-run":
        print("status: DRY_RUN_READY")
        print(f"target: {args.target_dir / 'data.yaml'}")
        print("names: 0 struktur_penyangga, 1 konduktor, 2 pohon_sono")
        return 0
    output = write_data_yaml(args.target_dir)
    print("status: READY")
    print(f"output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
