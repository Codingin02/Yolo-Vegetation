from pathlib import Path

from ulp_project.map_builder import build_field_map_status
from ulp_project.spreadsheet_export import build_rows, write_csv


def test_map_builder_dry_run_does_not_write(tmp_path: Path):
    output = tmp_path / "map.html"
    status = build_field_map_status(gps_dir=tmp_path / "missing_gps", output=output, mode="dry-run")
    assert status["status"] == "GPS_DATA_NOT_READY"
    assert status["written"] is False
    assert not output.exists()


def test_spreadsheet_rows_and_write_only_to_temp(tmp_path: Path):
    review = tmp_path / "review"
    point = review / "V001_pohon_sono"
    (point / "images_selected").mkdir(parents=True)
    (point / "labels_selected").mkdir(parents=True)
    (point / "images_selected" / "V001_sample.jpg").write_bytes(b"placeholder")
    rows = build_rows(review_dir=review, gps_dir=tmp_path / "gps")
    assert rows[0]["point_name"] == "V001_pohon_sono"
    assert rows[0]["status"] == "WAITING_FOR_LABELS"
    output = tmp_path / "manifest.csv"
    write_csv(rows, output)
    assert output.exists()
