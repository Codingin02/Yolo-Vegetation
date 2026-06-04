from __future__ import annotations

from pathlib import Path

from ulp_project.classes import CLASS_ORDER, CLASS_NAMES
from ulp_project.progress6_1_labeling import write_yolo_classes_template


def test_progress6_1_class_order_locked() -> None:
    assert CLASS_ORDER == {0: "struktur_penyangga", 1: "konduktor", 2: "pohon_sono"}
    assert CLASS_NAMES == ["struktur_penyangga", "konduktor", "pohon_sono"]


def test_progress6_1_yolo_classes_template_order(tmp_path: Path) -> None:
    output = write_yolo_classes_template(tmp_path / "yolo_classes.txt")

    assert output.read_text(encoding="utf-8").splitlines() == CLASS_NAMES
