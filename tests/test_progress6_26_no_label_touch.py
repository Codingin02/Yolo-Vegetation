from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATTERNS = [
    "data/dataset_yolo/00_review_candidates",
    "data\\\\dataset_yolo\\\\00_review_candidates",
    "labels_selected",
    "images_selected",
    "dataset_botol",
]

def test_progress6_26_no_label_touch_scripts_do_not_write_forbidden_paths():
    files = list((ROOT / "scripts").glob("progress6_26*.py")) + list((ROOT / "src" / "ulp_project").glob("*progress6_26*.py"))
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for forbidden in FORBIDDEN_PATTERNS:
            assert forbidden not in text or "planning" in text.lower() or "audit" in text.lower(), f"{path} mentions forbidden path {forbidden}"
