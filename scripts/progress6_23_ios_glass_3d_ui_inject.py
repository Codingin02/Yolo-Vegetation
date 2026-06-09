from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

templates = [
    ROOT / "src" / "ulp_project" / "templates" / "field_camera.html",
    ROOT / "src" / "ulp_project" / "templates" / "field_capture.html",
]

css_tag = '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'progress6_23_ios_glass_3d_ui.css\') }}?v=progress6_23_ios_glass_3d_ui">'
js_tag = '<script defer src="{{ url_for(\'static\', filename=\'progress6_23_ios_glass_3d_ui.js\') }}?v=progress6_23_ios_glass_3d_ui"></script>'

def inject_head(text, tag):
    if tag in text:
        return text
    idx = text.lower().rfind("</head>")
    if idx >= 0:
        return text[:idx] + "  " + tag + "\n" + text[idx:]
    return tag + "\n" + text

def inject_body(text, tag):
    if tag in text:
        return text
    idx = text.lower().rfind("</body>")
    if idx >= 0:
        return text[:idx] + "  " + tag + "\n" + text[idx:]
    return text + "\n" + tag + "\n"

for path in templates:
    text = path.read_text(encoding="utf-8", errors="replace")
    original = text
    text = inject_head(text, css_tag)
    text = inject_body(text, js_tag)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print("PATCHED:", path.relative_to(ROOT))
    else:
        print("UNCHANGED:", path.relative_to(ROOT))

print("PROGRESS_6_23_IOS_GLASS_3D_UI_INJECT_PASS")
