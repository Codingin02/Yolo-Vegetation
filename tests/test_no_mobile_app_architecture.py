from pathlib import Path


def test_no_apk_flutter_or_react_native_files_added():
    forbidden = {".apk", ".aab"}
    roots = [Path("src"), Path("scripts"), Path("configs"), Path("docs"), Path("tests")]
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if ".git" in path.parts or "venv" in path.parts:
                continue
            if path.name in {"mobile_upload.py", "mobile_result.py", "test_mobile_upload_contract.py", "test_phase6_mobile_runtime_gate.py"}:
                continue
            if path.parts[:3] == ("src", "ulp_project", "static") and path.name.startswith("mobile"):
                continue
            if path.parts[:3] == ("src", "ulp_project", "templates") and path.name.startswith("mobile"):
                continue
            assert path.suffix.lower() not in forbidden
            assert "flutter" not in path.name.lower()
            assert "reactnative" not in path.name.lower().replace("_", "")


def test_no_mobile_architecture_doc_declares_browser_only():
    text = Path("docs/NO_MOBILE_APP_ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "HP hanya" in text
    assert "/field-capture" in text
    assert "hanya alias" in text
