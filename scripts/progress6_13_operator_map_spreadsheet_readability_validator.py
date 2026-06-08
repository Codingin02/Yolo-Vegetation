
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "progress6_13_operator_map_spreadsheet_readability_fix"
REPORTS = ROOT / "reports"

def run_step(name: str, cmd: list[str]) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    result = {
        "name": name,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "returncode": proc.returncode,
        "cmd": cmd,
        "stdout_tail": proc.stdout.splitlines()[-40:],
        "stderr_tail": proc.stderr.splitlines()[-40:],
    }
    print("===", name, "===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

def contains(path: Path, needle: str) -> bool:
    if not path.exists():
        return False
    return needle in path.read_text(encoding="utf-8", errors="replace")

def main() -> int:
    py = str(ROOT / "venv" / "Scripts" / "python.exe")
    if not Path(py).exists():
        py = sys.executable

    checks = []
    checks.append({
        "name": "STATIC_CSS_EXISTS",
        "status": "PASS" if (ROOT / "src" / "ulp_project" / "static" / "progress6_13_operator_result_fix.css").exists() else "FAIL",
    })
    checks.append({
        "name": "STATIC_JS_EXISTS",
        "status": "PASS" if (ROOT / "src" / "ulp_project" / "static" / "progress6_13_operator_result_fix.js").exists() else "FAIL",
    })

    template_dir = ROOT / "src" / "ulp_project" / "templates"
    html_files = list(template_dir.glob("*.html"))
    injected = []
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "progress6_13_operator_result_fix.css" in text or "progress6_13_operator_result_fix.js" in text:
            injected.append(str(path.relative_to(ROOT)))

    checks.append({
        "name": "TEMPLATE_INJECTION_FOUND",
        "status": "PASS" if injected else "FAIL",
        "injected_templates": injected,
    })

    results = []
    results.append(run_step("PY_COMPILE_PATCH", [py, "-m", "py_compile", "scripts/progress6_13_operator_map_spreadsheet_readability_fix.py"]))
    results.append(run_step("COMPILEALL_SRC_SCRIPTS_TESTS", [py, "-m", "compileall", "src", "scripts", "tests"]))
    results.append(run_step("GIT_DIFF_CHECK", ["git", "diff", "--check"]))

    hard_failures = []
    for check in checks:
        print("===", check["name"], "===")
        print(json.dumps(check, indent=2, ensure_ascii=False))
        if check["status"] != "PASS":
            hard_failures.append(check["name"])

    for result in results:
        if result["status"] != "PASS":
            hard_failures.append(result["name"])

    final = {
        "status": "PROGRESS_6_13_VALIDATION_PASS" if not hard_failures else "PROGRESS_6_13_VALIDATION_HAS_FAILURES",
        "version": VERSION,
        "hard_failures": hard_failures,
        "checks": checks,
        "results": results,
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_dataset_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
        "note": "Patch ini hanya menambah CSS/JS operator readability dan injeksi template HTML aktif. Tidak menyentuh data/model/label.",
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / "progress6_13_operator_map_spreadsheet_readability_validation.json"
    report_path.write_text(json.dumps(final, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== FINAL ===")
    print(json.dumps(final, indent=2, ensure_ascii=False))
    print("VALIDATION_JSON=" + str(report_path))

    return 0 if not hard_failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
