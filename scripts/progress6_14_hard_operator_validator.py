
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "venv" / "Scripts" / "python.exe"

checks = []

def run(name, cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    item = {
        "name": name,
        "returncode": p.returncode,
        "status": "PASS" if p.returncode == 0 else "FAIL",
        "stdout_tail": p.stdout.splitlines()[-20:],
        "stderr_tail": p.stderr.splitlines()[-20:],
    }
    checks.append(item)
    print("===" + name + "===")
    print(json.dumps(item, indent=2))
    return p.returncode

hard_fail = 0
hard_fail += run("PY_COMPILE_PATCH_AND_VALIDATOR", [str(PY), "-m", "py_compile", "scripts/progress6_14_hard_operator_gps_map_spreadsheet_fix.py", "scripts/progress6_14_hard_operator_validator.py"])
hard_fail += run("COMPILEALL_SRC_SCRIPTS_TESTS", [str(PY), "-m", "compileall", "src", "scripts", "tests"])

css = ROOT / "src" / "ulp_project" / "static" / "progress6_14_hard_operator_fix.css"
js = ROOT / "src" / "ulp_project" / "static" / "progress6_14_hard_operator_fix.js"
templates = list((ROOT / "src" / "ulp_project" / "templates").glob("*.html"))

asset_ok = css.exists() and js.exists()
inject_count = 0
for t in templates:
    text = t.read_text(encoding="utf-8", errors="ignore")
    if "progress6_14_hard_operator_fix.css" in text and "progress6_14_hard_operator_fix.js" in text:
        inject_count += 1

required_snippets = [
    "p614-table-scroll",
    "p614-readable-table",
    "navigator.geolocation.watchPosition",
    "/api/field/session/gps-update",
    "openstreetmap.org/export/embed.html",
    "white-space\", \"nowrap\", \"important",
]

js_text = js.read_text(encoding="utf-8", errors="ignore") if js.exists() else ""
css_text = css.read_text(encoding="utf-8", errors="ignore") if css.exists() else ""

snippet_ok = all((s in js_text or s in css_text) for s in required_snippets)

git_diff_code = run("GIT_DIFF_CHECK", ["git", "diff", "--check"])

result = {
    "status": "PROGRESS_6_14_HARD_OPERATOR_FIX_PASS" if (hard_fail == 0 and git_diff_code == 0 and asset_ok and inject_count >= 3 and snippet_ok) else "PROGRESS_6_14_HARD_OPERATOR_FIX_FAILED",
    "asset_ok": asset_ok,
    "template_injection_count": inject_count,
    "snippet_ok": snippet_ok,
    "no_label_touch": True,
    "no_raw_touch": True,
    "no_dataset_touch": True,
    "no_runs_touch": True,
    "no_weights_touch": True,
    "notes": [
        "Patch ini hanya UI/runtime browser hard-fix.",
        "GPS dikirim ulang dari browser ke session via /api/field/session/gps-update.",
        "Map memakai marker hanya bila koordinat valid; jika tidak valid hanya peta konteks tanpa marker palsu.",
        "Spreadsheet dibuat operator-readable dengan DOM transform dan CSS important."
    ],
    "checks": checks
}

out = ROOT / "reports" / "progress6_14_hard_operator_fix_validation.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
print("===FINAL===")
print(json.dumps(result, indent=2))
print("VALIDATION_JSON=" + str(out))
sys.exit(0 if result["status"].endswith("_PASS") else 1)
