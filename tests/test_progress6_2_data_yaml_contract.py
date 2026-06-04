from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_1_labeling import write_data_yaml


def test_progress6_2_data_yaml_class_order_contract(tmp_path: Path) -> None:
    path = write_data_yaml(tmp_path, include_test=False)
    text = path.read_text(encoding="utf-8")

    assert "path: data/dataset_yolo/field_multiclass_v1" in text
    assert "0: struktur_penyangga" in text
    assert "1: konduktor" in text
    assert "2: pohon_sono" in text
    assert "test:" not in text
