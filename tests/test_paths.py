from ulp_project.paths import DEFAULT_IMAGE_DIR, DEFAULT_LABEL_DIR, DEFAULT_POINT, FIELD_DATASET_DIR


def test_default_paths_keep_v001_and_pkv_convention():
    assert DEFAULT_POINT == "V001_pohon_sono"
    assert DEFAULT_IMAGE_DIR.name == "images_selected"
    assert DEFAULT_LABEL_DIR.name == "labels_selected"
    assert FIELD_DATASET_DIR.name == "field_multiclass_v1"
