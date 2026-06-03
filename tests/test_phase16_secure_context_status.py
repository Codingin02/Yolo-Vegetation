from ulp_project.flask_app import create_app


def test_secure_context_labels_present():
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)
    assert "HTTPS_SECURE" in html
    assert "HTTP_LAN" in html
    assert "Mulai Deteksi Pohon" in html
