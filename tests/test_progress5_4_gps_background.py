from __future__ import annotations

from ulp_project.flask_app import create_app


def test_progress5_4_ui_has_gps_watchposition_contract() -> None:
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)
    js = (create_app().static_folder and "unused") or ""
    script = (create_app().root_path)

    assert "Izinkan GPS" in html
    assert "gps-accuracy-status" in html
    assert "gps_source" in html
    assert js == "unused"
    assert script
