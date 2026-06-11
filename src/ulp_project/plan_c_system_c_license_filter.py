"""License and source filtering for System C final dataset pipeline."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

ALLOWED_LICENSES = {
    "cc0",
    "public domain",
    "pd",
    "cc by",
    "cc-by",
    "cc by-sa",
    "cc-by-sa",
    "attribution",
    "attribution-sharealike",
}

RESTRICTED_LICENSES = {
    "cc by-nc",
    "cc-by-nc",
    "cc by-nc-sa",
    "cc-by-nc-sa",
    "cc by-nd",
    "cc-by-nd",
    "cc by-nc-nd",
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
        return {"status": "REJECT_GOOGLE_IMAGES_DIRECT", "training_allowed": False}

    bucket = license_bucket(row.get("license"))
    if bucket == "reject":
        return {"status": "REJECT_LICENSE_UNCLEAR", "training_allowed": False}
    if bucket == "restricted":
        return {"status": "RESTRICTED_REFERENCE_ONLY", "training_allowed": False}

    target = str(row.get("target_class") or "").strip()
    if target == "pohon_sono" and not has_pohon_sono_evidence(
        row.get("scientific_name"),
        row.get("common_name"),
        row.get("source_page_url"),
        row.get("description"),
        row.get("title"),
    ):
        return {"status": "REJECT_NOT_SPECIES_SPECIFIC", "training_allowed": False}
    return {"status": "ACCEPT_TRAINING_REFERENCE", "training_allowed": True}
