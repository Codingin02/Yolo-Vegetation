from scripts.phase4_integration_gate import config_avoids_dataset_botol, flask_contract_importable


def test_phase4_config_does_not_use_dataset_botol_as_main():
    assert config_avoids_dataset_botol()


def test_phase4_flask_contract_is_importable_or_explicitly_missing_flask():
    assert flask_contract_importable()
