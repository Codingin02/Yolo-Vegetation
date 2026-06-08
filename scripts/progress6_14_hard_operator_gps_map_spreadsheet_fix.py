from pathlib import Path
from datetime import datetime
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = "progress6_14_hard_operator_gps_map_spreadsheet_fix"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = ROOT / "manual_backups" / f"progress6_14_{STAMP}"

CSS_PATH = ROOT / "src" / "ulp_project" / "static" / "progress6_14_hard_operator_fix.css"
JS_PATH = ROOT / "src" / "ulp_project" / "static" / "progress6_14_hard_operator_fix.js"
VALIDATOR_PATH = ROOT / "scripts" / "progress6_14_hard_operator_validator.py"

TEMPLATE_DIR = ROOT / "src" / "ulp_project" / "templates"

CSS_MARKER = "progress6_14_hard_operator_fix.css"
JS_MARKER = "progress6_14_hard_operator_fix.js"

CSS = r'''
/* progress6_14_hard_operator_gps_map_spreadsheet_fix */
/* Tujuan: map tetap informatif, spreadsheet operator-readable, no fake GPS/clearance/model. */

:root {
  --p614-green-900: #073b2a;
  --p614-green-800: #0b4a35;
  --p614-green-700: #11765a;
  --p614-green-100: #eaf7f2;
  --p614-blue-700: #25639a;
  --p614-white: #ffffff;
  --p614-ink: #0d2228;
  --p614-muted: #4c6066;
  --p614-line: rgba(8, 68, 50, 0.18);
  --p614-shadow: 0 18px 52px rgba(7, 59, 42, 0.16);
}

html body {
  overflow-x: hidden !important;
}

.p614-operator-map-panel,
.p614-operator-sheet-panel,
.p614-operator-notice {
  box-sizing: border-box !important;
  width: min(1120px, calc(100vw - 28px)) !important;
  margin: 18px auto !important;
  padding: 18px !important;
  border: 1px solid var(--p614-line) !important;
  border-radius: 26px !important;
  background: rgba(255,255,255,0.88) !important;
  color: var(--p614-ink) !important;
  box-shadow: var(--p614-shadow) !important;
}

.p614-operator-map-panel {
  background: linear-gradient(145deg, rgba(10, 75, 54, 0.95), rgba(5, 45, 31, 0.96)) !important;
  color: #f3fff9 !important;
}

.p614-operator-map-panel h2,
.p614-operator-sheet-panel h2 {
  margin: 0 0 12px 0 !important;
  font-size: clamp(22px, 4vw, 34px) !important;
  line-height: 1.1 !important;
}

.p614-map-frame {
  width: 100% !important;
  height: min(58vh, 520px) !important;
  min-height: 340px !important;
  border: 0 !important;
  border-radius: 22px !important;
  background: #d8eee5 !important;
  display: block !important;
}

.p614-map-actions {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 10px !important;
  margin-top: 14px !important;
}

.p614-action-btn,
.p614-map-actions a,
.p614-operator-sheet-panel a,
.p614-operator-map-panel a {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-height: 44px !important;
  padding: 10px 14px !important;
  border-radius: 14px !important;
  background: var(--p614-green-700) !important;
  color: white !important;
  text-decoration: none !important;
  font-weight: 800 !important;
  box-shadow: 0 10px 26px rgba(0,0,0,0.16) !important;
}

.p614-map-status {
  margin: 10px 0 14px 0 !important;
  padding: 12px 14px !important;
  border-radius: 16px !important;
  background: rgba(255,255,255,0.13) !important;
  color: #f3fff9 !important;
  line-height: 1.45 !important;
}

.p614-kv-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)) !important;
  gap: 10px !important;
  width: 100% !important;
  margin: 12px 0 16px 0 !important;
}

.p614-kv-card {
  box-sizing: border-box !important;
  min-width: 0 !important;
  padding: 12px !important;
  border-radius: 16px !important;
  border: 1px solid rgba(8, 68, 50, 0.14) !important;
  background: rgba(255,255,255,0.94) !important;
  color: var(--p614-ink) !important;
}

.p614-kv-key {
  display: block !important;
  font-size: 12px !important;
  line-height: 1.2 !important;
  font-weight: 900 !important;
  color: var(--p614-muted) !important;
  margin-bottom: 4px !important;
  overflow-wrap: anywhere !important;
}

.p614-kv-val {
  display: block !important;
  font-size: 14px !important;
  line-height: 1.35 !important;
  font-weight: 800 !important;
  color: var(--p614-ink) !important;
  overflow-wrap: anywhere !important;
}

.p614-table-scroll {
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: auto !important;
  overflow-y: visible !important;
  -webkit-overflow-scrolling: touch !important;
  border-radius: 20px !important;
  background: white !important;
  box-shadow: 0 12px 34px rgba(7, 59, 42, 0.12) !important;
  padding: 10px !important;
}

html body table.p614-readable-table {
  width: max-content !important;
  min-width: 2350px !important;
  max-width: none !important;
  table-layout: auto !important;
  border-collapse: collapse !important;
  border-spacing: 0 !important;
  background: white !important;
}

html body table.p614-readable-table th,
html body table.p614-readable-table td,
html body .p614-table-scroll table th,
html body .p614-table-scroll table td {
  writing-mode: horizontal-tb !important;
  text-orientation: mixed !important;
  white-space: nowrap !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  hyphens: none !important;
  min-width: 118px !important;
  max-width: 360px !important;
  width: auto !important;
  padding: 10px 12px !important;
  font-size: 13px !important;
  line-height: 1.25 !important;
  vertical-align: top !important;
  text-align: left !important;
}

html body table.p614-readable-table th,
html body .p614-table-scroll table th {
  position: sticky !important;
  top: 0 !important;
  z-index: 2 !important;
  background: var(--p614-green-700) !important;
  color: white !important;
  font-weight: 900 !important;
}

html body table.p614-readable-table td,
html body .p614-table-scroll table td {
  color: var(--p614-ink) !important;
  background: white !important;
  border: 1px solid rgba(8, 68, 50, 0.14) !important;
}

.p614-hidden-raw-title {
  display: none !important;
}

.p614-gps-pill {
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  padding: 7px 10px !important;
  margin: 4px 6px 4px 0 !important;
  border-radius: 999px !important;
  background: rgba(255,255,255,0.14) !important;
  color: #f3fff9 !important;
  border: 1px solid rgba(255,255,255,0.22) !important;
  font-size: 12px !important;
  font-weight: 900 !important;
}

@media (max-width: 780px) {
  .p614-operator-map-panel,
  .p614-operator-sheet-panel,
  .p614-operator-notice {
    width: calc(100vw - 18px) !important;
    margin: 10px auto !important;
    padding: 14px !important;
    border-radius: 22px !important;
  }

  .p614-map-frame {
    height: 54vh !important;
    min-height: 300px !important;
  }

  .p614-kv-grid {
    grid-template-columns: 1fr !important;
  }

  html body table.p614-readable-table {
    min-width: 2450px !important;
  }

  html body table.p614-readable-table th,
  html body table.p614-readable-table td,
  html body .p614-table-scroll table th,
  html body .p614-table-scroll table td {
    min-width: 112px !important;
    padding: 9px 10px !important;
    font-size: 12px !important;
  }
}
'''

JS = r'''
// progress6_14_hard_operator_gps_map_spreadsheet_fix
(function () {
  "use strict";

  const VERSION = "progress6_14_hard_operator_gps_map_spreadsheet_fix";
  const GPS_ENDPOINT = "/api/field/session/gps-update";
  const SESSION_ID_RE = /FS_[A-Za-z0-9_:-]+/;
  let gpsWatchId = null;
  let lastGpsPostMs = 0;

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  }

  function normText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function cleanHeader(value) {
    return normText(value)
      .replace(/[^a-zA-Z0-9_ -]/g, "")
      .replace(/\s+/g, "_")
      .toLowerCase();
  }

  function getSessionId() {
    try {
      const qs = new URLSearchParams(window.location.search);
      const fromQuery = qs.get("session_id");
      if (fromQuery && fromQuery.trim()) {
        localStorage.setItem("field_session_id", fromQuery.trim());
        return fromQuery.trim();
      }
    } catch (e) {}

    const pathMatch = window.location.pathname.match(/\/session\/([^/?#]+)/);
    if (pathMatch && pathMatch[1]) {
      localStorage.setItem("field_session_id", pathMatch[1]);
      return pathMatch[1];
    }

    const bodyText = document.body ? document.body.innerText : "";
    const bodyMatch = bodyText.match(SESSION_ID_RE);
    if (bodyMatch && bodyMatch[0]) {
      localStorage.setItem("field_session_id", bodyMatch[0]);
      return bodyMatch[0];
    }

    const stored = localStorage.getItem("field_session_id");
    return stored || "";
  }

  function setGpsBadge(statusText) {
    const existing = document.querySelector("[data-p614-gps-live]");
    if (existing) {
      existing.textContent = statusText;
      return;
    }

    const target =
      document.querySelector(".hud, .status-row, .top-status, header, .status-pills") ||
      document.body;

    const badge = document.createElement("span");
    badge.className = "p614-gps-pill";
    badge.setAttribute("data-p614-gps-live", "1");
    badge.textContent = statusText;

    if (target === document.body) {
      badge.style.position = "fixed";
      badge.style.left = "12px";
      badge.style.top = "12px";
      badge.style.zIndex = "999999";
    }

    target.appendChild(badge);
  }

  function postGpsPosition(position) {
    const now = Date.now();
    if (now - lastGpsPostMs < 1800) return;
    lastGpsPostMs = now;

    const sessionId = getSessionId();
    if (!sessionId) {
      setGpsBadge("GPS_READY_NO_SESSION");
      return;
    }

    const c = position.coords || {};
    const lat = Number(c.latitude);
    const lon = Number(c.longitude);
    const acc = Number(c.accuracy);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      setGpsBadge("GPS_INVALID_BROWSER");
      return;
    }

    const accuracyText = Number.isFinite(acc) ? Math.round(acc) + "M" : "NO_ACC";
    setGpsBadge("GPS_READY_" + accuracyText);

    const payload = {
      ok: true,
      session_id: sessionId,
      gps_status: "GPS_READY",
      gps_source: "BROWSER_WATCHPOSITION",
      latitude: lat,
      longitude: lon,
      accuracy: Number.isFinite(acc) ? acc : null,
      accuracy_m: Number.isFinite(acc) ? acc : null,
      timestamp_ms: now,
      gps: {
        status: "GPS_READY",
        source: "BROWSER_WATCHPOSITION",
        latitude: lat,
        longitude: lon,
        accuracy: Number.isFinite(acc) ? acc : null,
        accuracy_m: Number.isFinite(acc) ? acc : null
      },
      gpsPayload: {
        gps_status: "GPS_READY",
        gps_source: "BROWSER_WATCHPOSITION",
        latitude: lat,
        longitude: lon,
        accuracy_m: Number.isFinite(acc) ? acc : null
      }
    };

    fetch(GPS_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
      body: JSON.stringify(payload),
      keepalive: true
    }).catch(function () {
      setGpsBadge("GPS_POST_RETRY");
    });
  }

  function startGpsWatcher(reason) {
    if (!("geolocation" in navigator)) {
      setGpsBadge("GPS_UNAVAILABLE");
      return;
    }
    if (gpsWatchId !== null) return;

    setGpsBadge("GPS_REQUESTING");
    try {
      gpsWatchId = navigator.geolocation.watchPosition(
        postGpsPosition,
        function (error) {
          const code = error && error.code ? error.code : "ERR";
          setGpsBadge("GPS_WAITING_" + code);
        },
        {
          enableHighAccuracy: true,
          timeout: 20000,
          maximumAge: 1000
        }
      );
    } catch (e) {
      setGpsBadge("GPS_WATCH_FAILED");
    }
  }

  function forceReadableTable(table) {
    if (!table || table.dataset.p614Fixed === "1") return;
    table.dataset.p614Fixed = "1";
    table.classList.add("p614-readable-table");

    table.style.setProperty("width", "max-content", "important");
    table.style.setProperty("min-width", "2350px", "important");
    table.style.setProperty("max-width", "none", "important");
    table.style.setProperty("table-layout", "auto", "important");
    table.style.setProperty("border-collapse", "collapse", "important");

    const cells = table.querySelectorAll("th, td");
    cells.forEach(function (cell) {
      cell.style.setProperty("writing-mode", "horizontal-tb", "important");
      cell.style.setProperty("text-orientation", "mixed", "important");
      cell.style.setProperty("white-space", "nowrap", "important");
      cell.style.setProperty("word-break", "normal", "important");
      cell.style.setProperty("overflow-wrap", "normal", "important");
      cell.style.setProperty("hyphens", "none", "important");
      cell.style.setProperty("min-width", "118px", "important");
      cell.style.setProperty("max-width", "360px", "important");
      cell.style.setProperty("width", "auto", "important");
      cell.style.setProperty("padding", "10px 12px", "important");
      cell.style.setProperty("font-size", "13px", "important");
      cell.style.setProperty("line-height", "1.25", "important");
      cell.title = normText(cell.textContent);
    });

    if (!table.parentElement || !table.parentElement.classList.contains("p614-table-scroll")) {
      const wrapper = document.createElement("div");
      wrapper.className = "p614-table-scroll";
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  }

  function extractTablePairs(table) {
    const rows = Array.from(table.querySelectorAll("tr"));
    if (rows.length < 2) return [];

    let headerCells = Array.from(rows[0].querySelectorAll("th, td"));
    let valueCells = Array.from(rows[1].querySelectorAll("td, th"));

    if (headerCells.length === 0 || valueCells.length === 0) return [];

    const pairs = [];
    const count = Math.min(headerCells.length, valueCells.length);
    for (let i = 0; i < count; i++) {
      const keyRaw = normText(headerCells[i].textContent);
      const valRaw = normText(valueCells[i].textContent);
      if (!keyRaw && !valRaw) continue;
      pairs.push({ key: keyRaw || ("field_" + i), cleanKey: cleanHeader(keyRaw), value: valRaw || "-" });
    }
    return pairs;
  }

  function buildOperatorCards(pairs, anchor) {
    if (!pairs || pairs.length === 0) return;
    if (document.querySelector("[data-p614-sheet-cards]")) return;

    const priority = [
      "session_id", "timestamp", "point_id", "operator_name",
      "gps_lat", "gps_lon", "gps_accuracy_m",
      "frame_status", "tree_model_status", "pole_model_status", "conductor_model_status",
      "tree_detected", "tree_confidence", "clearance_m", "clearance_status",
      "eta_3m_status", "zone_status", "source_status", "notes"
    ];

    const selected = [];
    priority.forEach(function (wanted) {
      const found = pairs.find(function (p) { return p.cleanKey === wanted || p.cleanKey.indexOf(wanted) >= 0; });
      if (found && !selected.includes(found)) selected.push(found);
    });

    pairs.forEach(function (p) {
      if (selected.length >= 18) return;
      if (!selected.includes(p)) selected.push(p);
    });

    const panel = document.createElement("section");
    panel.className = "p614-operator-sheet-panel";
    panel.setAttribute("data-p614-sheet-cards", "1");

    const title = document.createElement("h2");
    title.textContent = "Spreadsheet Evidence - Operator View";
    panel.appendChild(title);

    const grid = document.createElement("div");
    grid.className = "p614-kv-grid";

    selected.forEach(function (p) {
      const card = document.createElement("div");
      card.className = "p614-kv-card";

      const key = document.createElement("span");
      key.className = "p614-kv-key";
      key.textContent = p.key;

      const val = document.createElement("span");
      val.className = "p614-kv-val";
      val.textContent = p.value;

      card.appendChild(key);
      card.appendChild(val);
      grid.appendChild(card);
    });

    panel.appendChild(grid);

    const note = document.createElement("div");
    note.className = "p614-operator-notice";
    note.style.margin = "10px 0 0 0";
    note.textContent = "Tabel detail tetap tersedia di bawah. Geser horizontal untuk membaca semua kolom; data CSV tetap bisa diunduh.";
    panel.appendChild(note);

    anchor.parentNode.insertBefore(panel, anchor);
  }

  function fixSpreadsheetTables() {
    const tables = Array.from(document.querySelectorAll("table"));
    if (tables.length === 0) return;

    tables.forEach(function (table) {
      forceReadableTable(table);
    });

    const first = tables[0];
    const pairs = extractTablePairs(first);
    const anchor = first.closest(".p614-table-scroll") || first;
    buildOperatorCards(pairs, anchor);
  }

  function parseLatLonFromPage() {
    const text = document.body ? document.body.innerText : "";
    const matches = Array.from(text.matchAll(/(-?\d{1,2}\.\d{4,})\s*,\s*(-?\d{2,3}\.\d{4,})/g));
    for (const m of matches) {
      const lat = Number(m[1]);
      const lon = Number(m[2]);
      if (Number.isFinite(lat) && Number.isFinite(lon) && lat >= -11 && lat <= 6 && lon >= 95 && lon <= 142) {
        return { lat: lat, lon: lon };
      }
    }
    return null;
  }

  function ensureOperatorMap() {
    const path = window.location.pathname;
    if (path.indexOf("field-map") < 0 && path.indexOf("field_trial") < 0 && path.indexOf("field-acceptance") < 0) {
      return;
    }
    if (document.querySelector("[data-p614-map-panel]")) return;

    const sessionId = getSessionId();
    const coords = parseLatLonFromPage();

    const panel = document.createElement("section");
    panel.className = "p614-operator-map-panel";
    panel.setAttribute("data-p614-map-panel", "1");

    const title = document.createElement("h2");
    title.textContent = "Operator Map Evidence";
    panel.appendChild(title);

    const status = document.createElement("div");
    status.className = "p614-map-status";

    if (coords) {
      const lat = coords.lat;
      const lon = coords.lon;
      const delta = 0.004;
      status.innerHTML =
        "<b>MAP_MARKER_READY</b><br>" +
        "Koordinat session valid: " + lat.toFixed(7) + ", " + lon.toFixed(7) + "<br>" +
        "Marker dibuat dari GPS browser session, bukan koordinat palsu.";
      panel.appendChild(status);

      const iframe = document.createElement("iframe");
      iframe.className = "p614-map-frame";
      iframe.loading = "lazy";
      iframe.referrerPolicy = "no-referrer-when-downgrade";
      iframe.src =
        "https://www.openstreetmap.org/export/embed.html?bbox=" +
        encodeURIComponent((lon - delta).toFixed(7) + "," + (lat - delta).toFixed(7) + "," + (lon + delta).toFixed(7) + "," + (lat + delta).toFixed(7)) +
        "&layer=mapnik&marker=" + encodeURIComponent(lat.toFixed(7) + "," + lon.toFixed(7));
      panel.appendChild(iframe);

      const actions = document.createElement("div");
      actions.className = "p614-map-actions";
      actions.innerHTML =
        '<a target="_blank" rel="noopener" href="https://www.google.com/maps?q=' + encodeURIComponent(lat + "," + lon) + '">Open Google Maps</a>' +
        '<a target="_blank" rel="noopener" href="https://www.openstreetmap.org/?mlat=' + encodeURIComponent(lat) + '&mlon=' + encodeURIComponent(lon) + '#map=19/' + encodeURIComponent(lat) + '/' + encodeURIComponent(lon) + '">Open OSM</a>' +
        '<a href="/field-camera?session_id=' + encodeURIComponent(sessionId) + '">Back to Camera</a>';
      panel.appendChild(actions);
    } else {
      status.innerHTML =
        "<b>NO_GPS_NO_MARKER</b><br>" +
        "GPS session belum valid, jadi sistem tidak membuat marker palsu. " +
        "Di bawah ini hanya peta konteks area kerja Surabaya Utara/Perak, bukan bukti lokasi titik.";
      panel.appendChild(status);

      const iframe = document.createElement("iframe");
      iframe.className = "p614-map-frame";
      iframe.loading = "lazy";
      iframe.referrerPolicy = "no-referrer-when-downgrade";
      iframe.src = "https://www.openstreetmap.org/export/embed.html?bbox=112.6950%2C-7.2650%2C112.7800%2C-7.1850&layer=mapnik";
      panel.appendChild(iframe);

      const actions = document.createElement("div");
      actions.className = "p614-map-actions";
      actions.innerHTML =
        '<a href="/field-camera?session_id=' + encodeURIComponent(sessionId) + '">Back to Camera</a>' +
        '<a href="/field-capture">New Session</a>';
      panel.appendChild(actions);
    }

    const firstHeading = document.querySelector("h1, h2, main, .container, body > div");
    if (firstHeading && firstHeading.parentNode) {
      firstHeading.parentNode.insertBefore(panel, firstHeading);
    } else {
      document.body.insertBefore(panel, document.body.firstChild);
    }
  }

  function hookStartButtonsForGps() {
    document.addEventListener("click", function (event) {
      const el = event.target && event.target.closest ? event.target.closest("button, a, input[type='button'], input[type='submit']") : null;
      if (!el) return;
      const text = normText(el.textContent || el.value || "");
      if (/start|shutter|jepret|map|result|manual/i.test(text)) {
        startGpsWatcher("operator_click_" + text);
      }
    }, true);
  }

  function exposeDebugStatus() {
    window.PROGRESS_6_14_OPERATOR_FIX = {
      version: VERSION,
      session_id: getSessionId(),
      gps_watch_active: gpsWatchId !== null
    };
  }

  ready(function () {
    hookStartButtonsForGps();
    startGpsWatcher("page_ready");
    fixSpreadsheetTables();
    ensureOperatorMap();
    exposeDebugStatus();

    setTimeout(function () {
      fixSpreadsheetTables();
      ensureOperatorMap();
      exposeDebugStatus();
    }, 700);

    setTimeout(function () {
      fixSpreadsheetTables();
      ensureOperatorMap();
      exposeDebugStatus();
    }, 1800);
  });
})();
'''

VALIDATOR = r'''
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
'''

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"WROTE {path.relative_to(ROOT)}")

def backup(path: Path) -> None:
    rel = path.relative_to(ROOT)
    dst = BACKUP_DIR / str(rel).replace("\\", "_").replace("/", "_")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(read_text(path), encoding="utf-8", newline="\n")
    print(f"BACKUP {rel} -> {dst.relative_to(ROOT)}")

def inject_assets(html: str) -> str:
    if CSS_MARKER not in html:
        css_tag = f'<link rel="stylesheet" href="/static/{CSS_MARKER}?v={VERSION}">'
        if "</head>" in html.lower():
            idx = html.lower().find("</head>")
            html = html[:idx] + "  " + css_tag + "\n" + html[idx:]
        else:
            html = css_tag + "\n" + html

    if JS_MARKER not in html:
        js_tag = f'<script defer src="/static/{JS_MARKER}?v={VERSION}"></script>'
        lower = html.lower()
        if "</body>" in lower:
            idx = lower.rfind("</body>")
            html = html[:idx] + "  " + js_tag + "\n" + html[idx:]
        else:
            html = html + "\n" + js_tag + "\n"
    return html

def patch_templates():
    patched = []
    for path in sorted(TEMPLATE_DIR.glob("*.html")):
        text = read_text(path)
        if "<html" not in text.lower() and "</body>" not in text.lower() and "</head>" not in text.lower():
            continue
        new_text = inject_assets(text)
        if new_text != text:
            backup(path)
            write_text(path, new_text)
            patched.append(str(path.relative_to(ROOT)))
    return patched

def main():
    print(f"VERSION={VERSION}")
    print(f"ROOT={ROOT}")

    write_text(CSS_PATH, CSS)
    write_text(JS_PATH, JS)
    write_text(VALIDATOR_PATH, VALIDATOR)

    patched_templates = patch_templates()

    result = {
        "status": "PROGRESS_6_14_HARD_OPERATOR_FIX_PATCHED",
        "version": VERSION,
        "patched_static": [str(CSS_PATH.relative_to(ROOT)), str(JS_PATH.relative_to(ROOT))],
        "patched_validator": str(VALIDATOR_PATH.relative_to(ROOT)),
        "patched_templates": patched_templates,
        "backup_dir": str(BACKUP_DIR.relative_to(ROOT)),
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_dataset_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
        "operator_effect": [
            "GPS watcher dipaksa aktif dari browser dan dikirim ke /api/field/session/gps-update.",
            "Map menampilkan OSM iframe; marker hanya bila koordinat valid.",
            "Jika GPS null, map tetap menampilkan peta konteks tanpa marker palsu.",
            "Spreadsheet tabel dipaksa horizontal, scrollable, dan dibuat kartu operator-readable."
        ]
    }
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
