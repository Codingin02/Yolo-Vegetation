"""Frame size guard; never logs full base64 frame."""

from __future__ import annotations


def validate_frame_size(size_bytes: int | None, max_frame_size_bytes: int = 1_500_000) -> dict[str, object]:
    if size_bytes is None:
        return {"status": "FRAME_SIZE_UNKNOWN", "allowed": True, "max_frame_size_bytes": max_frame_size_bytes}
    if size_bytes > max_frame_size_bytes:
        return {"status": "FRAME_SIZE_REJECTED", "allowed": False, "max_frame_size_bytes": max_frame_size_bytes}
    return {"status": "FRAME_SIZE_OK", "allowed": True, "max_frame_size_bytes": max_frame_size_bytes}
