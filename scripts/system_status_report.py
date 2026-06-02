from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.system_status import collect_project_status, render_status_markdown, render_status_text  # noqa: E402


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Phase 4 system status report.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--write-md", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    status = collect_project_status(ROOT)
    if args.format == "json":
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print(render_status_text(status))
    if args.write_md:
        target = args.write_md
        if not str(target).replace("\\", "/").startswith("docs/") and not str(target.resolve()).startswith(str((ROOT / "docs").resolve())):
            print("write_md_error: output must be inside docs/")
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_status_markdown(status), encoding="utf-8")
        print(f"write_md: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
