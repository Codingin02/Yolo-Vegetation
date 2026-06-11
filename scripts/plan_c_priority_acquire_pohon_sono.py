from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_gbif_priority_downloader import collect_gbif_pohon_sono  # noqa: E402
from ulp_project.plan_c_inaturalist_priority_downloader import collect_inaturalist_pohon_sono  # noqa: E402
from ulp_project.plan_c_wikimedia_priority_downloader import collect_wikimedia_pohon_sono  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire priority pohon_sono legal image candidates.")
    parser.add_argument("--source", choices=["wikimedia", "gbif", "inaturalist", "all"], default="wikimedia")
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    download = bool(args.download and not args.dry_run)

    results = []
    per_source_limit = max(1, args.limit if args.source != "all" else args.limit // 3 or 1)
    if args.source in {"wikimedia", "all"}:
        results.append(collect_wikimedia_pohon_sono(limit=per_source_limit if args.source == "all" else args.limit, download=download))
    if args.source in {"gbif", "all"}:
        results.append(collect_gbif_pohon_sono(limit=per_source_limit if args.source == "all" else args.limit, download=download))
    if args.source in {"inaturalist", "all"}:
        results.append(collect_inaturalist_pohon_sono(limit=per_source_limit if args.source == "all" else args.limit, download=download))

    accepted = sum(_summary(item).get("accepted", 0) for item in results)
    restricted = sum(_summary(item).get("restricted", 0) for item in results)
    rejected = sum(_summary(item).get("rejected", 0) for item in results)
    unavailable = [item for item in results if item.get("status") == "SOURCE_UNAVAILABLE_OR_RATE_LIMITED"]
    status = "POHON_SONO_PRIORITY_ACQUISITION_DRY_RUN_READY" if not download else "POHON_SONO_PRIORITY_ACQUISITION_DOWNLOAD_READY"
    if accepted < 30:
        status = "POHON_SONO_CANDIDATES_NOT_ENOUGH"
    if unavailable and len(unavailable) == len(results):
        status = "INTERNET_UNAVAILABLE_PIPELINE_READY"
    payload = {
        "ok": True,
        "status": status,
        "source": args.source,
        "download": download,
        "accepted": accepted,
        "restricted": restricted,
        "rejected": rejected,
        "results": results,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _summary(result: dict) -> dict:
    return ((result.get("manifest") or {}).get("summary") or {}) if isinstance(result, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main())
