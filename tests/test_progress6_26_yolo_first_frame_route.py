from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import base64
import importlib

PNG_1X1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgaAAAAAYAAYDS3iKVAAAAAElFTkSuQmCC"

def load_app():
    mod = importlib.import_module("ulp_project.flask_app")
    if hasattr(mod, "create_app"):
        return mod.create_app()
    return mod.app

def test_progress6_26_yolo_first_frame_route_no_500():
    app = load_app()
    c = app.test_client()
    res = c.post("/api/field/session/frame", json={
        "session_id": "FS_TEST_626",
        "image_base64": "data:image/png;base64," + PNG_1X1,
        "ai_switch_on": True,
        "mode": "YOLO_FIRST_REALTIME",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["runtime_mode"] == "YOLO_FIRST"
    assert data["no_fake_detection"] is True
    assert isinstance(data["detections"], list)
