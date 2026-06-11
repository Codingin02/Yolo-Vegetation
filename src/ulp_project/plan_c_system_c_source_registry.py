"""System C final source registry with 25+ legal acquisition adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SystemCSource:
    source_id: str
    source_site: str
    adapter: str
    query: str
    target_class: str
    priority: int
    legal_note: str = "license_required"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def system_c_source_registry() -> list[SystemCSource]:
    return [
        SystemCSource("wikimedia_pterocarpus_category", "Wikimedia Commons", "wikimedia_category", "Category:Pterocarpus indicus", "pohon_sono", 1),
        SystemCSource("wikimedia_pterocarpus_search", "Wikimedia Commons", "wikimedia_search", "Pterocarpus indicus", "pohon_sono", 1),
        SystemCSource("wikimedia_angsana_search", "Wikimedia Commons", "wikimedia_search", "Angsana", "pohon_sono", 1),
        SystemCSource("wikimedia_narra_search", "Wikimedia Commons", "wikimedia_search", "Narra tree", "pohon_sono", 1),
        SystemCSource("wikimedia_sonokembang_search", "Wikimedia Commons", "wikimedia_search", "Sonokembang", "pohon_sono", 1),
        SystemCSource("gbif_pterocarpus_media", "GBIF", "gbif_occurrence_media", "Pterocarpus indicus taxonKey 5349242", "pohon_sono", 1),
        SystemCSource("inat_pterocarpus", "iNaturalist", "inaturalist_observations", "Pterocarpus indicus", "pohon_sono", 1),
        SystemCSource("inat_angsana", "iNaturalist", "inaturalist_observations", "Angsana", "pohon_sono", 1),
        SystemCSource("inat_narra", "iNaturalist", "inaturalist_observations", "Narra", "pohon_sono", 1),
        SystemCSource("inat_sonokembang", "iNaturalist", "inaturalist_observations", "Sonokembang", "pohon_sono", 1),
        SystemCSource("observation_org_gbif", "Observation.org/GBIF", "gbif_backed_occurrence_media", "Pterocarpus indicus", "pohon_sono", 1),
        SystemCSource("wikimedia_power_lines", "Wikimedia Commons", "wikimedia_search", "power lines", "konduktor", 2),
        SystemCSource("wikimedia_overhead_power_lines", "Wikimedia Commons", "wikimedia_category", "Category:Overhead power lines", "konduktor", 2),
        SystemCSource("wikimedia_utility_pole", "Wikimedia Commons", "wikimedia_search", "utility pole", "struktur_penyangga", 3),
        SystemCSource("wikimedia_electric_pole", "Wikimedia Commons", "wikimedia_search", "electric pole", "struktur_penyangga", 3),
        SystemCSource("wikimedia_distribution_pole", "Wikimedia Commons", "wikimedia_search", "distribution pole", "struktur_penyangga", 3),
        SystemCSource("wikimedia_concrete_pole", "Wikimedia Commons", "wikimedia_search", "concrete utility pole", "struktur_penyangga", 3),
        SystemCSource("wikimedia_electrical_conductor", "Wikimedia Commons", "wikimedia_search", "electrical conductor overhead", "konduktor", 2),
        SystemCSource("wikimedia_distribution_line", "Wikimedia Commons", "wikimedia_search", "distribution line", "konduktor", 2),
        SystemCSource("public_negative_person_vehicle", "Public CC/PD datasets", "manual_legal_dataset", "person vehicle negative", "non_target", 5),
        SystemCSource("public_negative_building_indoor", "Public CC/PD datasets", "manual_legal_dataset", "building indoor object negative", "non_target", 5),
        SystemCSource("ultralytics_openimages_negative", "Ultralytics/OpenImages", "manual_license_verified_dataset", "negative person vehicle building", "non_target", 5),
        SystemCSource("cc_tree_non_sono", "Public CC/PD datasets", "manual_legal_dataset", "non sono tree species", "pohon_non_sono", 4),
        SystemCSource("cc_urban_negative", "Public CC/PD datasets", "manual_legal_dataset", "urban object negative", "non_target", 5),
        SystemCSource("cc_utility_infra", "Public CC/PD datasets", "manual_legal_dataset", "utility infrastructure reference", "struktur_penyangga", 3),
    ]


def registry_as_dicts() -> list[dict[str, Any]]:
    return [source.to_dict() for source in system_c_source_registry()]
