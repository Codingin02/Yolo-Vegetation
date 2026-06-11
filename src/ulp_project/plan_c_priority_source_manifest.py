"""Manifest schema and legal filters for Progress 8.5A acquisition."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .plan_c_priority_acquisition_config import (
    ALLOWED_LICENSES,
    CONDUCTOR_TERMS,
    MANIFEST_DIR,
    POHON_SONO_EVIDENCE_TERMS,
    PRIORITY_MAPPING,
    REJECT_LICENSES,
    RESTRICTED_LICENSES,
    STRUCTURE_TERMS,
    ensure_priority_acquisition_dirs,
)

ACCEPT_POSITIVE_POHON_SONO_REFERENCE = "ACCEPT_POSITIVE_POHON_SONO_REFERENCE"
ACCEPT_CONDUCTOR_REFERENCE = "ACCEPT_CONDUCTOR_REFERENCE"
ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION = "ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION"
ACCEPT_STRUCTURE_REFERENCE = "ACCEPT_STRUCTURE_REFERENCE"
ACCEPT_NEGATIVE_REFERENCE = "ACCEPT_NEGATIVE_REFERENCE"
RESTRICTED_REFERENCE_ONLY = "RESTRICTED_REFERENCE_ONLY"
REJECT_LICENSE_UNCLEAR = "REJECT_LICENSE_UNCLEAR"
REJECT_NOT_SPECIES_SPECIFIC = "REJECT_NOT_SPECIES_SPECIFIC"
REJECT_LOW_QUALITY = "REJECT_LOW_QUALITY"
REJECT_WRONG_OBJECT = "REJECT_WRONG_OBJECT"
REJECT_GOOGLE_IMAGES_DIRECT = "REJECT_GOOGLE_IMAGES_DIRECT"

MANIFEST_FIELDS = [
    "source_site",
    "source_api",
    "source_page_url",
    "image_url",
    "local_path",
    "image_sha256",
    "width",
    "height",
    "scientific_name",
    "common_name",
    "target_class",
    "priority",
    "country",
    "location_text",
    "license",
    "license_url",
    "author",
    "attribution",
    "rights_holder",
    "accepted_status",
    "recommended_folder",
    "download_status",
    "pseudo_label_status",
    "roboflow_status",
    "risk_note",
    "created_at",
]


@dataclass
class PriorityImageManifestRecord:
    source_site: str = ""
    source_api: str = ""
    source_page_url: str = ""
    image_url: str = ""
    local_path: str = ""
    image_sha256: str = ""
    width: int = 0
    height: int = 0
    scientific_name: str = ""
    common_name: str = ""
    target_class: str = ""
    priority: int = 4
    country: str = ""
    location_text: str = ""
    license: str = ""
    license_url: str = ""
    author: str = ""
    attribution: str = ""
    rights_holder: str = ""
    accepted_status: str = ""
    recommended_folder: str = ""
    download_status: str = "DRY_RUN_NOT_DOWNLOADED"
    pseudo_label_status: str = "PSEUDO_LABEL_NOT_CREATED"
    roboflow_status: str = "ROBOFLOW_NOT_PACKAGED"
    risk_note: str = ""
    created_at: str = ""

    def to_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["created_at"] = row.get("created_at") or utc_now_iso()
        return {field: row.get(field, "") for field in MANIFEST_FIELDS}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_license(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip().lower())
    text = text.replace("cc-by", "cc by").replace("cc-by-sa", "cc by-sa").replace("cc-by-nc", "cc by-nc")
    return text


def classify_license(value: Any) -> str:
    text = normalize_license(value)
    if text in REJECT_LICENSES or not text:
        return "reject"
    if any(term in text for term in RESTRICTED_LICENSES):
        return "restricted"
    if "all rights reserved" in text or "unknown" in text or "no license" in text:
        return "reject"
    if "public domain" in text or text in {"pd", "cc0"} or "cc0" in text:
        return "allowed"
    if any(term in text for term in ALLOWED_LICENSES):
        return "allowed"
    return "reject"


def is_google_images_direct(url: Any) -> bool:
    host = urlparse(str(url or "")).netloc.lower()
    return host in {"images.google.com", "www.google.com", "google.com"} or host.endswith(".googleusercontent.com")


def contains_species_evidence(*values: Any) -> bool:
    text = _joined_text(values)
    return any(term in text for term in POHON_SONO_EVIDENCE_TERMS)


def contains_conductor_evidence(*values: Any) -> bool:
    text = _joined_text(values)
    return any(term in text for term in CONDUCTOR_TERMS)


def contains_structure_evidence(*values: Any) -> bool:
    text = _joined_text(values)
    return any(term in text for term in STRUCTURE_TERMS)


def decide_pohon_sono_status(*, license_name: str, source_url: str, metadata_values: list[Any]) -> tuple[str, str, str]:
    if is_google_images_direct(source_url):
        return REJECT_GOOGLE_IMAGES_DIRECT, "negative", "Google Images direct URL is not allowed."
    license_class = classify_license(license_name)
    if license_class == "reject":
        return REJECT_LICENSE_UNCLEAR, "negative", "License is not accepted for acquisition."
    if not contains_species_evidence(*metadata_values):
        return REJECT_NOT_SPECIES_SPECIFIC, "negative", "Metadata does not prove Pterocarpus indicus/Angsana/Narra/Sonokembang."
    if license_class == "restricted":
        return RESTRICTED_REFERENCE_ONLY, "pohon_sono", "Restricted license; reference review only, not final training."
    return ACCEPT_POSITIVE_POHON_SONO_REFERENCE, "pohon_sono", "Species evidence and license accepted."


def decide_conductor_status(*, license_name: str, source_url: str, metadata_values: list[Any]) -> tuple[str, str, str]:
    if is_google_images_direct(source_url):
        return REJECT_GOOGLE_IMAGES_DIRECT, "negative", "Google Images direct URL is not allowed."
    license_class = classify_license(license_name)
    if license_class == "reject":
        return REJECT_LICENSE_UNCLEAR, "negative", "License is not accepted for acquisition."
    if not contains_conductor_evidence(*metadata_values):
        return REJECT_WRONG_OBJECT, "negative", "Metadata does not identify overhead conductor/distribution line."
    text = _joined_text(metadata_values)
    accepted = ACCEPT_CONDUCTOR_REFERENCE if "20 kv" in text or "20kv" in text else ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION
    if license_class == "restricted":
        return RESTRICTED_REFERENCE_ONLY, "konduktor", "Restricted license; conductor reference only."
    return accepted, "konduktor", "Conductor reference accepted; 20kV only if metadata explicitly says so."


def decide_structure_status(*, license_name: str, source_url: str, metadata_values: list[Any]) -> tuple[str, str, str]:
    if is_google_images_direct(source_url):
        return REJECT_GOOGLE_IMAGES_DIRECT, "negative", "Google Images direct URL is not allowed."
    license_class = classify_license(license_name)
    if license_class == "reject":
        return REJECT_LICENSE_UNCLEAR, "negative", "License is not accepted for acquisition."
    if not contains_structure_evidence(*metadata_values):
        return REJECT_WRONG_OBJECT, "negative", "Metadata does not identify utility pole/crossarm/support structure."
    if license_class == "restricted":
        return RESTRICTED_REFERENCE_ONLY, "struktur_penyangga", "Restricted license; structure reference only."
    return ACCEPT_STRUCTURE_REFERENCE, "struktur_penyangga", "Structure reference accepted."


def write_manifest(records: list[PriorityImageManifestRecord], *, stem: str) -> dict[str, Any]:
    ensure_priority_acquisition_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = MANIFEST_DIR / f"{stem}_{timestamp}.csv"
    jsonl_path = MANIFEST_DIR / f"{stem}_{timestamp}.jsonl"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_row())
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_row(), ensure_ascii=False) + "\n")
    return {
        "csv_path": str(csv_path),
        "jsonl_path": str(jsonl_path),
        "summary": summarize_records(records),
    }


def summarize_records(records: list[PriorityImageManifestRecord]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total": len(records),
        "accepted": 0,
        "restricted": 0,
        "rejected": 0,
        "by_status": {},
        "by_class": {},
    }
    for record in records:
        status = record.accepted_status
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        summary["by_class"][record.target_class] = summary["by_class"].get(record.target_class, 0) + 1
        if status.startswith("ACCEPT_"):
            summary["accepted"] += 1
        elif status == RESTRICTED_REFERENCE_ONLY:
            summary["restricted"] += 1
        else:
            summary["rejected"] += 1
    return summary


def latest_manifest_rows() -> list[dict[str, str]]:
    if not MANIFEST_DIR.exists():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(MANIFEST_DIR.glob("*.csv")):
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows.extend(dict(row) for row in csv.DictReader(handle))
    return rows


def accepted_for_packaging(rows: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    rows = rows if rows is not None else latest_manifest_rows()
    return [
        row
        for row in rows
        if str(row.get("accepted_status", "")).startswith("ACCEPT_")
        and row.get("target_class") in {"struktur_penyangga", "konduktor", "pohon_sono", "pohon_non_sono", "negative"}
    ]


def safe_filename(prefix: str, url: str, extension: str = ".jpg") -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", prefix).strip("_")[:60] or "image"
    ext = extension.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    return f"{cleaned}_{digest}{ext}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_url(url: str, destination: Path, *, timeout: int = 30) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return {"status": "FILE_EXISTS_NOT_OVERWRITTEN", "path": str(destination), "sha256": sha256_file(destination)}
    request = Request(url, headers={"User-Agent": "ULP-Plan-C-Priority-Acquisition/8.5A"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
    destination.write_bytes(data)
    return {"status": "DOWNLOADED", "path": str(destination), "sha256": sha256_file(destination), "bytes": len(data)}


def build_record(
    *,
    source_site: str,
    source_api: str,
    source_page_url: str,
    image_url: str,
    width: int = 0,
    height: int = 0,
    scientific_name: str = "",
    common_name: str = "",
    target_class: str,
    country: str = "",
    location_text: str = "",
    license: str = "",
    license_url: str = "",
    author: str = "",
    attribution: str = "",
    rights_holder: str = "",
    accepted_status: str = "",
    recommended_folder: str = "",
    download_status: str = "DRY_RUN_NOT_DOWNLOADED",
    local_path: str = "",
    image_sha256: str = "",
    risk_note: str = "",
) -> PriorityImageManifestRecord:
    return PriorityImageManifestRecord(
        source_site=source_site,
        source_api=source_api,
        source_page_url=source_page_url,
        image_url=image_url,
        local_path=local_path,
        image_sha256=image_sha256,
        width=int(width or 0),
        height=int(height or 0),
        scientific_name=scientific_name,
        common_name=common_name,
        target_class=target_class,
        priority=PRIORITY_MAPPING.get(target_class, 4),
        country=country,
        location_text=location_text,
        license=license,
        license_url=license_url,
        author=author,
        attribution=attribution,
        rights_holder=rights_holder,
        accepted_status=accepted_status,
        recommended_folder=recommended_folder,
        download_status=download_status,
        risk_note=risk_note,
        created_at=utc_now_iso(),
    )


def _joined_text(values: list[Any] | tuple[Any, ...]) -> str:
    return re.sub(r"\s+", " ", " ".join(str(value or "") for value in values)).lower()
