from pathlib import Path

from ulp_project.plan_c_growth_model import load_csv_reference, load_growth_profile
from ulp_project.plan_c_storage import PLAN_C_REFERENCE_DIR


def test_plan_c_growth_profile_is_proxy_reference():
    profile = load_growth_profile(PLAN_C_REFERENCE_DIR)
    assert profile["growth_profile_status"] == "GROWTH_PROFILE_READY_PROXY"
    assert profile["data_source_type"] == "proxy"
    assert profile["observed_or_proxy"] == "proxy"
    assert profile["not_final_accuracy_claim"] is True


def test_plan_c_growth_missing_reference_is_safe(tmp_path: Path):
    profile = load_growth_profile(tmp_path)
    assert profile["growth_profile_status"] == "GROWTH_PROFILE_MISSING"
    assert profile["prediction_window"] == "data tidak cukup"


def test_plan_c_growth_csv_loader_skips_blank_first_line(tmp_path: Path):
    csv_path = tmp_path / "growth.csv"
    csv_path.write_text("\nvalue\n0.1\n", encoding="utf-8")
    result = load_csv_reference(csv_path)
    assert result["status"] == "CSV_REFERENCE_LOADED"
    assert result["row_count"] == 1
