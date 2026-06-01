from pathlib import Path

from ulp_project.gps_map import read_field_points


def test_read_field_points_from_txt(tmp_path: Path):
    gps = tmp_path / "V001_pohon_sono.txt"
    gps.write_text("-7.25, 112.75\n", encoding="utf-8")
    points = read_field_points(tmp_path)
    assert len(points) == 1
    assert points[0].name == "V001_pohon_sono"
