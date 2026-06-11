"""Configuration for Progress 8.5A priority image acquisition."""

from __future__ import annotations

from pathlib import Path

from .paths import PROJECT_ROOT

CLASS_MAPPING = {
    0: "struktur_penyangga",
    1: "konduktor",
    2: "pohon_sono",
    3: "pohon_non_sono",
}

PRIORITY_MAPPING = {
    "pohon_sono": 1,
    "konduktor": 2,
    "struktur_penyangga": 3,
    "negative": 4,
}

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
    "noncommercial",
}

REJECT_LICENSES = {
    "all rights reserved",
    "unknown",
    "no license",
    "unclear",
    "",
}

POHON_SONO_EVIDENCE_TERMS = {
    "pterocarpus indicus",
    "pterocarpus indicus willd",
    "angsana",
    "sonokembang",
    "sono kembang",
    "pohon sono",
    "pohon angsana",
    "narra",
    "amboyna wood",
    "burmese rosewood",
    "malay padauk",
    "papua new guinea rosewood",
}

CONDUCTOR_TERMS = {
    "overhead conductor",
    "distribution line conductor",
    "medium voltage line",
    "20 kv",
    "20kv",
    "power line cable",
    "saluran udara tegangan menengah",
    "sutm",
    "distribution feeder conductor",
    "overhead power line",
}

STRUCTURE_TERMS = {
    "utility pole",
    "electric pole",
    "concrete pole",
    "pole top structure",
    "crossarm",
    "distribution pole",
    "tiang listrik",
    "tiang beton listrik",
    "struktur penyangga",
}

NEGATIVE_TERMS = {
    "person",
    "face",
    "head",
    "chin",
    "car",
    "motorcycle",
    "wall",
    "indoor",
    "cabinet",
    "roof",
    "window",
    "room",
    "charger cable",
}

POHON_SONO_QUERIES = [
    "Pterocarpus indicus",
    '"Pterocarpus indicus tree"',
    '"Pterocarpus indicus leaf"',
    '"Pterocarpus indicus leaves"',
    '"Pterocarpus indicus trunk"',
    '"Pterocarpus indicus bark"',
    '"Pterocarpus indicus crown"',
    '"Pterocarpus indicus canopy"',
    '"Pterocarpus indicus flower"',
    '"Pterocarpus indicus fruit"',
    '"Pterocarpus indicus street tree"',
    '"Pterocarpus indicus roadside"',
    '"Pterocarpus indicus Willd"',
    "Angsana",
    '"Angsana tree"',
    '"pohon angsana"',
    '"daun angsana"',
    '"batang angsana"',
    '"tajuk angsana"',
    '"pohon sono"',
    '"pohon sonokembang"',
    "Sonokembang",
    '"Sonokembang tree"',
    "Narra",
    '"Narra tree"',
    '"Narra leaves"',
    '"Narra trunk"',
    '"Amboyna wood tree"',
    '"Burmese rosewood tree"',
    '"Malay padauk tree"',
    '"Papua New Guinea rosewood"',
    '"Pterocarpus indicus Philippines"',
    '"Pterocarpus indicus Indonesia"',
    '"Pterocarpus indicus Singapore"',
    '"Pterocarpus indicus Malaysia"',
]

CONDUCTOR_QUERIES = [
    "overhead conductor",
    "overhead power line conductor",
    "distribution line conductor",
    "medium voltage conductor",
    "medium voltage distribution line",
    "20 kV distribution line",
    "20kV overhead line",
    "20 kV overhead conductor",
    "power line cable",
    "overhead line wire",
    "distribution feeder conductor",
    "distribution power line",
    "electrical conductors overhead",
    "saluran udara tegangan menengah",
    "SUTM 20 kV",
    "kabel jaringan distribusi",
    "konduktor jaringan distribusi",
    "overhead electrical conductor",
    "three phase overhead line",
    "medium voltage overhead power line",
    "distribution feeder overhead",
]

STRUCTURE_QUERIES = [
    "utility pole",
    "electric pole",
    "concrete utility pole",
    "concrete electric pole",
    "power line pole",
    "distribution pole",
    "medium voltage pole",
    "pole top structure",
    "crossarm",
    "power line crossarm",
    "utility pole crossarm",
    "electric pole crossarm",
    "tiang listrik",
    "tiang beton listrik",
    "struktur penyangga jaringan distribusi",
    "tiang distribusi listrik",
    "pole mounted crossarm",
    "overhead distribution pole",
    "electrical distribution structure",
    "power distribution support structure",
    "utility pole bracket",
]

WIKIMEDIA_POHON_SONO_CATEGORIES = [
    "Category:Pterocarpus indicus",
    "Category:Pterocarpus indicus in the Philippines",
]

WIKIMEDIA_CONDUCTOR_CATEGORIES = [
    "Category:Overhead power lines",
    "Category:Electrical conductors",
    "Category:Distribution lines",
    "Category:Medium-voltage power lines",
]

WIKIMEDIA_STRUCTURE_CATEGORIES = [
    "Category:Utility poles",
    "Category:Electric poles",
    "Category:Power line poles",
    "Category:Concrete utility poles",
    "Category:Crossarms",
]

EXTERNAL_DATASET_INBOX = PROJECT_ROOT / "data" / "external_dataset_inbox"
LEGAL_IMAGES_ROOT = EXTERNAL_DATASET_INBOX / "legal_images"
POHON_SONO_WIKIMEDIA_DIR = LEGAL_IMAGES_ROOT / "pohon_sono_positive_reference" / "wikimedia"
POHON_SONO_GBIF_DIR = LEGAL_IMAGES_ROOT / "pohon_sono_positive_reference" / "gbif"
POHON_SONO_INATURALIST_DIR = LEGAL_IMAGES_ROOT / "pohon_sono_positive_reference" / "inaturalist"
CONDUCTOR_DIR = LEGAL_IMAGES_ROOT / "conductor_20kv_reference"
STRUCTURE_DIR = LEGAL_IMAGES_ROOT / "struktur_penyangga_reference"
NEGATIVE_DIR = LEGAL_IMAGES_ROOT / "negative_reference"
RESTRICTED_DIR = LEGAL_IMAGES_ROOT / "restricted_reference_review_only"

ACQUISITION_RUNTIME_ROOT = PROJECT_ROOT / "data" / "runtime" / "plan_c_dataset_acquisition"
MANIFEST_DIR = ACQUISITION_RUNTIME_ROOT / "manifests"
QUALITY_REPORT_DIR = ACQUISITION_RUNTIME_ROOT / "quality_reports"
PSEUDO_LABEL_DIR = ACQUISITION_RUNTIME_ROOT / "pseudo_labels"
ROBOFLOW_PACKAGE_ROOT = ACQUISITION_RUNTIME_ROOT / "roboflow_package"
YOLOV8_REVIEW_PACKAGE_ROOT = ACQUISITION_RUNTIME_ROOT / "yolov8_review_package"

FOLDER_MAPPING = {
    "pohon_sono_wikimedia": POHON_SONO_WIKIMEDIA_DIR,
    "pohon_sono_gbif": POHON_SONO_GBIF_DIR,
    "pohon_sono_inaturalist": POHON_SONO_INATURALIST_DIR,
    "konduktor": CONDUCTOR_DIR,
    "struktur_penyangga": STRUCTURE_DIR,
    "negative": NEGATIVE_DIR,
    "restricted": RESTRICTED_DIR,
}


def ensure_priority_acquisition_dirs() -> dict[str, str]:
    paths = [
        EXTERNAL_DATASET_INBOX,
        LEGAL_IMAGES_ROOT,
        POHON_SONO_WIKIMEDIA_DIR,
        POHON_SONO_GBIF_DIR,
        POHON_SONO_INATURALIST_DIR,
        CONDUCTOR_DIR,
        STRUCTURE_DIR,
        NEGATIVE_DIR,
        RESTRICTED_DIR,
        ACQUISITION_RUNTIME_ROOT,
        MANIFEST_DIR,
        QUALITY_REPORT_DIR,
        PSEUDO_LABEL_DIR,
        ROBOFLOW_PACKAGE_ROOT,
        YOLOV8_REVIEW_PACKAGE_ROOT,
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
    return {path.name: str(path) for path in paths}
