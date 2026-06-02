from scripts.phase8_pln_realtime_risk_gate import build_phase8_gate_status


def test_phase8_gate_reports_ready_waiting_for_real_inputs():
    result = build_phase8_gate_status()
    assert result["overall_status"] == "PHASE8_PLN_REALTIME_RISK_SYSTEM_READY_WAITING_FOR_MODEL_LABELS_AND_REAL_ENV_DATA"
    assert result["manual_eta_days_p50"] == 30.0
    assert result["manual_risk_priority"] == "CRITICAL"
    assert result["map_without_gps_status"] == "NO_MARKER_WITHOUT_GPS"
