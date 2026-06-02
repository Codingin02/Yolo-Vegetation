from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.inference_runtime import run_camera_inference, run_image_inference, run_video_inference  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe inference runtime scaffold.")
    parser.add_argument("--mode", choices=["image", "video", "camera"], default="image")
    parser.add_argument("--input", default="")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--model")
    args = parser.parse_args(argv)
    if args.mode == "image":
        result = run_image_inference(args.input, args.model)
    elif args.mode == "video":
        result = run_video_inference(args.input, args.model)
    else:
        result = run_camera_inference(args.camera_index, args.model)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {"MODEL_NOT_READY", "MODEL_AVAILABLE_INFERENCE_NOT_IMPLEMENTED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
