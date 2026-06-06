from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_smoke() -> dict[str, object]:
    tokens = ["SANGAT_AKURAT", "HIGH_" + "PRECISION", "SURVEY_" + "GRADE", "MULTI_" + "SATELLITE_CONFIRMED"]
    findings: list[str] = []
    for root in [ROOT / "src" / "ulp_project", ROOT / "scripts"]:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".js", ".html", ".css"}:
                continue
            if path.name == Path(__file__).name:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            upper = text.upper()
            for token in tokens:
                if token in upper:
                    findings.append(path.relative_to(ROOT).as_posix() + ":" + token)
    return {
        "status": "PROGRESS_6_3_NO_FAKE_PRECISION_SMOKE_PASS" if not findings else "PROGRESS_6_3_FAKE_PRECISION_CLAIM_FOUND",
        "findings": findings,
        "no_fake_accuracy": not findings,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PROGRESS_6_3_NO_FAKE_PRECISION_SMOKE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
