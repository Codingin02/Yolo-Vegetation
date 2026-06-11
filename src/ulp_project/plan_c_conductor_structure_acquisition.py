"""Second and third priority acquisition for conductor and support structure."""

from __future__ import annotations

from typing import Any

from .plan_c_wikimedia_priority_downloader import collect_wikimedia_conductor, collect_wikimedia_structure


def acquire_conductor_references(*, limit: int = 100, download: bool = False) -> dict[str, Any]:
    """Acquire legal overhead conductor references.

    The result can be generic distribution reference. It is only 20 kV verified
    when source metadata explicitly mentions 20 kV.
    """

    result = collect_wikimedia_conductor(limit=limit, download=download)
    result["priority_stage"] = "2_conductor_after_pohon_sono"
    result["twenty_kv_claim_policy"] = "ONLY_IF_METADATA_EXPLICITLY_MENTIONS_20KV"
    return result


def acquire_structure_references(*, limit: int = 80, download: bool = False) -> dict[str, Any]:
    """Acquire legal utility pole/crossarm references after conductor search."""

    result = collect_wikimedia_structure(limit=limit, download=download)
    result["priority_stage"] = "3_structure_after_conductor"
    return result
