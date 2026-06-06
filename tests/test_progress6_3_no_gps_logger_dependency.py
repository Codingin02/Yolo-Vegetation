from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_3_no_gps_logger_dependency_in_field_runtime() -> None:
    roots = [ROOT / "src" / "ulp_project"]
    roots.extend(path for path in (ROOT / "scripts").glob("progress6_3_*.py"))
    for root in roots:
        paths = root.rglob("*") if root.is_dir() else [root]
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in {".py", ".js", ".html", ".css"}:
                continue
            if "no_gps_logger_dependency" in path.name:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            assert "gps logger" not in text
            assert "download apk" not in text
