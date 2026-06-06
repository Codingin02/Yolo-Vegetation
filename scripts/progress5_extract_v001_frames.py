from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIDEO_DIR = ROOT / "data" / "raw" / "01_field_points" / "V001_pohon_sono" / "videos"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "images_all"
DEFAULT_SUMMARY_PATH = ROOT / "data" / "metadata" / "progress5_v001_frame_extract_summary.json"
FRAME_PREFIX = "V001_pohon_sono_frame_"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def list_videos(video_dir: Path) -> list[Path]:
    if not video_dir.exists():
        return []
    return sorted(path for path in video_dir.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS)


def frame_output_path(output_dir: Path, frame_number: int) -> Path:
    return output_dir / f"{FRAME_PREFIX}{frame_number:06d}.jpg"


def existing_frame_numbers(output_dir: Path) -> set[int]:
    pattern = re.compile(rf"^{re.escape(FRAME_PREFIX)}(\d{{6}})\.jpg$", re.IGNORECASE)
    numbers: set[int] = set()
    if not output_dir.exists():
        return numbers
    for path in output_dir.iterdir():
        match = pattern.match(path.name)
        if match:
            numbers.add(int(match.group(1)))
    return numbers


def write_summary(summary: dict[str, Any], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_frames(
    video_dir: Path,
    output_dir: Path,
    summary_path: Path,
    seconds_per_frame: float = 1.0,
    max_frames: int | None = None,
) -> dict[str, Any]:
    if seconds_per_frame <= 0:
        raise ValueError("seconds_per_frame must be greater than zero")

    try:
        import cv2  # type: ignore
    except Exception as exc:  # pragma: no cover - environment guard
        summary = {
            "status": "FRAME_EXTRACTION_FAILED_OPENCV_NOT_AVAILABLE",
            "error": str(exc),
            "video_dir": str(video_dir),
            "output_dir": str(output_dir),
        }
        write_summary(summary, summary_path)
        return summary

    videos = list_videos(video_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_numbers = existing_frame_numbers(output_dir)
    video_summaries: list[dict[str, Any]] = []
    global_sample_number = 0
    frames_written = 0
    frames_skipped_existing = 0
    frames_read_failed = 0
    frames_sampled = 0

    if not videos:
        summary = {
            "status": "NO_V001_VIDEO_FOUND",
            "video_dir": str(video_dir),
            "output_dir": str(output_dir),
            "videos_found": 0,
            "frames_written": 0,
        }
        write_summary(summary, summary_path)
        return summary

    stop_requested = False
    for video_path in videos:
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            video_summaries.append({"video": str(video_path), "status": "VIDEO_OPEN_FAILED"})
            continue

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 0:
            fps = 30.0
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frame_interval = max(1, int(round(fps * seconds_per_frame)))
        sampled_for_video = 0
        written_for_video = 0
        skipped_existing_for_video = 0
        read_failed_for_video = 0

        frame_numbers = range(0, total_frames, frame_interval) if total_frames > 0 else []
        for frame_index in frame_numbers:
            if max_frames is not None and frames_written >= max_frames:
                stop_requested = True
                break
            global_sample_number += 1
            frames_sampled += 1
            sampled_for_video += 1
            target = frame_output_path(output_dir, global_sample_number)
            if global_sample_number in existing_numbers or target.exists():
                frames_skipped_existing += 1
                skipped_existing_for_video += 1
                continue

            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok or frame is None:
                frames_read_failed += 1
                read_failed_for_video += 1
                continue
            if cv2.imwrite(str(target), frame):
                frames_written += 1
                written_for_video += 1
            else:
                frames_read_failed += 1
                read_failed_for_video += 1

        capture.release()
        video_summaries.append(
            {
                "video": str(video_path),
                "status": "VIDEO_PROCESSED",
                "fps": fps,
                "total_frames": total_frames,
                "frame_interval": frame_interval,
                "sampled": sampled_for_video,
                "written": written_for_video,
                "skipped_existing": skipped_existing_for_video,
                "read_failed": read_failed_for_video,
            }
        )
        if stop_requested:
            break

    status = "FRAME_EXTRACTION_COMPLETE"
    if frames_written == 0 and frames_skipped_existing > 0:
        status = "FRAME_EXTRACTION_COMPLETE_ALL_EXISTING"
    elif frames_written == 0:
        status = "FRAME_EXTRACTION_COMPLETE_NO_NEW_FRAMES"

    summary = {
        "status": status,
        "video_dir": str(video_dir),
        "output_dir": str(output_dir),
        "summary_path": str(summary_path),
        "seconds_per_frame": seconds_per_frame,
        "max_frames": max_frames,
        "videos_found": len(videos),
        "frames_sampled": frames_sampled,
        "frames_written": frames_written,
        "frames_skipped_existing": frames_skipped_existing,
        "frames_read_failed": frames_read_failed,
        "video_summaries": video_summaries,
        "raw_data_policy": "READ_ONLY_COPY_FRAMES_NO_RAW_MOVE_OR_DELETE",
    }
    write_summary(summary, summary_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract sampled V001 pohon_sono frames for Progress 5 Kelompok 1.")
    parser.add_argument("--input-dir", default=str(DEFAULT_VIDEO_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--seconds-per-frame", type=float, default=1.0)
    parser.add_argument("--max-frames", type=int, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = extract_frames(
        video_dir=resolve_path(args.input_dir),
        output_dir=resolve_path(args.output_dir),
        summary_path=resolve_path(args.summary),
        seconds_per_frame=args.seconds_per_frame,
        max_frames=args.max_frames,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(summary["status"])
    return 0 if str(summary["status"]).startswith("FRAME_EXTRACTION_COMPLETE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
