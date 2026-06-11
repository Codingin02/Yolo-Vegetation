"""Image quality checks for System C dataset candidates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MIN_WIDTH = 320
MIN_HEIGHT = 240


def inspect_image(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "IMAGE_MISSING", "quality_pass": False, "width": 0, "height": 0}
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = int(image.width), int(image.height)
    except Exception as exc:
        return {"status": "IMAGE_CORRUPT_OR_UNREADABLE", "quality_pass": False, "error": f"{type(exc).__name__}: {exc}", "width": 0, "height": 0}
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        return {"status": "REJECT_LOW_QUALITY", "quality_pass": False, "width": width, "height": height}
    return {"status": "IMAGE_QUALITY_OK", "quality_pass": True, "width": width, "height": height}


def inspect_many(paths: list[Path]) -> dict[str, Any]:
    results = [inspect_image(path) for path in paths]
    return {
        "total": len(results),
        "quality_pass": sum(1 for item in results if item.get("quality_pass")),
        "rejected": sum(1 for item in results if not item.get("quality_pass")),
        "by_status": _count_by_status(results),
    }


def _count_by_status(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status") or "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return counts
