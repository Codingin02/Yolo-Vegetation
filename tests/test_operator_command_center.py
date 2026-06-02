from scripts.operator_command_center import render_command_center


def test_operator_command_center_groups_safe_and_blocked_commands():
    text = render_command_center()
    assert "SAFE NOW" in text
    assert "WAIT UNTIL MAKESENSE EXPORT" in text
    assert "WAIT UNTIL LABEL VALIDATION" in text
    assert "WAIT UNTIL EXPLICIT TRAINING APPROVAL" in text
    assert "train_yolov8_field_multiclass.py --run" in text
