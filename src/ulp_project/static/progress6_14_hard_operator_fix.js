
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
