from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_priority_source_manifest import (  # noqa: E402
    ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION,
    REJECT_GOOGLE_IMAGES_DIRECT,
    REJECT_LICENSE_UNCLEAR,
    RESTRICTED_REFERENCE_ONLY,
    classify_license,
    decide_conductor_status,
    decide_pohon_sono_status,
)


def test_license_filter_rejects_unknown_and_restricts_nc() -> None:
    assert classify_license("unknown") == "reject"
    assert classify_license("all rights reserved") == "reject"
    assert classify_license("CC-BY-NC 4.0") == "restricted"
    assert classify_license("CC BY-SA 4.0") == "allowed"


def test_nc_pohon_sono_goes_to_restricted_reference_only() -> None:
    status, target_class, _note = decide_pohon_sono_status(
        license_name="CC BY-NC 4.0",
        source_url="https://www.inaturalist.org/observations/1",
        metadata_values=["Pterocarpus indicus"],
    )
    assert status == RESTRICTED_REFERENCE_ONLY
    assert target_class == "pohon_sono"


def test_google_images_direct_is_rejected() -> None:
    status, _target_class, _note = decide_pohon_sono_status(
        license_name="CC BY 4.0",
        source_url="https://images.google.com/example",
        metadata_values=["Pterocarpus indicus"],
    )
    assert status == REJECT_GOOGLE_IMAGES_DIRECT


def test_unknown_license_rejected() -> None:
    status, _target_class, _note = decide_pohon_sono_status(
        license_name="",
        source_url="https://commons.wikimedia.org/wiki/File:test.jpg",
        metadata_values=["Pterocarpus indicus"],
    )
    assert status == REJECT_LICENSE_UNCLEAR


def test_generic_distribution_conductor_not_claimed_20kv() -> None:
    status, target_class, note = decide_conductor_status(
        license_name="CC BY-SA 4.0",
        source_url="https://commons.wikimedia.org/wiki/File:line.jpg",
        metadata_values=["overhead power line conductor", "distribution line"],
    )
    assert status == ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION
    assert target_class == "konduktor"
    assert "20kV only" in note
