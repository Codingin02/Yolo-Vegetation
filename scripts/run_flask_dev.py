from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from ulp_project.flask_app import main  # noqa: E402
except RuntimeError as exc:  # pragma: no cover
    print(str(exc))
    raise SystemExit(1)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc))
        raise SystemExit(1)
