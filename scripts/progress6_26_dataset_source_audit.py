from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "metadata" / "progress6_26_dataset_source_audit.json"

SOURCES = [
    {
        "target": "pohon_sono",
        "query_names": ["Pterocarpus indicus", "angsana", "sonokembang", "pohon sono"],
        "candidate_sources": ["GBIF", "iNaturalist", "Wikimedia Commons"],
        "policy": "REVIEW_REQUIRED_NOT_GROUND_TRUTH",
    },
    {
        "target": "konduktor",
        "query_names": ["utility line", "power line", "overhead conductor"],
        "candidate_sources": ["Open Images", "field data"],
        "policy": "REVIEW_REQUIRED_NOT_ALWAYS_PLN_DISTRIBUTION_CONDUCTOR",
    },
    {
        "target": "struktur_penyangga",
        "query_names": ["utility pole", "distribution pole", "power pole"],
        "candidate_sources": ["Open Images", "field data"],
        "policy": "REVIEW_REQUIRED_MATCH_WITH_PLN_FIELD_STRUCTURE",
    },
]

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PROGRESS_6_26_DATASET_SOURCE_AUDIT_READY",
        "download_performed": False,
        "training_performed": False,
        "label_touch": False,
        "sources": SOURCES,
        "next_action": "Use only as candidate references. Review manually before training.",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
