"""Flask scaffold that reports MODEL_NOT_AVAILABLE instead of fake detections."""

from __future__ import annotations

from ulp_project.paths import FIELD_DATA_YAML, PROJECT_ROOT
from ulp_project.risk_stub import evaluate_vegetation_risk
from ulp_project.spreadsheet_export import build_rows

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover - exercised only when Flask is absent.
    Flask = None
    jsonify = None
    request = None


def model_status() -> dict[str, str]:
    candidates = [
        PROJECT_ROOT / "weights" / "field_multiclass_v1.pt",
        PROJECT_ROOT / "runs" / "detect" / "field_multiclass_v1" / "weights" / "best.pt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return {"status": "MODEL_AVAILABLE", "path": str(candidate)}
    return {"status": "MODEL_NOT_AVAILABLE", "path": ""}


def create_app():
    if Flask is None:
        raise RuntimeError("Flask is not installed. Run: python -m pip install flask")
    app = Flask(__name__)

    @app.get("/")
    def index():
        return jsonify(
            {
                "project": "ULP_Project",
                "mode": "SYSTEM_FINALIZATION_NO_LABEL_TOUCH",
                "model": model_status(),
            }
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "READY", "model": model_status()["status"]})

    @app.get("/api/project-status")
    def project_status():
        return jsonify(
            {
                "labeling": "WAITING_FOR_MAKESENSE_EXPORT",
                "dataset_yaml": "READY" if FIELD_DATA_YAML.exists() else "WAITING_FOR_LABELS",
                "training": "NOT_RUN",
                "model": model_status()["status"],
            }
        )

    @app.get("/api/points")
    def points():
        rows = build_rows()
        return jsonify({"status": "READY" if rows else "PLACEHOLDER", "points": rows})

    @app.get("/api/risk-preview")
    def risk_preview():
        result = evaluate_vegetation_risk(dict(request.args))
        return jsonify(result.to_dict())

    @app.post("/predict-image")
    def predict_image():
        status = model_status()
        if status["status"] != "MODEL_AVAILABLE":
            return jsonify({"status": "MODEL_NOT_AVAILABLE", "detections": []}), 503
        return jsonify({"status": "MODEL_AVAILABLE_BUT_INFERENCE_NOT_IMPLEMENTED", "detections": []})

    return app


def main() -> int:
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
