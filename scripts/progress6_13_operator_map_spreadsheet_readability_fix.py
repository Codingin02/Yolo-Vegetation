from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "progress6_13_operator_map_spreadsheet_readability_fix"

TEMPLATES = ROOT / "src" / "ulp_project" / "templates"
STATIC = ROOT / "src" / "ulp_project" / "static"
REPORTS = ROOT / "reports"
BACKUP_DIR = ROOT / "manual_backups" / f"progress6_13_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

CSS_NAME = "progress6_13_operator_result_fix.css"
JS_NAME = "progress6_13_operator_result_fix.js"

CSS_TEXT = r"""
/* progress6_13_operator_map_spreadsheet_readability_fix
   Scope: operator readability only.
   No label touch, no raw touch, no model touch.
*/

:root {
  --p613-bg: #eaf6f2;
  --p613-card: rgba(255,255,255,0.96);
  --p613-green: #11745f;
  --p613-green-dark: #083f31;
  --p613-border: rgba(8, 63, 49, 0.18);
  --p613-shadow: 0 18px 48px rgba(0,0,0,0.10);
  --p613-text: #0d2024;
}

html.p613-ready,
html.p613-ready body {
  overflow-x: hidden;
}

.p613-operator-summary {
  margin: 16px 0 18px 0;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255,255,255,0.78);
  border: 1px solid var(--p613-border);
  box-shadow: var(--p613-shadow);
}

.p613-summary-title {
  font-weight: 900;
  font-size: 16px;
  margin: 0 0 10px 0;
  color: var(--p613-green-dark);
}

.p613-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
}

.p613-summary-card {
  background: var(--p613-card);
  border: 1px solid var(--p613-border);
  border-radius: 14px;
  padding: 10px 12px;
  min-width: 0;
}

.p613-summary-card b {
  display: block;
  font-size: 11px;
  line-height: 1.25;
  margin-bottom: 5px;
  color: var(--p613-green-dark);
}

.p613-summary-card span {
  display: block;
  font-size: 13px;
  line-height: 1.35;
  color: var(--p613-text);
  overflow-wrap: anywhere;
  word-break: normal;
}

.p613-table-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin: 14px 0 8px 0;
  color: var(--p613-green-dark);
  font-size: 12px;
}

.p613-table-toolbar button {
  appearance: none;
  border: 0;
  border-radius: 999px;
  padding: 9px 12px;
  font-weight: 900;
  background: var(--p613-green);
  color: #fff;
  cursor: pointer;
}

.p613-table-toolbar span {
  opacity: 0.88;
  font-weight: 700;
}

.p613-table-wrap {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: auto !important;
  overflow-y: auto !important;
  max-height: min(68vh, 680px);
  border-radius: 18px;
  background: rgba(255,255,255,0.96);
  border: 1px solid var(--p613-border);
  box-shadow: var(--p613-shadow);
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  touch-action: pan-x pan-y;
}

.p613-table {
  width: max-content !important;
  min-width: 2100px !important;
  max-width: none !important;
  table-layout: auto !important;
  border-collapse: separate !important;
  border-spacing: 0 !important;
  font-size: 12px !important;
  line-height: 1.35 !important;
}

.p613-table th,
.p613-table td {
  writing-mode: horizontal-tb !important;
  text-orientation: mixed !important;
  white-space: nowrap !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  vertical-align: top !important;
  min-width: 92px !important;
  max-width: 260px !important;
  padding: 9px 10px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  border-right: 1px solid rgba(255,255,255,0.35) !important;
}

.p613-table th {
  position: sticky !important;
  top: 0 !important;
  z-index: 5 !important;
  background: var(--p613-green) !important;
  color: #fff !important;
  font-weight: 900 !important;
  letter-spacing: 0.01em !important;
}

.p613-table td {
  background: #fff !important;
  color: var(--p613-text) !important;
  border-bottom: 1px solid rgba(8,63,49,0.12) !important;
}

.p613-table th:first-child,
.p613-table td:first-child {
  position: sticky !important;
  left: 0 !important;
  z-index: 6 !important;
  min-width: 110px !important;
  max-width: 150px !important;
  box-shadow: 8px 0 14px rgba(0,0,0,0.08);
}

.p613-table td:first-child {
  background: #f6fffb !important;
  font-weight: 800 !important;
}

.p613-detail-mode .p613-table th,
.p613-detail-mode .p613-table td {
  max-width: none !important;
  min-width: 150px !important;
  overflow: visible !important;
  text-overflow: clip !important;
}

.p613-map-toolbar {
  margin: 16px 0 18px 0;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.22);
  box-shadow: var(--p613-shadow);
}

.p613-map-title {
  font-size: 15px;
  font-weight: 900;
  margin-bottom: 10px;
  color: #eafff8;
}

.p613-map-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 8px 0 12px 0;
}

.p613-map-actions a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 8px 12px;
  border-radius: 999px;
  background: #ffffff;
  color: #073d31 !important;
  font-weight: 900;
  text-decoration: none;
}

.p613-map-frame {
  display: block;
  width: 100%;
  min-height: 420px;
  border: 0;
  border-radius: 16px;
  background: #dcefe9;
}

@media (max-width: 700px) {
  body {
    overflow-x: hidden !important;
  }

  .p613-summary-grid {
    grid-template-columns: 1fr;
  }

  .p613-table-wrap {
    max-height: 58vh;
    border-radius: 14px;
  }

  .p613-table {
    min-width: 2400px !important;
    font-size: 11px !important;
  }

  .p613-table th,
  .p613-table td {
    min-width: 104px !important;
    max-width: 210px !important;
    padding: 8px 8px !important;
  }

  .p613-table-toolbar {
    position: sticky;
    top: 0;
    z-index: 20;
    background: rgba(234,246,242,0.96);
    padding: 8px 0;
  }

  .p613-map-frame {
    min-height: 320px;
  }
}
"""

JS_TEXT = r"""
(function () {
  "use strict";

  const VERSION = "progress6_13_operator_map_spreadsheet_readability_fix";

  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
      return;
    }
    document.addEventListener("DOMContentLoaded", fn);
  }

  function normText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getFirstMatch(text, regexList) {
    for (const rx of regexList) {
      const m = text.match(rx);
      if (m && m[1]) {
        return normText(m[1]);
      }
    }
    return "";
  }

  function enhanceTables() {
    const tables = Array.from(document.querySelectorAll("table"));
    for (const table of tables) {
      if (table.dataset.p613Enhanced === "1") {
        continue;
      }

      table.dataset.p613Enhanced = "1";
      table.classList.add("p613-table");

      let wrap = table.closest(".p613-table-wrap");
      if (!wrap) {
        wrap = document.createElement("div");
        wrap.className = "p613-table-wrap p613-compact-mode";
        table.parentNode.insertBefore(wrap, table);
        wrap.appendChild(table);
      }

      const cells = Array.from(table.querySelectorAll("th,td"));
      for (const cell of cells) {
        const txt = normText(cell.textContent);
        if (txt && !cell.title) {
          cell.title = txt;
        }
        cell.setAttribute("data-p613-full", txt);
      }

      if (!wrap.previousElementSibling || !wrap.previousElementSibling.classList.contains("p613-table-toolbar")) {
        const toolbar = document.createElement("div");
        toolbar.className = "p613-table-toolbar";
        toolbar.innerHTML =
          '<button type="button" data-p613-mode="compact">Mode Ringkas</button>' +
          '<button type="button" data-p613-mode="detail">Mode Detail</button>' +
          '<span>Geser kanan/kiri untuk melihat seluruh kolom. Tekan lama sel untuk melihat isi penuh.</span>';

        wrap.parentNode.insertBefore(toolbar, wrap);

        toolbar.addEventListener("click", function (event) {
          const button = event.target.closest("button[data-p613-mode]");
          if (!button) {
            return;
          }

          const mode = button.getAttribute("data-p613-mode");
          wrap.classList.toggle("p613-detail-mode", mode === "detail");
          wrap.classList.toggle("p613-compact-mode", mode !== "detail");
        });
      }
    }
  }

  function buildOperatorSummary() {
    if (document.querySelector(".p613-operator-summary")) {
      return;
    }

    const text = normText(document.body.textContent || "");
    const isTargetPage =
      /Spreadsheet Evidence/i.test(text) ||
      /Field Session Map/i.test(text) ||
      /Session ID:/i.test(text);

    if (!isTargetPage) {
      return;
    }

    const fields = [
      ["Session ID", [/Session ID:\s*([A-Z0-9_]+)/i, /session_id["']?\s*[:=]\s*["']?([A-Z0-9_]+)/i]],
      ["Point ID", [/Point ID:\s*([A-Za-z0-9_\-]+)/i, /point_id["']?\s*[:=]\s*["']?([A-Za-z0-9_\-]+)/i]],
      ["GPS Coordinate", [/GPS Coordinate:\s*(-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?)/i]],
      ["GPS Accuracy", [/GPS Accuracy:\s*([0-9.]+\s*m|[A-Z0-9_.\- ]+)/i]],
      ["Frame Status", [/Frame Status:\s*([A-Z0-9_]+)/i, /frame_status["']?\s*[:=]\s*["']?([A-Z0-9_]+)/i]],
      ["Tree Model", [/Tree Model Status:\s*([A-Z0-9_]+)/i, /tree_model_status["']?\s*[:=]\s*["']?([A-Z0-9_]+)/i]],
      ["Pole Model", [/Pole Model Status:\s*([A-Z0-9_]+)/i, /pole_model_status["']?\s*[:=]\s*["']?([A-Z0-9_]+)/i]],
      ["Conductor Model", [/Conductor Model:\s*([A-Z0-9_]+)/i, /conductor_model_status["']?\s*[:=]\s*["']?([A-Z0-9_]+)/i]],
      ["Clearance", [/Clearance Status:\s*([A-Z0-9_]+)/i, /clearance_status["']?\s*[:=]\s*["']?([A-Z0-9_]+)/i]],
      ["ETA", [/ETA Status:\s*([A-Z0-9_]+)/i, /eta_3m_status["']?\s*[:=]\s*["']?([A-Z0-9_]+)/i]]
    ];

    let html = "";
    for (const [label, regexList] of fields) {
      const value = getFirstMatch(text, regexList);
      if (!value) {
        continue;
      }

      html +=
        '<div class="p613-summary-card">' +
        "<b>" + escapeHtml(label) + "</b>" +
        "<span>" + escapeHtml(value) + "</span>" +
        "</div>";
    }

    if (!html) {
      return;
    }

    const box = document.createElement("section");
    box.className = "p613-operator-summary";
    box.innerHTML =
      '<div class="p613-summary-title">Ringkasan Operator</div>' +
      '<div class="p613-summary-grid">' + html + "</div>";

    const title = Array.from(document.querySelectorAll("h1,h2,h3"))
      .find((node) => /Spreadsheet Evidence|Field Session Map/i.test(node.textContent || ""));

    if (title && title.parentNode) {
      title.parentNode.insertBefore(box, title.nextSibling);
    } else {
      document.body.insertBefore(box, document.body.firstChild);
    }
  }

  function extractCoordinate() {
    const text = document.body.textContent || "";

    const patterns = [
      /Current marker[^:]*:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/i,
      /Base marker[^:]*:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/i,
      /GPS Coordinate:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/i
    ];

    for (const rx of patterns) {
      const match = text.match(rx);
      if (!match) {
        continue;
      }

      const lat = Number(match[1]);
      const lon = Number(match[2]);

      if (
        Number.isFinite(lat) &&
        Number.isFinite(lon) &&
        Math.abs(lat) <= 90 &&
        Math.abs(lon) <= 180
      ) {
        return { lat, lon };
      }
    }

    return null;
  }

  function enhanceMap() {
    const text = document.body.textContent || "";
    if (!/Field Session Map/i.test(text)) {
      return;
    }

    if (document.querySelector(".p613-map-toolbar")) {
      return;
    }

    const coord = extractCoordinate();
    const box = document.createElement("div");
    box.className = "p613-map-toolbar";

    if (coord) {
      const lat = coord.lat;
      const lon = coord.lon;
      const delta = 0.0025;

      const googleUrl = "https://www.google.com/maps?q=" + encodeURIComponent(lat + "," + lon);
      const osmUrl = "https://www.openstreetmap.org/?mlat=" + encodeURIComponent(lat) +
        "&mlon=" + encodeURIComponent(lon) + "#map=18/" +
        encodeURIComponent(lat) + "/" + encodeURIComponent(lon);

      const embedUrl =
        "https://www.openstreetmap.org/export/embed.html?bbox=" +
        encodeURIComponent(lon - delta) + "%2C" +
        encodeURIComponent(lat - delta) + "%2C" +
        encodeURIComponent(lon + delta) + "%2C" +
        encodeURIComponent(lat + delta) +
        "&layer=mapnik&marker=" +
        encodeURIComponent(lat) + "%2C" + encodeURIComponent(lon);

      box.innerHTML =
        '<div class="p613-map-title">Map Evidence Aktif</div>' +
        '<div class="p613-map-actions">' +
        '<a target="_blank" rel="noopener" href="' + googleUrl + '">Buka Google Maps</a>' +
        '<a target="_blank" rel="noopener" href="' + osmUrl + '">Buka OpenStreetMap</a>' +
        "</div>" +
        '<iframe class="p613-map-frame" loading="lazy" src="' + embedUrl + '" title="Field session map"></iframe>';
    } else {
      box.innerHTML =
        '<div class="p613-map-title">GPS belum valid untuk marker</div>' +
        "<p>Map tidak boleh membuat marker palsu. Kembali ke Camera, tunggu status GPS_READY_xM, lalu tekan Shutter ulang pada session yang sama.</p>";
    }

    const title = Array.from(document.querySelectorAll("h1,h2,h3"))
      .find((node) => /Field Session Map/i.test(node.textContent || ""));

    if (title && title.parentNode) {
      title.parentNode.insertBefore(box, title.nextSibling);
    } else {
      document.body.insertBefore(box, document.body.firstChild);
    }
  }

  function addUiVersionMarker() {
    if (document.querySelector("[data-p613-version]")) {
      return;
    }

    const marker = document.createElement("div");
    marker.setAttribute("data-p613-version", VERSION);
    marker.style.cssText =
      "position:fixed;right:8px;bottom:8px;z-index:9999;padding:4px 7px;border-radius:999px;background:rgba(0,0,0,.45);color:#fff;font:10px system-ui;pointer-events:none;";
    marker.textContent = "UI " + VERSION;
    document.body.appendChild(marker);
  }

  ready(function () {
    document.documentElement.classList.add("p613-ready");
    buildOperatorSummary();
    enhanceTables();
    enhanceMap();
    addUiVersionMarker();
  });
})();
"""

VALIDATOR_TEXT = r"""
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
"""

def safe_read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def backup_once(path: Path) -> None:
    if not path.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    rel = path.relative_to(ROOT)
    dst = BACKUP_DIR / str(rel).replace("\\", "_").replace("/", "_")
    if not dst.exists():
        shutil.copy2(path, dst)

def write_file(path: Path, text: str, backup: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and safe_read(path) == text:
        print(f"UNCHANGED {path.relative_to(ROOT)}")
        return
    if backup:
        backup_once(path)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"WROTE {path.relative_to(ROOT)}")

def inject_before(html: str, needle_regex: str, snippet: str) -> str:
    if snippet.strip() in html:
        return html

    match = re.search(needle_regex, html, flags=re.IGNORECASE)
    if not match:
        return html + "\n" + snippet + "\n"

    start = match.start()
    return html[:start] + snippet + "\n" + html[start:]

def inject_template(path: Path) -> bool:
    text = safe_read(path)

    css_tag = (
        '<link rel="stylesheet" '
        'href="{{ url_for(\'static\', filename=\'progress6_13_operator_result_fix.css\') }}?v=progress6_13_operator_map_spreadsheet_readability_fix" '
        'data-progress6-13="css">'
    )

    js_tag = (
        '<script defer '
        'src="{{ url_for(\'static\', filename=\'progress6_13_operator_result_fix.js\') }}?v=progress6_13_operator_map_spreadsheet_readability_fix" '
        'data-progress6-13="js"></script>'
    )

    changed = False

    if "progress6_13_operator_result_fix.css" not in text:
        text = inject_before(text, r"</head\s*>", css_tag)
        changed = True

    if "progress6_13_operator_result_fix.js" not in text:
        if re.search(r"</body\s*>", text, flags=re.IGNORECASE):
            text = inject_before(text, r"</body\s*>", js_tag)
        else:
            text = text + "\n" + js_tag + "\n"
        changed = True

    if changed:
        write_file(path, text, backup=True)
    else:
        print(f"UNCHANGED {path.relative_to(ROOT)}")

    return changed

def choose_templates() -> list[Path]:
    explicit_names = [
        "field_report.html",
        "field_result.html",
        "field_trial_checklist.html",
        "field_map.html",
        "field_spreadsheet.html",
        "field_acceptance.html",
    ]

    chosen: set[Path] = set()

    for name in explicit_names:
        p = TEMPLATES / name
        if p.exists():
            chosen.add(p)

    for p in TEMPLATES.glob("*.html"):
        text = safe_read(p).lower()
        if (
            "spreadsheet evidence" in text
            or "field session map" in text
            or "field-spreadsheet" in text
            or "field-map/session" in text
            or "<table" in text
        ):
            chosen.add(p)

    return sorted(chosen)

def main() -> int:
    print(f"VERSION={VERSION}")
    print(f"ROOT={ROOT}")

    STATIC.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    write_file(STATIC / CSS_NAME, CSS_TEXT, backup=True)
    write_file(STATIC / JS_NAME, JS_TEXT, backup=True)

    targets = choose_templates()
    if not targets:
        print("ERROR: no template targets found")
        return 2

    print("TEMPLATE TARGETS:")
    for p in targets:
        print("  " + str(p.relative_to(ROOT)))

    for template in targets:
        inject_template(template)

    write_file(ROOT / "scripts" / "progress6_13_operator_map_spreadsheet_readability_validator.py", VALIDATOR_TEXT, backup=False)

    summary = {
        "status": "PROGRESS_6_13_OPERATOR_MAP_SPREADSHEET_READABILITY_PATCHED",
        "version": VERSION,
        "patched_static": [
            str((STATIC / CSS_NAME).relative_to(ROOT)),
            str((STATIC / JS_NAME).relative_to(ROOT)),
        ],
        "patched_templates": [str(p.relative_to(ROOT)) for p in targets],
        "backup_dir": str(BACKUP_DIR.relative_to(ROOT)) if BACKUP_DIR.exists() else None,
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_dataset_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
        "operator_effect": [
            "Spreadsheet detail table gets horizontal scroll and no vertical-per-letter text.",
            "Operator summary cards are added above detail table.",
            "Map page gets Google Maps/OpenStreetMap links and embedded OSM only when valid coordinates exist.",
            "If GPS is missing, map displays explicit no-fake-marker instruction.",
        ],
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
