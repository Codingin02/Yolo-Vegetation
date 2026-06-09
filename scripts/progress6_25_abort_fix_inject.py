from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tpl = ROOT / "src" / "ulp_project" / "templates" / "field_camera.html"

css_tag = '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'progress6_25_abort_fix.css\') }}?v=progress6_25_abort_fix">'

text = tpl.read_text(encoding="utf-8", errors="replace")
original = text

if css_tag not in text:
    idx = text.lower().rfind("</head>")
    if idx >= 0:
        text = text[:idx] + "  " + css_tag + "\n" + text[idx:]
    else:
        text = css_tag + "\n" + text

if text != original:
    tpl.write_text(text, encoding="utf-8")
    print("PATCHED:", tpl.relative_to(ROOT))
else:
    print("UNCHANGED:", tpl.relative_to(ROOT))

print("PROGRESS_6_25_ABORT_FIX_INJECT_PASS")
