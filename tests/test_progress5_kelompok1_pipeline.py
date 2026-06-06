from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from progress5_audit_v001_labels import audit_v001_labels, parse_yolo_label_file  # noqa: E402
from progress5_filter_v001_frame_quality import hamming_distance  # noqa: E402
from progress5_kelompok1_gate import decide_gate_status  # noqa: E402


def test_v001_label_parser_accepts_single_class_zero(tmp_path: Path) -> None:
    label = tmp_path / "sample.txt"
    label.write_text("0 0.5 0.5 0.25 0.30\n", encoding="utf-8")

    result = parse_yolo_label_file(label)

    assert result["errors"] == []
    assert result["rows"][0]["class_id"] == 0


def test_v001_label_parser_rejects_non_single_class(tmp_path: Path) -> None:
    label = tmp_path / "sample.txt"
    label.write_text("1 0.5 0.5 0.25 0.30\n", encoding="utf-8")

    result = parse_yolo_label_file(label)

    assert any("NON_POHON_SONO_CLASS_1" in error for error in result["errors"])


def test_v001_label_audit_waits_when_labels_missing(tmp_path: Path) -> None:
    image_dir = tmp_path / "images_selected"
    label_dir = tmp_path / "labels_selected"
    image_dir.mkdir()
    (image_dir / "V001_pohon_sono_frame_000001.jpg").write_bytes(b"not a real image for stem audit")

    result = audit_v001_labels(image_dir, label_dir)

    assert result["status"] == "WAITING_FOR_LABEL_REVIEW"
    assert result["missing_label_count"] == 1


def test_hamming_distance_counts_changed_bits() -> None:
    assert hamming_distance(0b1010, 0b1001) == 2


def test_progress5_gate_status_waiting_for_label_review() -> None:
    status = decide_gate_status(
        required_ready=True,
        selected_images_exist=True,
        labels_exist=False,
        v2_best_exists=False,
    )

    assert status == "PROGRESS5_WAITING_FOR_V001_LABEL_REVIEW"
