from pathlib import Path

from ulp_project.point_registry import load_field_point_registry, validate_point_name


def test_point_registry_preserves_pkv_names(tmp_path: Path):
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "point_id,object_type,point_name,latitude,longitude,risk_level,status,notes\n"
        "P001,struktur_penyangga,P001_struktur_penyangga,-7.1,112.1,UNKNOWN,READY,\n"
        "K001,konduktor,K001_konduktor,-7.2,112.2,UNKNOWN,READY,\n"
        "V001,pohon_sono,V001_pohon_sono,-7.3,112.3,WATCH,READY,\n",
        encoding="utf-8",
    )
    result = load_field_point_registry(registry)
    names = [point["point_name"] for point in result["points"]]
    assert names == ["P001_struktur_penyangga", "K001_konduktor", "V001_pohon_sono"]
    assert validate_point_name("T001_uji_awal") is False
