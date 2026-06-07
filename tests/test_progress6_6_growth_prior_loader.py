from __future__ import annotations

from ulp_project.growth_prior_loader import DEFAULT_POHON_SONO_XLSX, growth_prior_dataset_status


def test_progress6_6_growth_prior_loader_reads_proxy_dataset_or_graceful_missing() -> None:
    status = growth_prior_dataset_status()
    assert status["source_status"] == "PROXY_NOT_FIELD_OBSERVED"
    if DEFAULT_POHON_SONO_XLSX.exists():
        assert status["status"] == "GROWTH_PRIOR_READY_PROXY_DATASET"
        assert status["row_count"] > 0
        assert not status["missing_columns"]
    else:
        assert status["status"] == "GROWTH_PRIOR_DATASET_NOT_FOUND"
