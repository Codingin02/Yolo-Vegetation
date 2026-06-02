from pathlib import Path

from scripts.phase3_readiness_gate import evaluate_readiness


def write_classes(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "names:\n"
        "  0: struktur_penyangga\n"
        "  1: konduktor\n"
        "  2: pohon_sono\n",
        encoding="utf-8",
    )


def test_phase3_gate_waits_for_labels_without_export(tmp_path: Path):
    image_dir = tmp_path / "images_selected"
    label_dir = tmp_path / "labels_selected"
    export_dir = tmp_path / "export"
    data_yaml = tmp_path / "field_multiclass_v1" / "data.yaml"
    class_config = tmp_path / "configs" / "classes.yaml"
    image_dir.mkdir()
    label_dir.mkdir()
    export_dir.mkdir()
    write_classes(class_config)
    (image_dir / "V001_sample.jpg").write_bytes(b"placeholder")

    readiness = evaluate_readiness(
        root=tmp_path,
        branch="system-finalization-no-label-touch",
        image_dir=image_dir,
        label_dir=label_dir,
        export_dir=export_dir,
        data_yaml=data_yaml,
        class_config=class_config,
    )

    assert readiness.final_status == "PHASE3_READY_WAITING_FOR_LABELS"
    assert readiness.import_status == "BLOCKED_WAITING_FOR_MAKESENSE_EXPORT"
    assert readiness.build_dataset_status == "BLOCKED_WAITING_FOR_LABELS"
    assert readiness.train_dry_run_status == "BLOCKED_DATASET_NOT_READY"


def test_phase3_gate_ready_for_import_when_export_labels_exist(tmp_path: Path):
    image_dir = tmp_path / "images_selected"
    label_dir = tmp_path / "labels_selected"
    export_dir = tmp_path / "export"
    data_yaml = tmp_path / "field_multiclass_v1" / "data.yaml"
    class_config = tmp_path / "configs" / "classes.yaml"
    image_dir.mkdir()
    label_dir.mkdir()
    export_dir.mkdir()
    write_classes(class_config)
    (image_dir / "V001_sample.jpg").write_bytes(b"placeholder")
    (export_dir / "V001_sample.txt").write_text("2 0.5 0.5 0.1 0.1\n", encoding="utf-8")

    readiness = evaluate_readiness(
        root=tmp_path,
        branch="system-finalization-no-label-touch",
        image_dir=image_dir,
        label_dir=label_dir,
        export_dir=export_dir,
        data_yaml=data_yaml,
        class_config=class_config,
    )

    assert readiness.final_status == "PHASE3_READY_FOR_LABEL_IMPORT"
    assert readiness.import_status == "READY_FOR_LABEL_IMPORT"
    assert readiness.label_count == 0


def test_phase3_gate_rejects_wrong_class_order(tmp_path: Path):
    image_dir = tmp_path / "images_selected"
    label_dir = tmp_path / "labels_selected"
    export_dir = tmp_path / "export"
    data_yaml = tmp_path / "field_multiclass_v1" / "data.yaml"
    class_config = tmp_path / "configs" / "classes.yaml"
    image_dir.mkdir()
    label_dir.mkdir()
    export_dir.mkdir()
    class_config.parent.mkdir(parents=True, exist_ok=True)
    class_config.write_text(
        "names:\n"
        "  0: pohon_sono\n"
        "  1: konduktor\n"
        "  2: struktur_penyangga\n",
        encoding="utf-8",
    )
    (image_dir / "V001_sample.jpg").write_bytes(b"placeholder")

    readiness = evaluate_readiness(
        root=tmp_path,
        branch="system-finalization-no-label-touch",
        image_dir=image_dir,
        label_dir=label_dir,
        export_dir=export_dir,
        data_yaml=data_yaml,
        class_config=class_config,
    )

    assert not readiness.class_order_ok
    assert readiness.final_status == "PHASE3_READY_WAITING_FOR_LABELS"
