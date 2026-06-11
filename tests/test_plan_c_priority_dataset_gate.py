from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_priority_dataset_gate import run_priority_dataset_gate  # noqa: E402


def test_dataset_gate_not_enough_when_thresholds_missing() -> None:
    result = run_priority_dataset_gate(rows=[_row("pohon_sono", "ACCEPT_POSITIVE_POHON_SONO_REFERENCE")])
    assert result["status"] == "PLAN_C_PRIORITY_DATASET_NOT_ENOUGH"
    assert result["not_ready_for_final_training"] is True


def test_dataset_gate_ready_for_roboflow_review_not_final_training() -> None:
    rows = []
    rows.extend(_row("pohon_sono", "ACCEPT_POSITIVE_POHON_SONO_REFERENCE") for _ in range(30))
    rows.extend(_row("konduktor", "ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION") for _ in range(10))
    rows.extend(_row("struktur_penyangga", "ACCEPT_STRUCTURE_REFERENCE") for _ in range(10))
    result = run_priority_dataset_gate(rows=rows)
    assert result["status"] == "PLAN_C_PRIORITY_DATASET_READY_FOR_ROBOFLOW_REVIEW"
    assert result["no_final_training"] is True


def test_dataset_gate_blocks_media_or_model_staged_paths() -> None:
    rows = []
    rows.extend(_row("pohon_sono", "ACCEPT_POSITIVE_POHON_SONO_REFERENCE") for _ in range(30))
    rows.extend(_row("konduktor", "ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION") for _ in range(10))
    rows.extend(_row("struktur_penyangga", "ACCEPT_STRUCTURE_REFERENCE") for _ in range(10))
    result = run_priority_dataset_gate(rows=rows, staged_paths=["data/external_dataset_inbox/legal_images/sample.jpg"])
    assert result["status"] == "PLAN_C_PRIORITY_DATASET_NOT_ENOUGH"
    assert result["forbidden_staged_paths"]


def _row(target_class: str, status: str) -> dict[str, str]:
    scientific_name = "Pterocarpus indicus" if target_class == "pohon_sono" else ""
    return {
        "source_site": "unit-test",
        "source_page_url": "https://commons.wikimedia.org/wiki/File:test.jpg",
        "image_url": "https://upload.wikimedia.org/test.jpg",
        "target_class": target_class,
        "accepted_status": status,
        "license": "CC BY-SA 4.0",
        "author": "Tester",
        "attribution": "Tester / CC BY-SA",
        "scientific_name": scientific_name,
    }
