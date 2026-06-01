from pathlib import Path

from ulp_project.dataset_split import DatasetPair, split_pairs


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
