from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_3_progress5_4_and_6_2_gates_still_pass() -> None:
    for script in [
        "scripts/progress5_4_remote_https_camera_yolo_gate.py",
        "scripts/progress6_2_native_browser_gps_camera_gate.py",
    ]:
        completed = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
