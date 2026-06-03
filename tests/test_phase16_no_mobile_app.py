from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_mobile_app_artifacts_or_pwa_service_worker():
    assert not list(ROOT.rglob("*.apk"))
    assert not list(ROOT.rglob("*.aab"))
    js = (ROOT / "src" / "ulp_project" / "static" / "field_capture.js").read_text(encoding="utf-8")
    assert "serviceWorker" not in js
