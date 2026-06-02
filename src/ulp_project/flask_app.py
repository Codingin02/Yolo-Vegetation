"""Flask API contract scaffold for Phase 4."""

from __future__ import annotations

from .classes import CLASS_ORDER
from .inference_runtime import run_image_inference
from .map_runtime import build_system_map
from .paths import PROJECT_ROOT
from .system_status import collect_project_status
from .vegetation_growth import predict_vegetation_growth_risk

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

    @app.get("/")
    def index():
        status = collect_project_status()
        html = f"""
        <html><body>
        <h1>ULP Project Dashboard</h1>
        <p>Labeling status: {status['labels_selected']['status']}</p>
        <p>Dataset status: {status['field_dataset']['status']}</p>
        <p>Model status: {status['model']['status']}</p>
        <p>Map status: {status['map']['status']}</p>
        <p>Environmental data status: {status['environmental_data']['status']}</p>
        <p>Next after makesense export: run phase gates, import dry-run, import copy, validate labels.</p>
        </body></html>
        """
        return html

    @app.get("/health")
    def health():
        return jsonify({"status": "READY", "service": "ulp_project_flask_scaffold"})

    @app.get("/api/status")
    @app.get("/status")
    def status():
        return jsonify(collect_project_status())

    @app.get("/api/classes")
    @app.get("/classes")
    def classes():
        return jsonify({"class_order": CLASS_ORDER, "status": "LOCKED"})

    @app.get("/api/points")
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

    @app.get("/api/map/status")
    @app.get("/map")
    def map_status():
        result = build_system_map(PROJECT_ROOT / "data" / "templates" / "field_point_registry_template.csv", mode="dry-run")
        return jsonify(result)

    @app.get("/api/risk/sample")
    def risk_sample():
        return jsonify(predict_vegetation_growth_risk({}))

    @app.post("/api/infer/image")
    @app.post("/predict-image")
    def predict_image():
        result = run_image_inference("uploaded-image-placeholder")
        return jsonify(result), 503 if result["status"] == "MODEL_NOT_READY" else 200

    return app


def main() -> int:
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
    return 0
