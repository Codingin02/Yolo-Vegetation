from __future__ import annotations

import html
import re
import urllib.parse
from string import Template

VERSION = "progress6_16b_visual_map_spreadsheet_hard_fix"

LAT_MIN = -11.5
LAT_MAX = 6.5
LON_MIN = 94.0
LON_MAX = 142.5

def _decode_body(body: bytes) -> str:
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return body.decode(enc)
        except Exception:
            pass
    return body.decode("utf-8", errors="replace")

def _strip_tags(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text or "", flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()

def _extract_session_id(path: str, text: str = "") -> str:
    m = re.search(r"FS_\d{8}_\d{6}_[A-Za-z0-9]+", path or "")
    if m:
        return m.group(0)
    m = re.search(r"FS_\d{8}_\d{6}_[A-Za-z0-9]+", text or "")
    if m:
        return m.group(0)
    return ""

def _extract_point_id(text: str) -> str:
    plain = _strip_tags(text)
    patterns = [
        r"Point\s*:\s*([A-Za-z0-9_ -]+)",
        r"Point\s*ID\s*:\s*([A-Za-z0-9_ -]+)",
        r"point_id\s*[=:]\s*([A-Za-z0-9_ -]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, plain, flags=re.I)
        if m:
            return m.group(1).strip()
    return "V001_pohon_sono"

def _valid_lat_lon(lat: float, lon: float) -> bool:
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX

def _extract_lat_lon(text: str):
    plain = _strip_tags(text)

    for m in re.finditer(r"(-?\d{1,2}\.\d{4,})\s*,\s*(-?\d{2,3}\.\d{4,})", plain):
        try:
            lat = float(m.group(1))
            lon = float(m.group(2))
        except Exception:
            continue
        if _valid_lat_lon(lat, lon):
            return lat, lon

    lat_matches = re.findall(r"(?:latitude|lat)\D{0,40}(-?\d{1,2}\.\d{4,})", text or "", flags=re.I)
    lon_matches = re.findall(r"(?:longitude|lng|lon)\D{0,40}(-?\d{2,3}\.\d{4,})", text or "", flags=re.I)

    for la in lat_matches:
        for lo in lon_matches:
            try:
                lat = float(la)
                lon = float(lo)
            except Exception:
                continue
            if _valid_lat_lon(lat, lon):
                return lat, lon

    return None

def _extract_accuracy(text: str) -> str:
    plain = _strip_tags(text)
    patterns = [
        r"GPS\s*Accuracy\s*:\s*([0-9.]+)",
        r"Accuracy\s*:\s*([0-9.]+)",
        r"gps_accuracy_m\D+([0-9.]+)",
        r"accuracy\D+([0-9.]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, plain, flags=re.I)
        if m:
            return m.group(1)
    return "NOT_PROVIDED"

def _osm_embed(lat: float, lon: float) -> str:
    delta = 0.003
    bbox = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
    return "https://www.openstreetmap.org/export/embed.html?" + urllib.parse.urlencode({
        "bbox": bbox,
        "layer": "mapnik",
        "marker": f"{lat},{lon}",
    })

def _osm_context() -> str:
    return "https://www.openstreetmap.org/export/embed.html?bbox=112.7200%2C-7.2400%2C112.7600%2C-7.2100&layer=mapnik"

def _google_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat},{lon}"

def _osm_link(lat: float, lon: float) -> str:
    return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}"

def _build_map_page(path: str, old_html: str) -> str:
    session_id = _extract_session_id(path, old_html)
    point_id = _extract_point_id(old_html)
    accuracy = _extract_accuracy(old_html)
    latlon = _extract_lat_lon(old_html)

    if latlon:
        lat, lon = latlon
        badges = "<span>MAP_IFRAME_READY</span><span>GPS_MARKER_READY</span><span>GPS_PRECISION_OK</span>"
        marker_cards = (
            f'<div class="p616-card"><b>Koordinat marker</b><span>{lat:.7f}, {lon:.7f}</span></div>'
            f'<div class="p616-card"><b>GPS accuracy</b><span>{html.escape(str(accuracy))} m</span></div>'
        )
        iframe_src = html.escape(_osm_embed(lat, lon), quote=True)
        external_links = (
            f'<a href="{html.escape(_osm_link(lat, lon), quote=True)}" target="_blank" rel="noopener">Buka OpenStreetMap</a>'
            f'<a href="{html.escape(_google_link(lat, lon), quote=True)}" target="_blank" rel="noopener">Buka Google Maps</a>'
        )
        note = "Marker dibuat dari koordinat session valid. GPS hanya evidence lokasi, bukan kalibrasi pixel-to-meter."
    else:
        badges = "<span>MAP_CONTEXT_READY</span><span>NO_GPS_NO_FAKE_MARKER</span>"
        marker_cards = (
            '<div class="p616-card warn"><b>Koordinat marker</b><span>GPS belum valid. Marker tidak dibuat.</span></div>'
            '<div class="p616-card warn"><b>Instruksi</b><span>Kembali ke camera, tunggu GPS_READY_xM, lalu Shutter ulang.</span></div>'
        )
        iframe_src = _osm_context()
        external_links = ""
        note = "Peta konteks tampil tanpa marker palsu karena koordinat session belum valid."

    template = Template("""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-store">
<title>Field Session Map</title>
<style>
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 18px;
  background: radial-gradient(circle at top left, #135c3d, #062d1f 58%);
  color: #ecfff7;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
}
.p616-wrap {
  width: min(1180px, calc(100vw - 24px));
  margin: 0 auto;
}
.p616-panel {
  border: 1px solid rgba(255,255,255,.22);
  border-radius: 24px;
  background: rgba(7,46,31,.94);
  padding: 18px;
  box-shadow: 0 24px 60px rgba(0,0,0,.28);
}
.p616-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.p616-badges span {
  border: 1px solid rgba(255,255,255,.24);
  border-radius: 999px;
  padding: 7px 11px;
  background: rgba(255,255,255,.10);
  font-size: 12px;
  font-weight: 900;
}
h1 {
  margin: 8px 0 14px;
  font-size: clamp(28px, 4vw, 46px);
  line-height: 1.05;
}
.p616-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 10px;
  margin: 14px 0 16px;
}
.p616-card {
  border: 1px solid rgba(255,255,255,.22);
  border-radius: 16px;
  background: rgba(255,255,255,.09);
  padding: 12px;
  min-height: 70px;
}
.p616-card b {
  display: block;
  color: rgba(236,255,247,.75);
  font-size: 12px;
  margin-bottom: 6px;
}
.p616-card span {
  display: block;
  font-weight: 900;
  overflow-wrap: anywhere;
}
.p616-card.warn {
  background: rgba(255,198,41,.13);
}
.p616-map-iframe {
  display: block;
  width: 100%;
  height: min(66vh, 720px);
  min-height: 430px;
  border: 0;
  border-radius: 20px;
  background: #e6f0ec;
}
.p616-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 14px 0;
}
.p616-actions a,
.p616-back {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  border-radius: 12px;
  padding: 11px 14px;
  background: #0f7655;
  color: white;
  text-decoration: none;
  font-weight: 900;
}
.p616-note {
  color: rgba(236,255,247,.78);
  line-height: 1.55;
}
@media (max-width: 760px) {
  body { padding: 10px; }
  .p616-panel { padding: 13px; border-radius: 18px; }
  .p616-grid { grid-template-columns: 1fr; }
  .p616-map-iframe { height: 60vh; min-height: 360px; }
}
</style>
</head>
<body>
<div class="p616-wrap" id="progress6_16_visual_map_mount">
  <div class="p616-panel">
    <div class="p616-badges">$badges</div>
    <h1>Field Session Map</h1>
    <div class="p616-grid">
      <div class="p616-card"><b>Session ID</b><span>$session_id</span></div>
      <div class="p616-card"><b>Point ID</b><span>$point_id</span></div>
      $marker_cards
    </div>
    <iframe class="p616-map-iframe" src="$iframe_src" loading="eager" referrerpolicy="no-referrer-when-downgrade" title="Field session map"></iframe>
    <div class="p616-actions">$external_links</div>
    <p class="p616-note">$note</p>
    <a class="p616-back" href="/field-camera?session_id=$session_id">Kembali ke Camera</a>
  </div>
</div>
</body>
</html>""")

    return template.safe_substitute(
        badges=badges,
        session_id=html.escape(session_id or "SESSION_ID_NOT_FOUND"),
        point_id=html.escape(point_id),
        marker_cards=marker_cards,
        iframe_src=iframe_src,
        external_links=external_links,
        note=html.escape(note),
    )

SHEET_STYLE = """
<style id="progress6_16_sheet_style">
html, body {
  max-width: none !important;
  overflow-x: auto !important;
}
body {
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif !important;
}
#progress6_16_readable_cards {
  width: min(1200px, calc(100vw - 28px)) !important;
  margin: 18px auto !important;
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)) !important;
  gap: 12px !important;
}
.p616-sheet-card {
  border: 1px solid rgba(0,0,0,.12) !important;
  border-radius: 16px !important;
  padding: 12px !important;
  background: #ffffff !important;
  box-shadow: 0 8px 24px rgba(0,0,0,.06) !important;
  color: #102023 !important;
}
.p616-sheet-card b {
  display: block !important;
  font-size: 12px !important;
  margin-bottom: 7px !important;
  opacity: .72 !important;
}
.p616-sheet-card span {
  display: block !important;
  font-size: 14px !important;
  font-weight: 800 !important;
  line-height: 1.35 !important;
  overflow-wrap: anywhere !important;
}
.progress6_16_table_scroll {
  width: min(1200px, calc(100vw - 28px)) !important;
  max-width: min(1200px, calc(100vw - 28px)) !important;
  margin: 16px auto !important;
  overflow-x: auto !important;
  overflow-y: visible !important;
  border-radius: 18px !important;
  border: 1px solid rgba(0,0,0,.12) !important;
  background: #fff !important;
  box-shadow: 0 12px 30px rgba(0,0,0,.08) !important;
  padding: 10px !important;
}
.progress6_16_table_scroll:before {
  content: "Geser tabel ke kanan/kiri untuk melihat seluruh kolom";
  display: block !important;
  padding: 8px 4px 12px !important;
  font-weight: 900 !important;
  color: #0d5945 !important;
}
.progress6_16_table_scroll table,
table.progress6_16_readable_table {
  table-layout: auto !important;
  width: max-content !important;
  min-width: 2400px !important;
  max-width: none !important;
  border-collapse: collapse !important;
}
.progress6_16_table_scroll th,
.progress6_16_table_scroll td,
table.progress6_16_readable_table th,
table.progress6_16_readable_table td {
  writing-mode: horizontal-tb !important;
  text-orientation: mixed !important;
  white-space: nowrap !important;
  word-break: normal !important;
  overflow-wrap: normal !important;
  transform: none !important;
  rotate: none !important;
  min-width: 128px !important;
  max-width: 320px !important;
  width: auto !important;
  padding: 10px 12px !important;
  font-size: 12px !important;
  line-height: 1.25 !important;
  vertical-align: top !important;
  overflow: visible !important;
}
.progress6_16_table_scroll th {
  background: #0f7557 !important;
  color: #fff !important;
  font-weight: 900 !important;
  position: sticky !important;
  top: 0 !important;
  z-index: 2 !important;
}
.progress6_16_table_scroll td {
  color: #102023 !important;
  background: #fff !important;
}
@media (max-width: 760px) {
  #progress6_16_readable_cards {
    grid-template-columns: 1fr !important;
    width: calc(100vw - 18px) !important;
  }
  .progress6_16_table_scroll {
    width: calc(100vw - 18px) !important;
    max-width: calc(100vw - 18px) !important;
  }
}
</style>
"""

SHEET_SCRIPT = """
<script id="progress6_16_sheet_script">
(function () {
  function clean(s) {
    return (s || "").replace(/\\s+/g, " ").trim();
  }

  function makeCards(table) {
    if (!table || document.getElementById("progress6_16_readable_cards")) return;

    var rows = Array.from(table.querySelectorAll("tr"));
    if (rows.length < 2) return;

    var headers = Array.from(rows[0].children);
    var cells = Array.from(rows[1].children);

    var cards = document.createElement("section");
    cards.id = "progress6_16_readable_cards";

    for (var i = 0; i < headers.length; i++) {
      var key = clean(headers[i].innerText || headers[i].textContent);
      var val = cells[i] ? clean(cells[i].innerText || cells[i].textContent) : "";
      if (!key) continue;

      var card = document.createElement("div");
      card.className = "p616-sheet-card";

      var b = document.createElement("b");
      b.textContent = key;

      var span = document.createElement("span");
      span.textContent = val || "-";

      card.appendChild(b);
      card.appendChild(span);
      cards.appendChild(card);
    }

    var title = document.querySelector("h1, h2, h3");
    if (title && title.parentNode) {
      title.parentNode.insertBefore(cards, title.nextSibling);
    } else {
      document.body.insertBefore(cards, document.body.firstChild);
    }
  }

  function wrapTable(table) {
    if (!table || table.closest(".progress6_16_table_scroll")) return;

    table.classList.add("progress6_16_readable_table");

    var wrap = document.createElement("div");
    wrap.className = "progress6_16_table_scroll";

    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
  }

  function forceCellStyle() {
    Array.from(document.querySelectorAll("th,td")).forEach(function(cell) {
      cell.style.writingMode = "horizontal-tb";
      cell.style.whiteSpace = "nowrap";
      cell.style.wordBreak = "normal";
      cell.style.overflowWrap = "normal";
      cell.style.transform = "none";
      cell.style.minWidth = "128px";
      cell.style.maxWidth = "320px";
    });
  }

  function run() {
    var tables = Array.from(document.querySelectorAll("table"));
    if (!tables.length) return;

    tables.sort(function(a, b) {
      return b.querySelectorAll("th,td").length - a.querySelectorAll("th,td").length;
    });

    var table = tables[0];
    makeCards(table);
    wrapTable(table);
    forceCellStyle();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }

  setTimeout(run, 300);
  setTimeout(run, 1000);
})();
</script>
"""

def _inject_sheet_fix(old_html: str) -> str:
    if "progress6_16_sheet_style" in old_html:
        return old_html

    if re.search(r"</head\s*>", old_html, flags=re.I):
        old_html = re.sub(r"</head\s*>", lambda m: SHEET_STYLE + "\n" + m.group(0), old_html, count=1, flags=re.I)
    else:
        old_html = SHEET_STYLE + "\n" + old_html

    if re.search(r"</body\s*>", old_html, flags=re.I):
        old_html = re.sub(r"</body\s*>", lambda m: SHEET_SCRIPT + "\n" + m.group(0), old_html, count=1, flags=re.I)
    else:
        old_html = old_html + "\n" + SHEET_SCRIPT

    return old_html

def _empty_session_page(path: str) -> str:
    kind = "map" if "field-map" in path else "spreadsheet"
    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Session kosong</title>
</head>
<body style="font-family:system-ui;padding:24px;background:#062d1f;color:white">
<h1>SESSION_ID_EMPTY_STOP</h1>
<p>URL {html.escape(kind)} tidak boleh dibuka tanpa session_id. Kembali ke /field-capture, tekan Start, izinkan kamera/GPS, lalu Shutter.</p>
<a style="color:#b8ffe4" href="/field-capture">Kembali ke Field Capture</a>
</body>
</html>"""

def _send_html(start_response, status: str, content: str):
    body = content.encode("utf-8")
    start_response(status, [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"),
        ("Pragma", "no-cache"),
        ("X-Progress-616-Visual-Fix", VERSION),
    ])
    return [body]

class Progress616VisualResultMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "") or ""
        is_map = path.startswith("/field-map/session")
        is_sheet = path.startswith("/field-spreadsheet/session")

        if not (is_map or is_sheet):
            return self.app(environ, start_response)

        if path.rstrip("/") in ("/field-map/session", "/field-spreadsheet/session"):
            return _send_html(start_response, "400 BAD REQUEST", _empty_session_page(path))

        captured = {
            "status": "200 OK",
            "headers": [],
            "exc_info": None,
        }

        def capture_start_response(status, headers, exc_info=None):
            captured["status"] = status
            captured["headers"] = headers
            captured["exc_info"] = exc_info
            return lambda data: None

        app_iter = self.app(environ, capture_start_response)
        chunks = []

        try:
            for chunk in app_iter:
                if isinstance(chunk, bytes):
                    chunks.append(chunk)
                else:
                    chunks.append(str(chunk).encode("utf-8", errors="replace"))
        finally:
            close = getattr(app_iter, "close", None)
            if callable(close):
                close()

        old_html = _decode_body(b"".join(chunks))

        if is_map:
            return _send_html(start_response, "200 OK", _build_map_page(path, old_html))

        if is_sheet:
            return _send_html(start_response, "200 OK", _inject_sheet_fix(old_html))

        return _send_html(start_response, captured["status"], old_html)

def install_progress6_16_visual_result_middleware(flask_app):
    if getattr(flask_app, "_progress6_16_visual_result_middleware_installed", False):
        return flask_app

    flask_app.wsgi_app = Progress616VisualResultMiddleware(flask_app.wsgi_app)
    flask_app._progress6_16_visual_result_middleware_installed = True
    return flask_app