from ulp_project.runtime_diagnostics import collect_remote_field_trial_diagnostics


def test_remote_diagnostics_ready():
    result = collect_remote_field_trial_diagnostics()
    assert result["status"] == "REMOTE_FIELD_TRIAL_DIAGNOSTICS_READY"
    assert result["no_label_touch"] is True
