from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_priority_source_manifest import (  # noqa: E402
    ACCEPT_POSITIVE_POHON_SONO_REFERENCE,
    REJECT_NOT_SPECIES_SPECIFIC,
    decide_pohon_sono_status,
)


def test_species_terms_are_accepted_as_pohon_sono() -> None:
    for term in ["Pterocarpus indicus", "Angsana", "Narra", "Sonokembang"]:
        status, target_class, _note = decide_pohon_sono_status(
            license_name="CC BY-SA 4.0",
            source_url="https://commons.wikimedia.org/wiki/File:test.jpg",
            metadata_values=[term, "tree photo"],
        )
        assert status == ACCEPT_POSITIVE_POHON_SONO_REFERENCE
        assert target_class == "pohon_sono"


def test_generic_tree_without_taxon_is_rejected_from_pohon_sono() -> None:
    status, target_class, _note = decide_pohon_sono_status(
        license_name="CC BY 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:tree.jpg",
        metadata_values=["tropical tree", "street tree"],
    )
    assert status == REJECT_NOT_SPECIES_SPECIFIC
    assert target_class == "negative"
