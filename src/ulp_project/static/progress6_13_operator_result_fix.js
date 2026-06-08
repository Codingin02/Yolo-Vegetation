
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
