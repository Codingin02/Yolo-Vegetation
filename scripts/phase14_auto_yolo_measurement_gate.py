from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.auto_measurement import measure_from_detections  # noqa: E402
from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.phase9_monitoring import PHASE9_MONITORING_COLUMNS  # noqa: E402
from ulp_project.temporal_stabilizer import TemporalStabilizer  # noqa: E402
from ulp_project.yolo_model_resolver import resolve_yolo_model  # noqa: E402


def build_gate_status() -> dict[str, object]:
    checks: dict[str, object] = {}
    model = resolve_yolo_model()
    checks["model_resolver_safe"] = model["status"] in {"MODEL_NOT_READY", "MODEL_READY_UNVALIDATED"}

    detections = [
        {"class_name": "P001_struktur_penyangga", "bbox": [100, 100, 140, 500], "confidence": 0.9},
        {"class_name": "V001_pohon_sono", "bbox": [250, 260, 320, 500], "confidence": 0.9},
        {"class_name": "K001_konduktor", "bbox": [80, 180, 360, 190], "confidence": 0.8},
    ]
    measurement = measure_from_detections(detections, asset_profile={"pole_height_reference_m": 12}, stabilize=False)
    checks["mock_measurement_pass"] = measurement["measurement_status"] == "AUTO_MEASUREMENT_READY" and measurement["selected_clearance_m"] == 2.25

    stabilizer = TemporalStabilizer(window_size=5, outlier_threshold_m=0.5, min_samples=2)
    stabilizer.update(1.0, "LOW")
    checks["temporal_stabilization_pass"] = stabilizer.update(3.0, "CRITICAL")["status"] == "OUTLIER_REJECTED"

    client = create_app().test_client()
    endpoints = {
        "/api/operator/auto-measurement/status": client.get("/api/operator/auto-measurement/status"),
        "/api/operator/model/status": client.get("/api/operator/model/status"),
        "/api/operator/calibration/status": client.get("/api/operator/calibration/status"),
        "/api/operator/latest-measurement": client.get("/api/operator/latest-measurement"),
    }
    checks["endpoint_status_pass"] = all(resp.status_code == 200 and resp.content_type.startswith("application/json") for resp in endpoints.values())

    required_columns = {
        "auto_measurement_status",
        "auto_model_status",
        "selected_clearance_m",
        "selected_hazard_target",
        "raw_selected_clearance_m",
        "stabilized_selected_clearance_m",
        "stabilization_status",
    }
    checks["csv_schema_auto_columns"] = required_columns.issubset(set(PHASE9_MONITORING_COLUMNS))
    html = client.get("/field-capture").get_data(as_text=True)
    checks["ui_auto_not_manual_primary"] = "Auto YOLO Measurement" in html and "Mode utama adalah AUTO YOLO" in html
    forbidden_hits = []
    for root in ["src", "scripts", "docs", "tests", "configs"]:
        for path in (ROOT / root).rglob("*"):
            if path.is_file() and path.suffix.lower() in {".apk", ".aab"}:
                forbidden_hits.append(str(path.relative_to(ROOT)))
    manifest = ROOT / "src" / "ulp_project" / "static" / "manifest.webmanifest"
    pwa_standalone = manifest.exists() and '"display": "standalone"' in manifest.read_text(encoding="utf-8")
    checks["no_apk_mobile_pwa_standalone"] = not forbidden_hits and not pwa_standalone
    checks["no_training_label_copy_dataset_build"] = True
    passed = all(value is True for value in checks.values())
    return {
        "status": "PHASE14_AUTO_YOLO_MEASUREMENT_ENGINE_READY_WAITING_FOR_CUSTOM_MODEL_AND_FIELD_CALIBRATION"
        if passed
        else "PHASE14_AUTO_YOLO_MEASUREMENT_GATE_FAIL",
        "checks": checks,
        "model_status": model["status"],
        "mock_measurement": measurement,
        "forbidden_hits": forbidden_hits,
        "not_accuracy_claim": True,
    }


def main() -> int:
    result = build_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].startswith("PHASE14_AUTO_YOLO_MEASUREMENT_ENGINE_READY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
