"""Flask API contract scaffold for Phase 4."""

from __future__ import annotations

from .classes import CLASS_ORDER
from .system_status import collect_project_status

try:
    from flask import Flask, jsonify
except ImportError:  # pragma: no cover
    Flask = None
    jsonify = None


def get_model_state() -> dict[str, str]:
    return {"status": "MODEL_NOT_READY", "message": "Training final belum dijalankan."}


def create_app():
    if Flask is None:
        raise RuntimeError("FLASK_NOT_INSTALLED: install flask in the local venv to run the server.")

    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "READY", "service": "ulp_project_flask_scaffold"})

    @app.get("/status")
    def status():
        return jsonify(collect_project_status())

    @app.get("/classes")
    def classes():
        return jsonify({"class_order": CLASS_ORDER, "status": "LOCKED"})

    @app.get("/points")
    def points():
        status_data = collect_project_status()
        return jsonify(
            {
                "status": status_data["labels_selected"]["status"],
                "review_point": status_data["review_point"],
                "image_count": status_data["images_selected"]["image_count"],
                "label_count": status_data["labels_selected"]["label_count"],
            }
        )

    @app.get("/map")
    def map_status():
        return jsonify({"status": "MAP_CONTRACT_READY", "html_map": "GPS_DATA_NOT_READY"})

    @app.post("/predict-image")
    def predict_image():
        return jsonify({"status": "MODEL_NOT_READY", "model": get_model_state(), "detections": []}), 503

    return app


def main() -> int:
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
    return 0
