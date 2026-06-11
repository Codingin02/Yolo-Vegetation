"""System C download manager and manifest writer."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .paths import PROJECT_ROOT
from .plan_c_system_c_license_filter import classify_candidate
from .plan_c_system_c_source_registry import registry_as_dicts

SHARED_DOWNLOAD_ROOT = Path("D:/Users/All Users/Downloads/ULP_Project_PlanC_Dataset_Downloads")
DATASET_FINAL_ROOT = PROJECT_ROOT / "data" / "dataset_yolo" / "plan_c_final_v1"
MANIFEST_DIR = DATASET_FINAL_ROOT / "review"

MANIFEST_FIELDS = [
    "source_id",
    "source_site",
    "adapter",
    "query",
    "source_page_url",
    "image_url",
    "local_path",
    "sha256",
    "target_class",
    "license",
    "author",
    "attribution",
    "accepted_status",
    "download_status",
    "training_allowed",
    "risk_note",
]


def ensure_system_c_dirs() -> None:
    for path in [
        SHARED_DOWNLOAD_ROOT,
        DATASET_FINAL_ROOT,
        DATASET_FINAL_ROOT / "images" / "train",
        DATASET_FINAL_ROOT / "images" / "val",
        DATASET_FINAL_ROOT / "images" / "test",
        DATASET_FINAL_ROOT / "labels" / "train",
        DATASET_FINAL_ROOT / "labels" / "val",
        DATASET_FINAL_ROOT / "labels" / "test",
        DATASET_FINAL_ROOT / "review",
        DATASET_FINAL_ROOT / "rejected",
        DATASET_FINAL_ROOT / "roboflow_package",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def build_empty_manifest_from_registry() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in registry_as_dicts():
        rows.append(
            {
                **source,
                "source_page_url": "",
                "image_url": "",
                "local_path": "",
                "sha256": "",
                "license": "",
                "author": "",
                "attribution": "",
                "accepted_status": "SOURCE_REGISTERED_NOT_DOWNLOADED",
                "download_status": "DRY_RUN_NO_DOWNLOAD",
                "training_allowed": False,
                "risk_note": "Registry entry only; no internet called.",
            }
        )
    return rows


def collect_candidates_from_registry(*, limit_per_source: int = 25, sleep_seconds: float = 0.6) -> dict[str, Any]:
    """Collect legal-source candidates from supported public APIs.

    This function performs network calls only when explicitly invoked by the
    caller. It records source failures instead of fabricating candidates.
    """

    rows: list[dict[str, Any]] = []
    source_status: dict[str, str] = {}
    for source in registry_as_dicts():
        adapter = str(source.get("adapter") or "")
        source_id = str(source.get("source_id") or "")
        try:
            if adapter in {"wikimedia_category", "wikimedia_search"}:
                collected = _collect_wikimedia(source, limit_per_source=limit_per_source)
            elif adapter in {"gbif_occurrence_media", "gbif_backed_occurrence_media"}:
                collected = _collect_gbif(source, limit_per_source=limit_per_source)
            elif adapter == "inaturalist_observations":
                collected = _collect_inaturalist(source, limit_per_source=limit_per_source)
            else:
                collected = []
                source_status[source_id] = "MANUAL_SOURCE_REQUIRES_USER_VERIFIED_DATASET"
            rows.extend(collected)
            if source_id not in source_status:
                source_status[source_id] = "SOURCE_COLLECTED" if collected else "SOURCE_NO_CANDIDATES"
        except Exception as exc:
            source_status[source_id] = f"SOURCE_UNAVAILABLE_OR_RATE_LIMITED:{type(exc).__name__}"
        time.sleep(max(0.0, sleep_seconds))
    return {"rows": rows, "source_status": source_status, "summary": summarize_rows(rows)}


def write_manifest(rows: list[dict[str, Any]], *, stem: str = "system_c_manifest") -> dict[str, Any]:
    ensure_system_c_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = MANIFEST_DIR / f"{stem}_{timestamp}.csv"
    jsonl_path = MANIFEST_DIR / f"{stem}_{timestamp}.jsonl"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(_normalized_row(row))
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_normalized_row(row), ensure_ascii=False) + "\n")
    return {"csv_path": str(csv_path), "jsonl_path": str(jsonl_path), "summary": summarize_rows(rows)}


def download_candidate(row: dict[str, Any], *, timeout: int = 30) -> dict[str, Any]:
    decision = classify_candidate(row)
    if not decision.get("training_allowed"):
        return {**row, **decision, "download_status": "DOWNLOAD_SKIPPED_NOT_ALLOWED"}
    image_url = str(row.get("image_url") or "")
    if not image_url:
        return {**row, **decision, "download_status": "DOWNLOAD_SKIPPED_NO_IMAGE_URL"}
    target = str(row.get("target_class") or "non_target")
    folder = SHARED_DOWNLOAD_ROOT / target
    folder.mkdir(parents=True, exist_ok=True)
    filename = hashlib.sha256(image_url.encode("utf-8")).hexdigest()[:20] + ".jpg"
    destination = folder / filename
    if not destination.exists():
        request = Request(image_url, headers={"User-Agent": "ULP-System-C-Final/8.6"})
        with urlopen(request, timeout=timeout) as response:
            destination.write_bytes(response.read())
    return {
        **row,
        **decision,
        "local_path": str(destination),
        "sha256": sha256_file(destination),
        "download_status": "DOWNLOADED" if destination.exists() else "DOWNLOAD_FAILED",
    }


def _collect_wikimedia(source: dict[str, Any], *, limit_per_source: int) -> list[dict[str, Any]]:
    adapter = str(source.get("adapter") or "")
    query = str(source.get("query") or "")
    if adapter == "wikimedia_category":
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": query,
            "cmtype": "file",
            "cmlimit": min(limit_per_source, 50),
            "format": "json",
        }
        data = _fetch_json("https://commons.wikimedia.org/w/api.php", params)
        titles = [item.get("title") for item in data.get("query", {}).get("categorymembers", []) if item.get("title")]
        return _wikimedia_imageinfo_rows(source, titles)
    params = {
        "action": "query",
        "generator": "search",
        "gsrnamespace": 6,
        "gsrsearch": query,
        "gsrlimit": min(limit_per_source, 50),
        "prop": "imageinfo",
        "iiprop": "url|size|mime|mediatype|extmetadata",
        "format": "json",
    }
    data = _fetch_json("https://commons.wikimedia.org/w/api.php", params)
    pages = data.get("query", {}).get("pages", {})
    return [_wikimedia_page_to_row(source, page) for page in pages.values() if page.get("imageinfo")]


def _wikimedia_imageinfo_rows(source: dict[str, Any], titles: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for start in range(0, len(titles), 25):
        chunk = titles[start : start + 25]
        params = {
            "action": "query",
            "titles": "|".join(chunk),
            "prop": "imageinfo",
            "iiprop": "url|size|mime|mediatype|extmetadata",
            "format": "json",
        }
        data = _fetch_json("https://commons.wikimedia.org/w/api.php", params)
        pages = data.get("query", {}).get("pages", {})
        rows.extend(_wikimedia_page_to_row(source, page) for page in pages.values() if page.get("imageinfo"))
    return rows


def _wikimedia_page_to_row(source: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    imageinfo = (page.get("imageinfo") or [{}])[0]
    meta = imageinfo.get("extmetadata") or {}
    title = str(page.get("title") or meta_value(meta, "ObjectName"))
    description = meta_value(meta, "ImageDescription")
    return {
        **source,
        "title": title,
        "description": description,
        "source_page_url": imageinfo.get("descriptionurl") or "",
        "image_url": imageinfo.get("url") or "",
        "license": meta_value(meta, "LicenseShortName") or meta_value(meta, "UsageTerms"),
        "author": meta_value(meta, "Artist"),
        "attribution": meta_value(meta, "Attribution") or meta_value(meta, "Credit"),
        "scientific_name": "Pterocarpus indicus" if "pterocarpus indicus" in (title + " " + description).lower() else "",
        "download_status": "CANDIDATE_DISCOVERED",
    }


def _collect_gbif(source: dict[str, Any], *, limit_per_source: int) -> list[dict[str, Any]]:
    params = {
        "taxonKey": "5349242",
        "mediaType": "StillImage",
        "limit": min(limit_per_source, 300),
    }
    data = _fetch_json("https://api.gbif.org/v1/occurrence/search", params)
    rows: list[dict[str, Any]] = []
    for item in data.get("results", []):
        for media in item.get("media") or []:
            image_url = media.get("identifier") or media.get("references") or ""
            if not image_url:
                continue
            rows.append(
                {
                    **source,
                    "source_page_url": item.get("references") or f"https://www.gbif.org/occurrence/{item.get('key', '')}",
                    "image_url": image_url,
                    "license": media.get("license") or item.get("license") or "",
                    "author": media.get("creator") or item.get("recordedBy") or "",
                    "attribution": media.get("rightsHolder") or item.get("rightsHolder") or item.get("publisher") or "",
                    "scientific_name": item.get("scientificName") or item.get("species") or "",
                    "country": item.get("country") or "",
                    "download_status": "CANDIDATE_DISCOVERED",
                }
            )
    return rows


def _collect_inaturalist(source: dict[str, Any], *, limit_per_source: int) -> list[dict[str, Any]]:
    query = str(source.get("query") or "Pterocarpus indicus")
    params = {
        "taxon_name": query,
        "photos": "true",
        "per_page": min(limit_per_source, 200),
        "order": "desc",
        "order_by": "created_at",
    }
    data = _fetch_json("https://api.inaturalist.org/v1/observations", params)
    rows: list[dict[str, Any]] = []
    for item in data.get("results", []):
        taxon = item.get("taxon") or {}
        for photo in item.get("photos") or []:
            image_url = str(photo.get("url") or "").replace("square", "original")
            rows.append(
                {
                    **source,
                    "source_page_url": item.get("uri") or "",
                    "image_url": image_url,
                    "license": photo.get("license_code") or item.get("license_code") or "",
                    "author": (item.get("user") or {}).get("login") or "",
                    "attribution": photo.get("attribution") or "",
                    "scientific_name": taxon.get("name") or "",
                    "common_name": taxon.get("preferred_common_name") or query,
                    "location_text": item.get("place_guess") or "",
                    "download_status": "CANDIDATE_DISCOVERED",
                }
            )
    return rows


def _fetch_json(url: str, params: dict[str, Any], *, retries: int = 3, timeout: int = 30) -> dict[str, Any]:
    full_url = f"{url}?{urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(full_url, headers={"User-Agent": "ULP-System-C-Final/8.6"})
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            sleep_for = min(8.0, 1.0 * (2**attempt))
            time.sleep(sleep_for)
    if last_error:
        raise last_error
    return {}


def meta_value(meta: dict[str, Any], key: str) -> str:
    value = meta.get(key) or {}
    if isinstance(value, dict):
        return str(value.get("value") or "")
    return str(value or "")


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_class: dict[str, int] = {}
    downloads = 0
    for row in rows:
        status = str(row.get("accepted_status") or row.get("status") or "UNKNOWN")
        target = str(row.get("target_class") or "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        by_class[target] = by_class.get(target, 0) + 1
        if str(row.get("download_status") or "").startswith("DOWNLOADED"):
            downloads += 1
    return {"total": len(rows), "downloads": downloads, "by_status": by_status, "by_class": by_class}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_row(row: dict[str, Any]) -> dict[str, Any]:
    has_candidate_payload = bool(row.get("image_url") or row.get("source_page_url") or row.get("license"))
    decision = classify_candidate(row) if has_candidate_payload else {}
    accepted_status = row.get("accepted_status") or decision.get("status") or "SOURCE_REGISTERED_NOT_DOWNLOADED"
    return {field: row.get(field, "") for field in MANIFEST_FIELDS} | {
        "accepted_status": accepted_status,
        "training_allowed": bool(row.get("training_allowed", decision.get("training_allowed", False))),
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
