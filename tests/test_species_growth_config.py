from pathlib import Path

from ulp_project.species_growth_config import get_species_config, load_species_growth_config
from ulp_project.tree_growth_calibration import load_tree_growth_calibration_csv


def test_pohon_sono_growth_config_requires_calibration():
    config = get_species_config("pohon_sono")
    assert config["base_growth_rate_m_per_day"] is None
    assert config["source_status"] == "NEEDS_LOCAL_CALIBRATION_OR_LITERATURE"


def test_tree_growth_calibration_template_parseable():
    result = load_tree_growth_calibration_csv(Path("data/templates/tree_growth_calibration_template.csv"))
    assert result["status"] == "READY"
    assert load_species_growth_config()["species"]["unknown_tree"]["source_status"] == "UNKNOWN"
