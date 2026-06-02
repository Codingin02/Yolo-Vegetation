from pathlib import Path

from ulp_project.environmental_data import load_manual_environmental_csv
from ulp_project.vegetation_growth import predict_vegetation_growth_risk


def test_no_environmental_csv_returns_not_ready(tmp_path: Path):
    result = load_manual_environmental_csv(tmp_path / "missing.csv")
    assert result["status"] == "ENVIRONMENTAL_DATA_NOT_READY"


def test_manual_environmental_csv_can_be_parsed(tmp_path: Path):
    csv_path = tmp_path / "env.csv"
    csv_path.write_text(
        "point_id,vegetation_class,current_tree_height_m,current_clearance_m,estimated_growth_cm_per_month,"
        "rainfall_monthly_mm,season_label,soil_ph,soil_type,temperature_c,humidity_percent,"
        "pruning_history_date,observation_date,confidence_source\n"
        "V001,pohon_sono,4,2.5,10,100,pending,7,unknown,30,70,unknown,2026-06-02,manual\n",
        encoding="utf-8",
    )
    result = load_manual_environmental_csv(csv_path)
    assert result["status"] == "READY"
    assert result["rows"][0]["point_id"] == "V001"


def test_growth_engine_with_manual_inputs_is_stub_not_final_prediction():
    result = predict_vegetation_growth_risk(
        {
            "point_id": "V001",
            "vegetation_class": "pohon_sono",
            "current_clearance_m": 2.5,
            "estimated_growth_cm_per_month": 10,
            "observation_date": "2026-06-02",
            "confidence_source": "manual",
            "rainfall_monthly_mm": 100,
            "season_label": "pending",
            "soil_ph": 7,
            "soil_type": "unknown",
            "temperature_c": 30,
            "humidity_percent": 70,
            "pruning_history_date": "unknown",
        }
    )
    assert result["status"] == "RULE_BASED_STUB"
    assert result["risk_level"] in {"SAFE", "WATCH", "WARNING", "CRITICAL"}
