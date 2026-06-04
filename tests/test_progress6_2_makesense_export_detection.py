from __future__ import annotations

import zipfile
from pathlib import Path

from ulp_project.progress6_2_training import extract_makesense_zips, progress6_2_export_audit


def test_progress6_2_missing_export_blocks_training(tmp_path: Path) -> None:
    result = progress6_2_export_audit([tmp_path])

    assert result["status"] == "PROGRESS_6_2_BLOCKED_MAKESENSE_EXPORT_NOT_FOUND"
    assert result["label_file_count"] == 0
    assert result["no_fake_label"] is True


def test_progress6_2_zip_export_extracts_to_ignored_work_folder(tmp_path: Path) -> None:
    zip_path = tmp_path / "makesense.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("labels/sample.txt", "2 0.5 0.5 0.2 0.2\n")

    result = extract_makesense_zips(tmp_path)

    assert result["status"] == "MAKESENSE_ZIP_EXTRACTED"
    assert result["zip_count"] == 1
    assert (tmp_path / "extracted" / "makesense" / "labels" / "sample.txt").is_file()
