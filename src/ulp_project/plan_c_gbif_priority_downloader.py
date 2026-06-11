"""GBIF priority downloader for Pterocarpus indicus media."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .plan_c_priority_acquisition_config import POHON_SONO_GBIF_DIR, RESTRICTED_DIR, ensure_priority_acquisition_dirs
from .plan_c_priority_source_manifest import (
    ACCEPT_POSITIVE_POHON_SONO_REFERENCE,
    RESTRICTED_REFERENCE_ONLY,
    PriorityImageManifestRecord,
    build_record,
    decide_pohon_sono_status,
    download_url,
    safe_filename,
    write_manifest,
)

GBIF_API = "https://api.gbif.org/v1/occurrence/search"
GBIF_TAXON_KEY = 5349242
USER_AGENT = "ULP-Plan-C-Priority-Acquisition/8.5A"


def collect_gbif_pohon_sono(*, limit: int = 100, download: bool = False) -> dict[str, Any]:
    ensure_priority_acquisition_dirs()
    try:
        data = _gbif_search(limit=limit)
        records = _records_from_gbif(data.get("results", []), download=download)
        manifest = write_manifest(records, stem="pohon_sono_gbif")
        accepted = sum(1 for record in records if record.accepted_status == ACCEPT_POSITIVE_POHON_SONO_REFERENCE)
        return {
            "ok": True,
            "status": "POHON_SONO_CANDIDATES_NOT_ENOUGH" if accepted < 30 else "GBIF_POHON_SONO_MANIFEST_READY",
            "source": "gbif",
            "taxonKey": GBIF_TAXON_KEY,
            "download": download,
            "manifest": manifest,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "SOURCE_UNAVAILABLE_OR_RATE_LIMITED",
            "source": "gbif",
            "error": f"{type(exc).__name__}: {exc}",
            "download": download,
        }


def _gbif_search(*, limit: int) -> dict[str, Any]:
    params = {
        "taxonKey": GBIF_TAXON_KEY,
        "mediaType": "StillImage",
        "limit": min(max(int(limit), 1), 300),
    }
    request = Request(GBIF_API + "?" + urlencode(params), headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _records_from_gbif(items: list[dict[str, Any]], *, download: bool) -> list[PriorityImageManifestRecord]:
    records: list[PriorityImageManifestRecord] = []
    for item in items:
        media_items = item.get("media") if isinstance(item.get("media"), list) else []
        if not media_items:
            records.append(_record_from_item(item, media={}, download=False))
            continue
        for media in media_items:
            if isinstance(media, dict):
                records.append(_record_from_item(item, media=media, download=download))
    return records


def _record_from_item(item: dict[str, Any], *, media: dict[str, Any], download: bool) -> PriorityImageManifestRecord:
    image_url = str(media.get("identifier") or media.get("references") or "")
    license_name = str(media.get("license") or item.get("license") or "")
    source_page = str(item.get("references") or f"https://www.gbif.org/occurrence/{item.get('key', '')}")
    metadata_values = [
        item.get("species"),
        item.get("scientificName"),
        item.get("vernacularName"),
        item.get("acceptedScientificName"),
        media.get("title"),
        media.get("description"),
    ]
    status, target_class, risk_note = decide_pohon_sono_status(license_name=license_name, source_url=source_page, metadata_values=metadata_values)
    folder = RESTRICTED_DIR if status == RESTRICTED_REFERENCE_ONLY else POHON_SONO_GBIF_DIR
    local_path = ""
    image_sha256 = ""
    download_status = "DRY_RUN_NOT_DOWNLOADED"
    if download and status == ACCEPT_POSITIVE_POHON_SONO_REFERENCE and image_url:
        destination = folder / safe_filename(f"gbif_{item.get('key', '')}", image_url, extension=Path(urlparse(image_url).path).suffix)
        try:
            result = download_url(image_url, destination)
            local_path = str(destination)
            image_sha256 = str(result.get("sha256") or "")
            download_status = str(result.get("status") or "DOWNLOADED")
        except Exception as exc:
            download_status = f"DOWNLOAD_FAILED: {type(exc).__name__}"
    elif download and status == RESTRICTED_REFERENCE_ONLY:
        download_status = "DOWNLOAD_SKIPPED_RESTRICTED_LICENSE"

    return build_record(
        source_site="GBIF",
        source_api=GBIF_API,
        source_page_url=source_page,
        image_url=image_url,
        scientific_name=str(item.get("scientificName") or item.get("species") or ""),
        common_name=str(item.get("vernacularName") or ""),
        target_class=target_class,
        country=str(item.get("country") or ""),
        location_text=_location_text(item),
        license=license_name,
        license_url=license_name,
        author=str(media.get("creator") or item.get("recordedBy") or ""),
        attribution=str(media.get("publisher") or item.get("datasetName") or ""),
        rights_holder=str(media.get("rightsHolder") or item.get("rightsHolder") or item.get("publishingOrgKey") or ""),
        accepted_status=status,
        recommended_folder=str(folder),
        download_status=download_status,
        local_path=local_path,
        image_sha256=image_sha256,
        risk_note=f"{risk_note} datasetKey={item.get('datasetKey', '')}; publisher={item.get('publisher', '')}",
    )


def _location_text(item: dict[str, Any]) -> str:
    lat = item.get("decimalLatitude")
    lon = item.get("decimalLongitude")
    if lat is None or lon is None:
        return str(item.get("locality") or "")
    return f"{lat},{lon}"
