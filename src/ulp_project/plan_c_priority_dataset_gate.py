"""Dataset readiness gate for Progress 8.5A priority acquisition."""

from __future__ import annotations

from typing import Any

from .plan_c_priority_source_manifest import (
    ACCEPT_CONDUCTOR_REFERENCE,
    ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION,
    ACCEPT_POSITIVE_POHON_SONO_REFERENCE,
    ACCEPT_STRUCTURE_REFERENCE,
    RESTRICTED_REFERENCE_ONLY,
    classify_license,
    is_google_images_direct,
    latest_manifest_rows,
)

THRESHOLDS = {
    "pohon_sono": 30,
    "konduktor": 10,
    "struktur_penyangga": 10,
}

FORBIDDEN_STAGED_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".zip", ".pt", ".onnx", ".engine")
FORBIDDEN_STAGED_PREFIXES = (
    "data/external_dataset_inbox/",
    "data/runtime/",
    "data/raw/",
    "data/gps/",
    "data/processed/",
    "data/dataset_yolo/",
    "dataset_botol/",
    "runs/",
    "weights/",
    "models/",
)


def run_priority_dataset_gate(*, rows: list[dict[str, Any]] | None = None, staged_paths: list[str] | None = None) -> dict[str, Any]:
    rows = rows if rows is not None else latest_manifest_rows()
    staged_paths = staged_paths or []
    counts = _accepted_counts(rows)
    issues = _manifest_issues(rows)
    staged_issues = _forbidden_staged_paths(staged_paths)
    ready = (
        counts["pohon_sono"] >= THRESHOLDS["pohon_sono"]
        and counts["konduktor"] >= THRESHOLDS["konduktor"]
        and counts["struktur_penyangga"] >= THRESHOLDS["struktur_penyangga"]
        and not issues
        and not staged_issues
    )
    return {
        "ok": True,
        "status": "PLAN_C_PRIORITY_DATASET_READY_FOR_ROBOFLOW_REVIEW" if ready else "PLAN_C_PRIORITY_DATASET_NOT_ENOUGH",
        "not_ready_for_final_training": True,
        "thresholds": THRESHOLDS,
        "accepted_counts": counts,
        "restricted_count": sum(1 for row in rows if row.get("accepted_status") == RESTRICTED_REFERENCE_ONLY),
        "rejected_count": sum(1 for row in rows if not str(row.get("accepted_status", "")).startswith("ACCEPT_") and row.get("accepted_status") != RESTRICTED_REFERENCE_ONLY),
        "manifest_issues": issues[:100],
        "forbidden_staged_paths": staged_issues,
        "no_final_training": True,
        "pseudo_label_policy": "review-only",
    }


def _accepted_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pohon_sono": 0, "konduktor": 0, "struktur_penyangga": 0, "negative": 0}
    for row in rows:
        status = str(row.get("accepted_status") or "")
        target = str(row.get("target_class") or "")
        if status == ACCEPT_POSITIVE_POHON_SONO_REFERENCE and target == "pohon_sono":
            counts["pohon_sono"] += 1
        elif status in {ACCEPT_CONDUCTOR_REFERENCE, ACCEPT_CONDUCTOR_REFERENCE_GENERIC_DISTRIBUTION} and target == "konduktor":
            counts["konduktor"] += 1
        elif status == ACCEPT_STRUCTURE_REFERENCE and target == "struktur_penyangga":
            counts["struktur_penyangga"] += 1
        elif status.startswith("ACCEPT_") and target == "negative":
            counts["negative"] += 1
    return counts


def _manifest_issues(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        status = str(row.get("accepted_status") or "")
        if not status.startswith("ACCEPT_"):
            continue
        if is_google_images_direct(row.get("source_page_url")) or is_google_images_direct(row.get("image_url")):
            issues.append({"row": str(index), "issue": "GOOGLE_IMAGES_DIRECT_ACCEPTED"})
        if classify_license(row.get("license")) != "allowed":
            issues.append({"row": str(index), "issue": "UNKNOWN_OR_RESTRICTED_LICENSE_ACCEPTED"})
        if not row.get("source_page_url") or not row.get("image_url"):
            issues.append({"row": str(index), "issue": "SOURCE_OR_IMAGE_URL_MISSING"})
        if not row.get("author") and not row.get("attribution") and not row.get("rights_holder"):
            issues.append({"row": str(index), "issue": "ATTRIBUTION_MISSING"})
        if row.get("target_class") == "pohon_sono" and row.get("scientific_name") and "pterocarpus indicus" not in str(row.get("scientific_name")).lower():
            issues.append({"row": str(index), "issue": "POHON_SONO_SCIENTIFIC_NAME_AMBIGUOUS"})
    return issues


def _forbidden_staged_paths(paths: list[str]) -> list[str]:
    flagged: list[str] = []
    for raw in paths:
        path = str(raw or "").replace("\\", "/").lower()
        if path.endswith(FORBIDDEN_STAGED_SUFFIXES) or any(path.startswith(prefix) for prefix in FORBIDDEN_STAGED_PREFIXES):
            flagged.append(raw)
    return flagged
