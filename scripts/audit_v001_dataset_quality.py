from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.classes import CLASS_ORDER  # noqa: E402
from ulp_project.yolo_label_audit import audit_yolo_folder, compute_box_area_stats, detect_class_coverage_risk  # noqa: E402

PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
V001_IMAGE_DIR = PROJECT_ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "images_selected"
V001_LABEL_DIR = PROJECT_ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "labels_selected"
FIELD_DATASET = PROJECT_ROOT / "data" / "dataset_yolo" / "field_multiclass_v1"
REPORT_PATH = PROJECT_ROOT / "data" / "metadata" / "v001_dataset_quality_report.json"


def build_report() -> dict:
    selected_audit = audit_yolo_folder(V001_IMAGE_DIR, V001_LABEL_DIR, CLASS_ORDER)
    train_audit = audit_yolo_folder(FIELD_DATASET / "images" / "train", FIELD_DATASET / "labels" / "train", CLASS_ORDER)
    val_audit = audit_yolo_folder(FIELD_DATASET / "images" / "val", FIELD_DATASET / "labels" / "val", CLASS_ORDER)
    coverage = detect_class_coverage_risk(FIELD_DATASET / "labels" / "train", FIELD_DATASET / "labels" / "val")
    area_stats = compute_box_area_stats(V001_LABEL_DIR)
    selected_counts = selected_audit["class_counts"]
    train_counts = train_audit["class_counts"]
    val_counts = val_audit["class_counts"]
    struktur_total = int(train_counts.get(0, 0)) + int(val_counts.get(0, 0))
    konduktor_total = int(train_counts.get(1, 0)) + int(val_counts.get(1, 0))
    pohon_total = int(train_counts.get(2, 0)) + int(val_counts.get(2, 0))
    return {
        "status": "MODEL_NOT_USABLE_FOR_RUNTIME",
        "runtime_model_status": "MODEL_UNSTABLE_LOW_CONF",
        "summary": {
            "field_multiclass_v1": "technically valid but not reliable for multiclass runtime",
            "struktur_penyangga": "not ready because only 1 instance exists and none are in validation",
            "konduktor": "not yet reliable for runtime despite labels because validation evidence is still weak",
            "pohon_sono": "only feasible initial target for this recovery cycle",
            "no_final_accuracy_claim": True,
        },
        "selected_v001": selected_audit,
        "field_multiclass_v1": {
            "data_yaml_exists": (FIELD_DATASET / "data.yaml").exists(),
            "train": train_audit,
            "val": val_audit,
            "coverage_risk": coverage,
            "split_counts": {
                "train_images": train_audit["image_count"],
                "train_labels": train_audit["label_count"],
                "val_images": val_audit["image_count"],
                "val_labels": val_audit["label_count"],
            },
        },
        "class_distribution_selected": {
            CLASS_ORDER[class_id]: int(selected_counts.get(class_id, 0)) for class_id in CLASS_ORDER
        },
        "class_distribution_train_val": {
            "struktur_penyangga": struktur_total,
            "konduktor": konduktor_total,
            "pohon_sono": pohon_total,
        },
        "box_area_stats_selected": area_stats,
        "decision": "build v001_pohon_sono_only_v1 and keep multiclass model out of runtime readiness",
        "no_fake_label": True,
        "no_fake_detection": True,
    }


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    counts = report["class_distribution_selected"]
    split = report["field_multiclass_v1"]["split_counts"]
    print("V001 dataset quality audit")
    print(f"report_json: {REPORT_PATH}")
    print(f"selected_images: {report['selected_v001']['image_count']}")
    print(f"selected_labels: {report['selected_v001']['label_count']}")
    print(f"selected_status: {report['selected_v001']['status']}")
    print("class_distribution_selected:")
    for name, count in counts.items():
        print(f"  {name}: {count}")
    print("field_multiclass_v1_split:")
    for key, value in split.items():
        print(f"  {key}: {value}")
    print("diagnosis:")
    print("  field_multiclass_v1 technically valid, tetapi tidak reliable untuk multiclass runtime.")
    print("  struktur_penyangga belum siap: hanya 1 instance total dan 0 di validation.")
    print("  konduktor belum reliable untuk runtime.")
    print("  pohon_sono adalah target awal yang paling feasible untuk V001.")
    print("status: MODEL_NOT_USABLE_FOR_RUNTIME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
