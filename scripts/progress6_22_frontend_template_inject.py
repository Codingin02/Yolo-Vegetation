from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

camera_tpl = ROOT / "src" / "ulp_project" / "templates" / "field_camera.html"
capture_tpl = ROOT / "src" / "ulp_project" / "templates" / "field_capture.html"

css_tag = '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'progress6_22_vision_camera.css\') }}?v=progress6_22_frontend_vision_overlay">'
camera_js_tag = '<script defer src="{{ url_for(\'static\', filename=\'progress6_22_vision_camera.js\') }}?v=progress6_22_frontend_vision_overlay"></script>'
capture_js_tag = '<script defer src="{{ url_for(\'static\', filename=\'progress6_22_capture_start_guard.js\') }}?v=progress6_22_capture_start_guard"></script>'

def inject_head(text, tag):
    if tag in text:
        return text
    low = text.lower()
    idx = low.rfind("</head>")
    if idx >= 0:
        return text[:idx] + "  " + tag + "\n" + text[idx:]
    return tag + "\n" + text

def inject_body(text, tag):
    if tag in text:
        return text
    low = text.lower()
    idx = low.rfind("</body>")
    if idx >= 0:
        return text[:idx] + "  " + tag + "\n" + text[idx:]
    return text + "\n" + tag + "\n"

def patch(path, tags_head=(), tags_body=()):
    text = path.read_text(encoding="utf-8", errors="replace")
    original = text
    for tag in tags_head:
        text = inject_head(text, tag)
    for tag in tags_body:
        text = inject_body(text, tag)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"PATCHED: {path.relative_to(ROOT)}")
    else:
        print(f"UNCHANGED: {path.relative_to(ROOT)}")

patch(camera_tpl, tags_head=[css_tag], tags_body=[camera_js_tag])
patch(capture_tpl, tags_head=[css_tag], tags_body=[capture_js_tag])
print("PROGRESS_6_22_FRONTEND_TEMPLATE_INJECT_PASS")
