from ulp_project.paths import DEFAULT_IMAGE_DIR, DEFAULT_LABEL_DIR, DEFAULT_POINT, FIELD_DATASET_DIR, NO_TOUCH_PATHS


def test_default_paths_keep_v001_and_pkv_convention():
    assert DEFAULT_POINT == "V001_pohon_sono"
    assert DEFAULT_IMAGE_DIR.name == "images_selected"
    assert DEFAULT_LABEL_DIR.name == "labels_selected"
    assert FIELD_DATASET_DIR.name == "field_multiclass_v1"


def test_no_touch_paths_include_labeling_boundaries():
    joined = "\n".join(path.as_posix() for path in NO_TOUCH_PATHS)
    assert "00_review_candidates" in joined
    assert "data/raw" in joined
    assert "data/gps" in joined
    assert "dataset_botol" in joined
