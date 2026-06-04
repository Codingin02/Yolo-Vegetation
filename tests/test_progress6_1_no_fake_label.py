from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_1_labeling import build_labeling_manifest, prepare_labeling_handoff


def test_progress6_1_handoff_manifest_waits_for_manual_labels(tmp_path: Path) -> None:
    result = build_labeling_manifest(output=tmp_path / "labeling_manifest.csv")

    assert result["status"] == "LABELING_MANIFEST_READY"
    assert result["no_fake_label"] is True
    text = Path(result["manifest_path"]).read_text(encoding="utf-8")
    assert "WAITING_FOR_MAKESENSE_LABEL" in text
    assert "do not auto-generate bounding boxes" in text


def test_progress6_1_prepare_handoff_no_fake_label_policy() -> None:
    result = prepare_labeling_handoff()

    assert result["status"] == "PROGRESS_6_1_LABELING_HANDOFF_READY"
    assert result["no_fake_label"] is True
