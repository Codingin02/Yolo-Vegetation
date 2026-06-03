from scripts.operator_command_center import render_command_center


def test_operator_command_center_includes_final_commands():
    text = render_command_center()
    assert "phase16_remote_realtime_streaming_gate.py" in text
    assert "phase5_2_field_trial_prediction_gate.py" in text
    assert "run_remote_realtime_server.py" in text
