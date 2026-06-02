from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.auto_measurement import measure_from_detections  # noqa: E402
from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.realtime_field_pipeline import process_realtime_inspection  # noqa: E402


MOCK_DETECTIONS = [
    {"class_name": "P001_struktur_penyangga", "bbox": [100, 100, 140, 500], "confidence": 0.9},
    {"class_name": "V001_pohon_sono", "bbox": [250, 260, 320, 500], "confidence": 0.9},
    {"class_name": "K001_konduktor", "bbox": [80, 180, 360, 190], "confidence": 0.8},
]


def mock_auto() -> dict[str, object]:
    measurement = measure_from_detections(MOCK_DETECTIONS, asset_profile={"pole_height_reference_m": 12}, stabilize=False)
    payload = {
        "inspection_id": "PHASE15_DEMO_SAMPLE_NOT_FIELD_DATA",
        "point_id": "V001_pohon_sono_phase15_demo",
        "species": "pohon_sono",
        "asset_type": "span",
        "latitude": "-7.000000",
        "longitude": "112.000000",
        "measurement_source": "mock_auto_demo_not_field_data",
        "confidence_status": "PROVISIONAL_OPERATOR_CONFIG",
        "notes": "PHASE15_DEMO_SAMPLE_NOT_FIELD_DATA",
        "selected_clearance_m": measurement.get("selected_clearance_m"),
        "selected_hazard_target": measurement.get("selected_hazard_target"),
        "auto_measurement_status": measurement.get("measurement_status"),
        "auto_model_status": measurement.get("model_status"),
        "auto_tree_height_m": measurement.get("tree_height_m"),
        "auto_pole_height_m": measurement.get("pole_height_m"),
        "auto_cable_height_m": measurement.get("cable_height_m"),
        "auto_span_lowest_point_height_m": measurement.get("span_lowest_point_height_m"),
        "clearance_to_cable_m": measurement.get("clearance_to_cable_m"),
        "clearance_to_span_m": measurement.get("clearance_to_span_m"),
        "detected_objects": measurement.get("detected_objects"),
        "detected_classes": ",".join(item["class_name"] for item in measurement.get("detected_objects", [])),
        "pole_height_reference_m": measurement.get("pole_height_reference_m"),
        "tree_height_m_raw": measurement.get("tree_height_m"),
        "tree_height_m_stable": measurement.get("tree_height_m"),
        "cable_height_m_raw": measurement.get("cable_height_m"),
        "selected_clearance_m_raw": measurement.get("selected_clearance_m"),
        "selected_clearance_m_stable": measurement.get("selected_clearance_m"),
        "measurement_confidence": measurement.get("measurement_confidence"),
        "raw_selected_clearance_m": measurement.get("selected_clearance_m"),
        "stabilized_selected_clearance_m": measurement.get("selected_clearance_m"),
        "stabilization_status": measurement.get("stabilization_status"),
        "model_status": measurement.get("model_status"),
        "model_path": "",
        "calibration_status": "MOCK_REFERENCE_CONFIG_NOT_FIELD_FINAL",
    }
    result = process_realtime_inspection(payload, write_outputs=True)
    passed = (
        measurement["measurement_status"] == "AUTO_MEASUREMENT_READY"
        and result["eta_days"] is not None
        and result["report_written"] is True
        and result["map_marker_written"] is True
        and result["not_accuracy_claim"] is True
    )
    return {"status": "PHASE15_ROUGH_REALTIME_AUTO_DEMO_PASS" if passed else "PHASE15_ROUGH_REALTIME_AUTO_DEMO_FAIL", "measurement": measurement, "eta": result}


def server_smoke() -> dict[str, object]:
    client = create_app().test_client()
    return {
        "status": "PHASE15_SERVER_SMOKE_PASS" if client.get("/field-capture").status_code == 200 and client.get("/api/operator/auto-measurement/status").status_code == 200 else "PHASE15_SERVER_SMOKE_FAIL"
    }


def file_upload_smoke() -> dict[str, object]:
    client = create_app().test_client()
    response = client.post("/api/field-capture/upload", json={"point_id": "phase15_file_upload_smoke", "capture_fingerprint": "phase15_file_upload_smoke"})
    payload = response.get_json() or {}
    ok = response.status_code in {200, 202} and payload.get("auto_model_status") == "MODEL_NOT_READY"
    return {"status": "PHASE15_FILE_UPLOAD_SMOKE_PASS" if ok else "PHASE15_FILE_UPLOAD_SMOKE_FAIL", "response": payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 15 rough realtime auto-measurement demo.")
    parser.add_argument("--mode", choices=["mock-auto", "server-smoke", "file-upload-smoke"], default="mock-auto")
    args = parser.parse_args(argv)
    result = {"mock-auto": mock_auto, "server-smoke": server_smoke, "file-upload-smoke": file_upload_smoke}[args.mode]()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if str(result["status"]).endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
