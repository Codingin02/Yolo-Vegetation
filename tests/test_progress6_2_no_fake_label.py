from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_2_training import progress6_2_export_audit


def test_progress6_2_never_creates_fake_labels_for_missing_export(tmp_path: Path) -> None:
    result = progress6_2_export_audit([tmp_path])

    assert result["status"] == "PROGRESS_6_2_BLOCKED_MAKESENSE_EXPORT_NOT_FOUND"
    assert not list(tmp_path.rglob("*.txt"))
    assert result["no_fake_label"] is True
