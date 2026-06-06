from __future__ import annotations

from pathlib import Path

from scripts.diagnose_v001_model_thresholds import inspect_model
from scripts.predict_v001_safe import is_conf_allowed_for_visual
from scripts.train_v001_pohon_sono_only import check_dataset, normalize_seed
from ulp_project.safe_inference import validate_single_class_pohon_sono_names


def _write_single_class_dataset(root: Path, bad_class: bool = False) -> Path:
    for split, count in (("train", 15), ("val", 4)):
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)
        for index in range(count):
            stem = f"{split}_{index:02d}"
            (root / "images" / split / f"{stem}.jpg").write_bytes(b"jpg")
            class_id = 1 if bad_class and split == "train" and index == 0 else 0
            (root / "labels" / split / f"{stem}.txt").write_text(
                f"{class_id} 0.5 0.5 0.1 0.1\n",
                encoding="utf-8",
            )
    data_yaml = root / "data.yaml"
    data_yaml.write_text(
        "\n".join(
            [
                f"path: {root.as_posix()}",
                "train: images/train",
                "val: images/val",
                "names:",
                "  0: pohon_sono",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return data_yaml


def test_progress6_3_seed_normalization() -> None:
    assert normalize_seed(23050874166) == 1576037691


def test_progress6_3_missing_model_is_not_ready(tmp_path: Path) -> None:
    result = inspect_model(tmp_path / "missing.pt")

    assert result["status"] == "MODEL_NOT_READY"
    assert result["rejection_reason"] == "MODEL_FILE_NOT_FOUND"


def test_progress6_3_multiclass_names_rejected() -> None:
    result = validate_single_class_pohon_sono_names({0: "struktur_penyangga", 1: "konduktor", 2: "pohon_sono"})

    assert result["status"] == "WRONG_MODEL_MULTICLASS_REJECTED"


def test_progress6_3_low_conf_requires_diagnostic_unsafe() -> None:
    assert is_conf_allowed_for_visual(0.049, diagnostic_unsafe=False) is False
    assert is_conf_allowed_for_visual(0.049, diagnostic_unsafe=True) is True


def test_progress6_3_dataset_rejects_non_zero_class(tmp_path: Path) -> None:
    data_yaml = _write_single_class_dataset(tmp_path / "dataset", bad_class=True)

    result = check_dataset(data_yaml)

    assert result["ready"] is False
    assert result["status"] == "DATASET_NOT_SINGLE_CLASS"


def test_progress6_3_dataset_accepts_single_class_zero(tmp_path: Path) -> None:
    data_yaml = _write_single_class_dataset(tmp_path / "dataset")

    result = check_dataset(data_yaml)

    assert result["ready"] is True
    assert result["status"] == "READY"
    assert result["pohon_sono_boxes"] == 19
