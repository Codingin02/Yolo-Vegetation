"""Small metadata helpers that only read project folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


@dataclass(frozen=True)
class PointName:
    point_id: str
    object_type: str
    point_name: str


def parse_point_name(name: str) -> PointName:
    parts = name.split("_", 1)
    point_id = parts[0]
    object_type = parts[1] if len(parts) > 1 else "unknown"
    return PointName(point_id=point_id, object_type=object_type, point_name=name)


def list_images(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        item for item in folder.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
    )


def list_videos(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        item for item in folder.iterdir() if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS
    )


def list_label_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(item for item in folder.iterdir() if item.is_file() and item.suffix.lower() == ".txt")
