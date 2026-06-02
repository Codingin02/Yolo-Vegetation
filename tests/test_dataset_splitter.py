from pathlib import Path

from ulp_project.dataset_split import DatasetPair, split_pairs
from ulp_project.dataset_split import build_dataset, write_data_yaml


def test_split_pairs_is_deterministic(tmp_path: Path):
    pairs = [
        DatasetPair(tmp_path / f"img_{idx}.jpg", tmp_path / f"img_{idx}.txt")
        for idx in range(10)
    ]
    first_train, first_val = split_pairs(pairs, val_ratio=0.2, seed=23050874166)
    second_train, second_val = split_pairs(pairs, val_ratio=0.2, seed=23050874166)
    assert [pair.image.name for pair in first_train] == [pair.image.name for pair in second_train]
    assert [pair.image.name for pair in first_val] == [pair.image.name for pair in second_val]
    assert len(first_val) == 2


def test_build_dataset_dry_run_waits_for_labels_without_creating_target(tmp_path: Path):
    target = tmp_path / "field_multiclass_v1"
    summary = build_dataset(
        point="V001_pohon_sono",
        target_dir=target,
        val_ratio=0.2,
        seed=23050874166,
        mode="dry-run",
    )
    assert summary.status == "LABELS_NOT_READY"
    assert not target.exists()


def test_write_data_yaml_uses_locked_order(tmp_path: Path):
    output = write_data_yaml(tmp_path / "field_multiclass_v1")
    text = output.read_text(encoding="utf-8")
    assert "0: struktur_penyangga" in text
    assert "1: konduktor" in text
    assert "2: pohon_sono" in text
