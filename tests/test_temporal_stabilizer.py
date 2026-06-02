from __future__ import annotations

from ulp_project.temporal_stabilizer import TemporalStabilizer


def test_temporal_stabilizer_waits_then_becomes_stable() -> None:
    stabilizer = TemporalStabilizer(window_size=5, outlier_threshold_m=1.0, min_samples=3)
    assert stabilizer.update(1.0, "LOW")["status"] == "WAITING_FOR_STABLE_SAMPLES"
    assert stabilizer.update(1.1, "MEDIUM")["status"] == "WAITING_FOR_STABLE_SAMPLES"
    result = stabilizer.update(1.05, "HIGH")
    assert result["status"] == "STABLE_READY"
    assert result["risk_priority"] == "HIGH"


def test_temporal_stabilizer_rejects_outlier() -> None:
    stabilizer = TemporalStabilizer(window_size=5, outlier_threshold_m=0.5, min_samples=2)
    stabilizer.update(1.0, "LOW")
    result = stabilizer.update(3.0, "CRITICAL")
    assert result["status"] == "OUTLIER_REJECTED"
