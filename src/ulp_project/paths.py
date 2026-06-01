"""Central project paths with no-label-touch boundaries."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CONFIGS_DIR = PROJECT_ROOT / "configs"
DOCS_DIR = PROJECT_ROOT / "docs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
METADATA_DIR = DATA_DIR / "metadata"

REVIEW_CANDIDATES_DIR = DATA_DIR / "dataset_yolo" / "00_review_candidates"
DEFAULT_POINT = "V001_pohon_sono"
DEFAULT_POINT_DIR = REVIEW_CANDIDATES_DIR / DEFAULT_POINT
DEFAULT_IMAGE_DIR = DEFAULT_POINT_DIR / "images_selected"
DEFAULT_LABEL_DIR = DEFAULT_POINT_DIR / "labels_selected"
DEFAULT_CLASSES_FILE = DEFAULT_POINT_DIR / "classes.txt"

MAKESENSE_EXPORT_DIR = DATA_DIR / "exports" / "make_sense" / DEFAULT_POINT
FIELD_DATASET_DIR = DATA_DIR / "dataset_yolo" / "field_multiclass_v1"
FIELD_DATA_YAML = FIELD_DATASET_DIR / "data.yaml"
GPS_FIELD_POINTS_DIR = DATA_DIR / "gps" / "01_field_points"
RESULTS_MAP_DIR = PROJECT_ROOT / "results" / "maps"

DATASET_BOTOL_DIR = PROJECT_ROOT / "dataset_botol"

NO_TOUCH_PATHS = [
    REVIEW_CANDIDATES_DIR,
    DATA_DIR / "raw",
    DATA_DIR / "gps",
    DATA_DIR / "processed",
    DATA_DIR / "exports",
    DATASET_BOTOL_DIR,
]


def point_dir(point: str) -> Path:
    return REVIEW_CANDIDATES_DIR / point


def image_dir_for_point(point: str) -> Path:
    return point_dir(point) / "images_selected"


def label_dir_for_point(point: str) -> Path:
    return point_dir(point) / "labels_selected"


def classes_file_for_point(point: str) -> Path:
    return point_dir(point) / "classes.txt"


def export_dir_for_point(point: str) -> Path:
    return DATA_DIR / "exports" / "make_sense" / point


def as_posix_path(path: Path) -> str:
    return path.resolve().as_posix()
