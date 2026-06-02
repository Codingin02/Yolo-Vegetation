"""Flask API/dashboard scaffold for system runtime phases."""

from __future__ import annotations

import time
import csv
from datetime import datetime
from pathlib import Path

from .classes import CLASS_ORDER
from .field_capture_routes import register_field_capture_routes
from .inference_runtime import run_image_inference
from .job_queue import RUNTIME_ROOT
from .map_runtime import build_system_map
from .paths import PROJECT_ROOT
from .risk_map_exporter import risk_map_status
from .vegetation_report_writer import latest_report_status
from .system_status import collect_project_status
from .vegetation_growth import predict_vegetation_growth_risk
from .phase9_monitoring import MONITORING_CSV, RISK_MAP_HTML
from .runtime_error_log import latest_api_error, write_api_error

try:
    from flask import Flask, jsonify, request
    from werkzeug.exceptions import HTTPException
except ImportError:  # pragma: no cover
    Flask = None
    jsonify = None
    request = None
    HTTPException = None


def get_model_state() -> dict[str, str]:
    return {"status": "MODEL_NOT_READY", "message": "Training final belum dijalankan."}


def create_app(runtime_root: Path | None = None):
    if Flask is None:
        raise RuntimeError("FLASK_NOT_INSTALLED: install flask in the local venv to run the server.")

    app = Flask(__name__)
    app.config["ULP_RUNTIME_ROOT"] = str(runtime_root or RUNTIME_ROOT)
    register_field_capture_routes(app)

    @app.errorhandler(Exception)
    def api_error_handler(error):
        if request is not None and request.path.startswith("/api/"):
            logged = write_api_error(error, request.path)
            status_code = error.code if HTTPException is not None and isinstance(error, HTTPException) else 500
            return (
                jsonify(
                    {
                        "status": "ERROR",
                        "error_type": logged["error_type"],
                        "message": logged["message"][:300],
                        "request_path": request.path,
                        "timestamp": logged["timestamp"],
                    }
                ),
                status_code,
            )
        raise error

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
        <p>Field capture browser: /field-capture</p>
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

    @app.get("/api/latency/ping")
    def latency_ping():
        started = time.perf_counter()
        return jsonify({"status": "PONG", "latency_ms": int((time.perf_counter() - started) * 1000)})

    @app.get("/operator")
    def operator_dashboard():
        count = _monitoring_row_count()
        html = f"""
        <html><body>
        <h1>Operator Server Dashboard</h1>
        <p>Server status: OPERATOR_DASHBOARD_READY</p>
        <p>Last inspection count: {count}</p>
        <p>CSV report: {MONITORING_CSV}</p>
        <p>Risk map: {RISK_MAP_HTML}</p>
        <p>Model status: MODEL_NOT_READY</p>
        <p>Calibration status: MANUAL_CLEARANCE_PROVISIONAL / CALIBRATION_WAITING_FOR_FIELD_DATA</p>
        <p>Environmental status: ENVIRONMENT_PARTIAL_OR_MANUAL_REQUIRED</p>
        <p>Warning: ETA masih provisional sampai YOLO, kalibrasi, data lingkungan, dan ground truth valid.</p>
        </body></html>
        """
        return html

    @app.get("/api/operator/latest-report")
    def operator_latest_report():
        scaffold = latest_report_status()
        return jsonify(
            {
                **scaffold,
                "phase10_12_monitoring_csv": str(MONITORING_CSV),
                "monitoring_csv_exists": MONITORING_CSV.exists(),
                "inspection_count": _monitoring_row_count(),
                "status": "LOCAL_MONITORING_CSV_READY" if MONITORING_CSV.exists() else "LOCAL_MONITORING_CSV_NOT_WRITTEN_YET",
            }
        )

    @app.get("/api/operator/map-status")
    def operator_map_status():
        return jsonify({**risk_map_status(), "phase10_12_map": str(RISK_MAP_HTML), "phase10_12_map_exists": RISK_MAP_HTML.exists()})

    @app.get("/api/operator/latest-error")
    def operator_latest_error():
        return jsonify(latest_api_error())

    @app.get("/api/operator/runtime-status")
    def operator_runtime_status():
        return jsonify(
            {
                "status": "RUNTIME_STATUS_READY",
                "timestamp": datetime.now().isoformat(),
                "monitoring_csv": str(MONITORING_CSV),
                "monitoring_csv_exists": MONITORING_CSV.exists(),
                "risk_map": str(RISK_MAP_HTML),
                "risk_map_exists": RISK_MAP_HTML.exists(),
                "runtime_root": app.config["ULP_RUNTIME_ROOT"],
                "model_status": "MODEL_NOT_READY",
                "dataset_status": "WAITING_FOR_LABELS",
                "field_capture": "/field-capture",
            }
        )

    return app


def _monitoring_row_count() -> int:
    if not MONITORING_CSV.exists():
        return 0
    with MONITORING_CSV.open("r", newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in csv.DictReader(handle)), 0)


def main() -> int:
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
    return 0
