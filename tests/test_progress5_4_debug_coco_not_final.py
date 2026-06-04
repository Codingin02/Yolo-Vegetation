from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress5_4_debug_coco_never_becomes_real_model() -> None:
    payload = create_app().test_client().post("/api/field/debug-coco-frame", json={"point_id": "V001_pohon_sono"}).get_json()

    assert str(payload["model_status"]).startswith("DEBUG_COCO_YOLO_NOT_FIELD_MODEL")
    assert payload["debug_mode"] is True
    assert payload["detection_source"] == "DEBUG_COCO_YOLO_NOT_FIELD_MODEL"
    assert payload["model_status"] != "REAL_MODEL"
