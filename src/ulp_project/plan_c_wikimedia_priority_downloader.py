"""Wikimedia Commons priority downloader for Plan C 8.5A."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .plan_c_priority_acquisition_config import (
    CONDUCTOR_DIR,
    POHON_SONO_WIKIMEDIA_DIR,
    RESTRICTED_DIR,
    STRUCTURE_DIR,
    WIKIMEDIA_CONDUCTOR_CATEGORIES,
    WIKIMEDIA_POHON_SONO_CATEGORIES,
    WIKIMEDIA_STRUCTURE_CATEGORIES,
    ensure_priority_acquisition_dirs,
)
from .plan_c_priority_source_manifest import (
    ACCEPT_CONDUCTOR_REFERENCE,
    ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION,
    ACCEPT_POSITIVE_POHON_SONO_REFERENCE,
    ACCEPT_STRUCTURE_REFERENCE,
    RESTRICTED_REFERENCE_ONLY,
    PriorityImageManifestRecord,
    build_record,
    decide_conductor_status,
    decide_pohon_sono_status,
    decide_structure_status,
    download_url,
    safe_filename,
    write_manifest,
)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_FILE_PAGE = "https://commons.wikimedia.org/wiki/{title}"
USER_AGENT = "ULP-Plan-C-Priority-Acquisition/8.5A"


def collect_wikimedia_pohon_sono(*, limit: int = 150, download: bool = False, sleep_seconds: float = 0.5) -> dict[str, Any]:
    return collect_wikimedia_category_targets(
        categories=WIKIMEDIA_POHON_SONO_CATEGORIES,
        limit=limit,
        target="pohon_sono",
        output_dir=POHON_SONO_WIKIMEDIA_DIR,
        manifest_stem="pohon_sono_wikimedia",
        download=download,
        sleep_seconds=sleep_seconds,
    )


def collect_wikimedia_conductor(*, limit: int = 100, download: bool = False, sleep_seconds: float = 0.5) -> dict[str, Any]:
    return collect_wikimedia_category_targets(
        categories=WIKIMEDIA_CONDUCTOR_CATEGORIES,
        limit=limit,
        target="konduktor",
        output_dir=CONDUCTOR_DIR,
        manifest_stem="conductor_wikimedia",
        download=download,
        sleep_seconds=sleep_seconds,
    )


def collect_wikimedia_structure(*, limit: int = 80, download: bool = False, sleep_seconds: float = 0.5) -> dict[str, Any]:
    return collect_wikimedia_category_targets(
        categories=WIKIMEDIA_STRUCTURE_CATEGORIES,
        limit=limit,
        target="struktur_penyangga",
        output_dir=STRUCTURE_DIR,
        manifest_stem="structure_wikimedia",
        download=download,
        sleep_seconds=sleep_seconds,
    )


def collect_wikimedia_category_targets(
    *,
    categories: list[str],
    limit: int,
    target: str,
    output_dir: Path,
    manifest_stem: str,
    download: bool,
    sleep_seconds: float,
) -> dict[str, Any]:
    ensure_priority_acquisition_dirs()
    try:
        titles = _collect_file_titles(categories, limit=limit, sleep_seconds=sleep_seconds)
        records = _records_from_titles(titles[:limit], target=target, output_dir=output_dir, download=download, sleep_seconds=sleep_seconds)
        manifest = write_manifest(records, stem=manifest_stem)
        status = _status_for_target(target, records)
        return {
            "ok": True,
            "status": status,
            "source": "wikimedia",
            "target": target,
            "download": download,
            "candidate_titles": len(titles),
            "manifest": manifest,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "SOURCE_UNAVAILABLE_OR_RATE_LIMITED",
            "source": "wikimedia",
            "target": target,
            "error": f"{type(exc).__name__}: {exc}",
            "download": download,
        }


def _collect_file_titles(categories: list[str], *, limit: int, sleep_seconds: float) -> list[str]:
    titles: list[str] = []
    seen = set()
    for category in categories:
        category_titles = _category_members(category, cmtype="file", limit=max(limit, 50), sleep_seconds=sleep_seconds)
        subcats = _category_members(category, cmtype="subcat", limit=20, sleep_seconds=sleep_seconds)
        for subcat in subcats:
            lowered = subcat.lower()
            if any(term in lowered for term in ["pterocarpus", "indicus", "flower", "fruit", "leaf", "leaves", "wood", "narra", "power", "pole", "line", "conductor"]):
                category_titles.extend(_category_members(subcat, cmtype="file", limit=max(30, limit // 2), sleep_seconds=sleep_seconds))
        for title in category_titles:
            if title not in seen:
                seen.add(title)
                titles.append(title)
            if len(titles) >= limit:
                return titles
    return titles


def _category_members(category: str, *, cmtype: str, limit: int, sleep_seconds: float) -> list[str]:
    titles: list[str] = []
    cmcontinue = ""
    while len(titles) < limit:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": cmtype,
            "cmlimit": min(500, max(1, limit - len(titles))),
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data = _get_json(params)
        for item in data.get("query", {}).get("categorymembers", []):
            title = str(item.get("title") or "")
            if title:
                titles.append(title)
        cmcontinue = data.get("continue", {}).get("cmcontinue", "")
        time.sleep(max(0.0, sleep_seconds))
        if not cmcontinue:
            break
    return titles[:limit]


def _records_from_titles(
    titles: list[str],
    *,
    target: str,
    output_dir: Path,
    download: bool,
    sleep_seconds: float,
) -> list[PriorityImageManifestRecord]:
    records: list[PriorityImageManifestRecord] = []
    for chunk in _chunks(titles, 25):
        pages = _imageinfo(chunk)
        for page in pages:
            record = _page_to_record(page, target=target, output_dir=output_dir, download=download)
            records.append(record)
        time.sleep(max(0.0, sleep_seconds))
    return records


def _imageinfo(titles: list[str]) -> list[dict[str, Any]]:
    data = _get_json(
        {
            "action": "query",
            "prop": "imageinfo|categories",
            "titles": "|".join(titles),
            "iiprop": "url|size|mime|mediatype|extmetadata",
            "cllimit": "max",
            "format": "json",
        }
    )
    pages = data.get("query", {}).get("pages", {})
    return [page for page in pages.values() if isinstance(page, dict)]


def _page_to_record(page: dict[str, Any], *, target: str, output_dir: Path, download: bool) -> PriorityImageManifestRecord:
    title = str(page.get("title") or "")
    info = (page.get("imageinfo") or [{}])[0] if page.get("imageinfo") else {}
    metadata = info.get("extmetadata") or {}
    image_url = str(info.get("url") or "")
    license_name = _meta(metadata, "LicenseShortName") or _meta(metadata, "UsageTerms")
    license_url = _meta(metadata, "LicenseUrl")
    author = _meta(metadata, "Artist")
    attribution = _meta(metadata, "Attribution") or _meta(metadata, "Credit")
    description = _meta(metadata, "ImageDescription")
    object_name = _meta(metadata, "ObjectName")
    categories = " ".join(str(item.get("title") or "") for item in page.get("categories", []) if isinstance(item, dict))
    source_page = COMMONS_FILE_PAGE.format(title=title.replace(" ", "_"))
    metadata_values = [title, description, object_name, categories, attribution, author]

    if target == "pohon_sono":
        status, target_class, risk_note = decide_pohon_sono_status(license_name=license_name, source_url=source_page, metadata_values=metadata_values)
        folder = RESTRICTED_DIR if status == RESTRICTED_REFERENCE_ONLY else output_dir
        scientific_name = "Pterocarpus indicus" if status in {ACCEPT_POSITIVE_POHON_SONO_REFERENCE, RESTRICTED_REFERENCE_ONLY} else ""
        common_name = "pohon_sono"
    elif target == "konduktor":
        status, target_class, risk_note = decide_conductor_status(license_name=license_name, source_url=source_page, metadata_values=metadata_values)
        folder = RESTRICTED_DIR if status == RESTRICTED_REFERENCE_ONLY else output_dir
        scientific_name = ""
        common_name = "overhead conductor"
    else:
        status, target_class, risk_note = decide_structure_status(license_name=license_name, source_url=source_page, metadata_values=metadata_values)
        folder = RESTRICTED_DIR if status == RESTRICTED_REFERENCE_ONLY else output_dir
        scientific_name = ""
        common_name = "utility pole"

    local_path = ""
    image_sha256 = ""
    download_status = "DRY_RUN_NOT_DOWNLOADED"
    if download and status.startswith("ACCEPT_") and image_url:
        destination = folder / safe_filename(title.replace("File:", ""), image_url, extension=Path(urlparse(image_url).path).suffix)
        try:
            result = download_url(image_url, destination)
            local_path = str(destination)
            image_sha256 = str(result.get("sha256") or "")
            download_status = str(result.get("status") or "DOWNLOADED")
        except Exception as exc:
            download_status = f"DOWNLOAD_FAILED: {type(exc).__name__}"
    elif download and status == RESTRICTED_REFERENCE_ONLY and image_url:
        download_status = "DOWNLOAD_SKIPPED_RESTRICTED_LICENSE"

    return build_record(
        source_site="Wikimedia Commons",
        source_api=COMMONS_API,
        source_page_url=source_page,
        image_url=image_url,
        width=int(info.get("width") or 0),
        height=int(info.get("height") or 0),
        scientific_name=scientific_name,
        common_name=common_name,
        target_class=target_class,
        license=license_name,
        license_url=license_url,
        author=author,
        attribution=attribution,
        rights_holder=author,
        accepted_status=status,
        recommended_folder=str(folder),
        download_status=download_status,
        local_path=local_path,
        image_sha256=image_sha256,
        risk_note=risk_note,
    )


def _status_for_target(target: str, records: list[PriorityImageManifestRecord]) -> str:
    accepted = sum(1 for record in records if record.accepted_status.startswith("ACCEPT_"))
    if target == "pohon_sono" and accepted < 30:
        return "POHON_SONO_CANDIDATES_NOT_ENOUGH"
    if target == "konduktor" and accepted < 10:
        return "CONDUCTOR_CANDIDATES_NOT_ENOUGH"
    if target == "struktur_penyangga" and accepted < 10:
        return "STRUCTURE_CANDIDATES_NOT_ENOUGH"
    return "PRIORITY_WIKIMEDIA_MANIFEST_READY"


def _get_json(params: dict[str, Any]) -> dict[str, Any]:
    url = COMMONS_API + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _meta(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if isinstance(value, dict):
        return str(value.get("value") or "").strip()
    return ""


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]
