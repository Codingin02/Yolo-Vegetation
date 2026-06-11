"""License and source filtering for System C final dataset pipeline."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

ALLOWED_LICENSES = {
    "by",
    "by-sa",
    "cc0",
    "cc0 1.0",
    "public domain",
    "pd",
    "pdm",
    "cc by",
    "cc-by",
    "cc by-sa",
    "cc by sa",
    "cc-by-sa",
    "attribution",
    "attribution-sharealike",
}

RESTRICTED_LICENSES = {
    "by-nc",
    "by-nc-sa",
    "by-nd",
    "by-nc-nd",
    "cc by-nc",
    "cc by nc",
    "cc-by-nc",
    "cc by-nc-sa",
    "cc by nc sa",
    "cc-by-nc-sa",
    "cc by-nd",
    "cc by nd",
    "cc-by-nd",
    "cc by-nc-nd",
    "cc by nc nd",
    "cc-by-nc-nd",
    "non-commercial",
    "noncommercial",
}

REJECT_LICENSES = {"", "unknown", "no license", "unclear", "all rights reserved"}

POHON_SONO_TERMS = {
    "pterocarpus indicus",
    "pterocarpus indicus willd",
    "angsana",
    "sonokembang",
    "sono kembang",
    "narra",
    "amboyna wood",
    "burmese rosewood",
    "malay padauk",
}

GOOGLE_HOSTS = {"google.com", "www.google.com", "images.google.com"}


def normalize_license(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ")


def license_bucket(value: Any) -> str:
    text = normalize_license(value)
    text = (
        text.replace("https://creativecommons.org/licenses/", "cc ")
        .replace("http://creativecommons.org/licenses/", "cc ")
        .replace("/4.0", "")
        .replace("/3.0", "")
        .replace("/2.0", "")
        .replace("/", " ")
        .replace("-", " ")
    )
    if text in REJECT_LICENSES or "all rights reserved" in text:
        return "reject"
    if any(term in text for term in RESTRICTED_LICENSES):
        return "restricted"
    if any(term in text for term in ALLOWED_LICENSES):
        return "allowed"
    return "reject"


def is_google_images_direct(url: Any) -> bool:
    host = urlparse(str(url or "")).netloc.lower()
    return host in GOOGLE_HOSTS or host.endswith(".googleusercontent.com")


def has_pohon_sono_evidence(*values: Any) -> bool:
    text = " ".join(str(value or "") for value in values).lower()
    return any(term in text for term in POHON_SONO_TERMS)


def classify_candidate(row: dict[str, Any]) -> dict[str, Any]:
    source_url = row.get("source_page_url") or row.get("source_url") or ""
    image_url = row.get("image_url") or ""
    if is_google_images_direct(source_url) or is_google_images_direct(image_url):
        return {"status": "REJECT_GOOGLE_IMAGES_DIRECT", "training_allowed": False, "reason": "Google image URLs are not accepted as a direct source."}

    bucket = license_bucket(row.get("license"))
    if bucket == "reject":
        return {"status": "REJECT_LICENSE_UNCLEAR", "training_allowed": False, "reason": "License is missing, unclear, or not accepted for training."}
    if bucket == "restricted":
        return {"status": "RESTRICTED_REFERENCE_ONLY", "training_allowed": False, "reason": "License is restricted to visual reference only."}

    target = str(row.get("target_class") or "").strip()
    scientific_name = str(row.get("scientific_name") or "").strip().lower()
    source_site = str(row.get("source_site") or "").lower()
    if (
        target == "pohon_sono"
        and scientific_name
        and "pterocarpus indicus" not in scientific_name
        and any(site in source_site for site in ["gbif", "inaturalist", "observation"])
    ):
        return {"status": "REJECT_NOT_SPECIES_SPECIFIC", "training_allowed": False, "reason": "Occurrence taxon is not Pterocarpus indicus."}
    if target == "pohon_sono" and not has_pohon_sono_evidence(
        row.get("scientific_name"),
        row.get("common_name"),
        row.get("query"),
        row.get("source_page_url"),
        row.get("description"),
        row.get("title"),
    ):
        return {"status": "REJECT_NOT_SPECIES_SPECIFIC", "training_allowed": False, "reason": "Pohon sono candidate lacks explicit species/common-name evidence."}
    return {"status": "ACCEPT_TRAINING_REFERENCE", "training_allowed": True, "reason": "License and target metadata passed initial filter."}
