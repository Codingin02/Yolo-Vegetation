"""iNaturalist priority downloader for Pterocarpus indicus candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .plan_c_priority_acquisition_config import POHON_SONO_INATURALIST_DIR, RESTRICTED_DIR, ensure_priority_acquisition_dirs
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

INAT_API = "https://api.inaturalist.org/v1/observations"
USER_AGENT = "ULP-Plan-C-Priority-Acquisition/8.5A"


def collect_inaturalist_pohon_sono(*, limit: int = 100, download: bool = False) -> dict[str, Any]:
    ensure_priority_acquisition_dirs()
    try:
        data = _inat_search(limit=limit)
        records = _records_from_results(data.get("results", []), download=download)
        manifest = write_manifest(records, stem="pohon_sono_inaturalist")
        accepted = sum(1 for record in records if record.accepted_status == ACCEPT_POSITIVE_POHON_SONO_REFERENCE)
        return {
            "ok": True,
            "status": "POHON_SONO_CANDIDATES_NOT_ENOUGH" if accepted < 30 else "INATURALIST_POHON_SONO_MANIFEST_READY",
            "source": "inaturalist",
            "download": download,
            "manifest": manifest,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "SOURCE_UNAVAILABLE_OR_RATE_LIMITED",
            "source": "inaturalist",
            "error": f"{type(exc).__name__}: {exc}",
            "download": download,
        }


def _inat_search(*, limit: int) -> dict[str, Any]:
    params = {
        "taxon_name": "Pterocarpus indicus",
        "photos": "true",
        "per_page": min(max(int(limit), 1), 200),
        "order": "desc",
        "order_by": "created_at",
    }
    request = Request(INAT_API + "?" + urlencode(params), headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _records_from_results(results: list[dict[str, Any]], *, download: bool) -> list[PriorityImageManifestRecord]:
    records: list[PriorityImageManifestRecord] = []
    for item in results:
        photos = item.get("photos") if isinstance(item.get("photos"), list) else []
        if not photos:
            continue
        for photo in photos:
            if isinstance(photo, dict):
                records.append(_record_from_photo(item, photo, download=download))
    return records


def _record_from_photo(item: dict[str, Any], photo: dict[str, Any], *, download: bool) -> PriorityImageManifestRecord:
    taxon = item.get("taxon") if isinstance(item.get("taxon"), dict) else {}
    license_name = str(photo.get("license_code") or item.get("license_code") or "")
    observation_url = str(item.get("uri") or "")
    image_url = _photo_url(photo)
    metadata_values = [
        taxon.get("name"),
        taxon.get("preferred_common_name"),
        taxon.get("english_common_name"),
        item.get("description"),
        item.get("place_guess"),
    ]
    status, target_class, risk_note = decide_pohon_sono_status(license_name=license_name, source_url=observation_url, metadata_values=metadata_values)
    folder = RESTRICTED_DIR if status == RESTRICTED_REFERENCE_ONLY else POHON_SONO_INATURALIST_DIR
    local_path = ""
    image_sha256 = ""
    download_status = "DRY_RUN_NOT_DOWNLOADED"
    if download and status == ACCEPT_POSITIVE_POHON_SONO_REFERENCE and image_url:
        destination = folder / safe_filename(f"inaturalist_{item.get('id', '')}_{photo.get('id', '')}", image_url, extension=Path(urlparse(image_url).path).suffix)
        try:
            result = download_url(image_url, destination)
            local_path = str(destination)
            image_sha256 = str(result.get("sha256") or "")
            download_status = str(result.get("status") or "DOWNLOADED")
        except Exception as exc:
            download_status = f"DOWNLOAD_FAILED: {type(exc).__name__}"
    elif download and status == RESTRICTED_REFERENCE_ONLY:
        download_status = "DOWNLOAD_SKIPPED_RESTRICTED_LICENSE"

    user = item.get("user") if isinstance(item.get("user"), dict) else {}
    return build_record(
        source_site="iNaturalist",
        source_api=INAT_API,
        source_page_url=observation_url,
        image_url=image_url,
        width=int(photo.get("width") or 0),
        height=int(photo.get("height") or 0),
        scientific_name=str(taxon.get("name") or ""),
        common_name=str(taxon.get("preferred_common_name") or taxon.get("english_common_name") or ""),
        target_class=target_class,
        country="",
        location_text=str(item.get("place_guess") or ""),
        license=license_name,
        license_url=f"https://creativecommons.org/licenses/{license_name}/" if license_name else "",
        author=str(user.get("login") or ""),
        attribution=str(photo.get("attribution") or user.get("login") or ""),
        rights_holder=str(photo.get("attribution") or user.get("login") or ""),
        accepted_status=status,
        recommended_folder=str(folder),
        download_status=download_status,
        local_path=local_path,
        image_sha256=image_sha256,
        risk_note=risk_note,
    )


def _photo_url(photo: dict[str, Any]) -> str:
    url = str(photo.get("url") or photo.get("original_url") or "")
    if not url:
        return ""
    return url.replace("square.", "large.")
