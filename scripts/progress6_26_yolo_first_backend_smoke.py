import base64
import importlib
import json
from pathlib import Path

# 1x1 png transparent
PNG_1X1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="

def load_app():
    mod = importlib.import_module("ulp_project.flask_app")
    if hasattr(mod, "create_app"):
        return mod.create_app()
    if hasattr(mod, "app"):
        return mod.app
    raise RuntimeError("FLASK_APP_NOT_FOUND")

def main():
    app = load_app()
    client = app.test_client()
    payload = {
        "session_id": "FS_PROGRESS_6_26_SMOKE",
        "point_id": "V001_pohon_sono",
        "image_base64": "data:image/png;base64," + PNG_1X1,
        "frame_ts": "2026-06-09T00:00:00Z",
        "mode": "YOLO_FIRST_REALTIME",
        "ai_switch_on": True,
    }
    res = client.post("/api/field/session/frame", json=payload)
    assert res.status_code == 200, res.get_data(as_text=True)
    data = res.get_json()
    assert data["ok"] is True
    assert data["runtime_mode"] == "YOLO_FIRST"
    assert data["no_fake_detection"] is True
    assert isinstance(data.get("detections"), list)
    print(json.dumps({
        "status": "PROGRESS_6_26_YOLO_FIRST_BACKEND_SMOKE_PASS",
        "http": res.status_code,
        "route": "/api/field/session/frame",
        "runtime_mode": data.get("runtime_mode"),
        "result_status": data.get("status"),
    }, indent=2))

if __name__ == "__main__":
    main()
