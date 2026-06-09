from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
camera_tpl = ROOT / "src" / "ulp_project" / "templates" / "field_camera.html"

css_tag = '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'progress6_24_realtime_vision_switch.css\') }}?v=progress6_24_realtime_vision_switch">'
js_tag = '<script defer src="{{ url_for(\'static\', filename=\'progress6_24_realtime_vision_switch.js\') }}?v=progress6_24_realtime_vision_switch"></script>'

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

text = camera_tpl.read_text(encoding="utf-8", errors="replace")
original = text
text = inject_head(text, css_tag)
text = inject_body(text, js_tag)

if text != original:
    camera_tpl.write_text(text, encoding="utf-8")
    print("PATCHED:", camera_tpl.relative_to(ROOT))
else:
    print("UNCHANGED:", camera_tpl.relative_to(ROOT))

print("PROGRESS_6_24_REALTIME_VISION_SWITCH_INJECT_PASS")
