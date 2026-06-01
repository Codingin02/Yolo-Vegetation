from ulp_project.paths import DATASET_BOTOL_DIR, FIELD_DATASET_DIR


def test_dataset_botol_is_not_main_dataset():
    assert "dataset_botol" in str(DATASET_BOTOL_DIR)
    assert "field_multiclass_v1" in str(FIELD_DATASET_DIR)
    assert DATASET_BOTOL_DIR != FIELD_DATASET_DIR
