from pathlib import Path

from ulp_project.map_runtime import build_system_map


def test_map_runtime_dry_run_uses_outputs_maps_not_results(tmp_path: Path):
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "point_id,object_type,point_name,latitude,longitude,risk_level,status,notes\n"
        "V001,pohon_sono,V001_pohon_sono,,,,GPS_DATA_NOT_READY,\n",
        encoding="utf-8",
    )
    result = build_system_map(registry, mode="dry-run")
    assert result["status"] == "GPS_DATA_NOT_READY"
    assert result["written"] is False
    assert "outputs" in result["output"]
    assert "results" not in result["output"]
