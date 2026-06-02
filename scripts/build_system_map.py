from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.map_runtime import OUTPUT_MAP_DIR, build_system_map  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build system map from a field point registry CSV.")
    parser.add_argument("--registry", type=Path, default=ROOT / "data" / "templates" / "field_point_registry_template.csv")
    parser.add_argument("--output", type=Path, default=OUTPUT_MAP_DIR / "field_system_map.html")
    parser.add_argument("--risk")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    args = parser.parse_args(argv)
    result = build_system_map(args.registry, args.output, Path(args.risk) if args.risk else None, args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {"READY", "GPS_DATA_NOT_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
