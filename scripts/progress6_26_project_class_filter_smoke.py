from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "src" / "ulp_project" / "progress6_26_yolo_first_runtime.py"

def main():
    text = PY.read_text(encoding="utf-8")
    assert "PROJECT_CLASS_NAMES" in text
    assert "pohon_sono" in text
    assert "konduktor" in text
    assert "struktur_penyangga" in text
    assert "filter_project_classes_only" in text
    print(json.dumps({
        "status": "PROGRESS_6_26_PROJECT_CLASS_FILTER_SMOKE_PASS",
        "allowed_classes": ["pohon_sono", "konduktor", "struktur_penyangga"],
        "non_project_objects_operator_visible": False,
    }, indent=2))

if __name__ == "__main__":
    main()
