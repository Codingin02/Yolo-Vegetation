(function () {
  "use strict";

  var PATCH = "final_live_force_yolo_frame_v1";
  var originalFetch = window.fetch ? window.fetch.bind(window) : null;
  var lastSentAt = 0;
  var lastBoxData = null;
  var loopStarted = false;

  if (!originalFetch) {
    return;
  }

  function qs(name) {
    try {
      return new URLSearchParams(window.location.search).get(name) || "";
    } catch (e) {
      return "";
    }
  }

  function sessionId() {
    var q = qs("session_id");
    if (q) return q;

    var txt = "";
    try { txt = document.body ? document.body.innerText : ""; } catch (e) {}
    var m = txt.match(/FS_\d{8}_\d{6}_[a-zA-Z0-9]+/);
    return m ? m[0] : "";
  }

  function videoEl() {
    var videos = Array.prototype.slice.call(document.querySelectorAll("video"));
    for (var i = 0; i < videos.length; i++) {
      if (videos[i].videoWidth > 0 && videos[i].videoHeight > 0) return videos[i];
    }
    return videos[0] || null;
  }

  function isYoloOn() {
    var txt = "";
    try { txt = document.body ? document.body.innerText : ""; } catch (e) {}

    if (/YOLO-FIRST\s+OFF/i.test(txt)) return false;
    if (/AI detection OFF/i.test(txt)) return false;

    if (/YOLO-FIRST\s*(200|ON)/i.test(txt)) return true;
    if (/AI detection ON/i.test(txt)) return true;
    if (/membaca frame realtime/i.test(txt)) return true;

    var pressed = document.querySelector('[aria-pressed="true"], .active, .is-active, .on');
    if (pressed && /YOLO|AI|realtime|detect/i.test(pressed.textContent || "")) return true;

    return false;
  }

  function ensureCanvas() {
    var c = document.getElementById("final-live-yolo-overlay");
    if (c) return c;

    c = document.createElement("canvas");
    c.id = "final-live-yolo-overlay";
    c.style.position = "fixed";
    c.style.left = "0";
    c.style.top = "0";
    c.style.width = "100vw";
    c.style.height = "100vh";
    c.style.zIndex = "1400";
    c.style.pointerEvents = "none";
    c.style.mixBlendMode = "normal";
    document.body.appendChild(c);
    return c;
  }

  function captureFrame() {
    var v = videoEl();
    if (!v || !v.videoWidth || !v.videoHeight) return "";

    var maxW = 640;
    var scale = Math.min(1, maxW / v.videoWidth);
    var w = Math.max(320, Math.round(v.videoWidth * scale));
    var h = Math.max(240, Math.round(v.videoHeight * scale));

    var c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    var ctx = c.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(v, 0, 0, w, h);
    return c.toDataURL("image/jpeg", 0.72);
  }

  function normalizePayload(raw) {
    var payload = {};
    if (raw && typeof raw === "object") payload = raw;

    var frame = payload.frame_base64 || payload.image_base64 || payload.image || payload.snapshot_base64 || "";
    if (!frame) frame = captureFrame();

    payload.session_id = payload.session_id || sessionId();
    payload.frame_base64 = frame;
    payload.image_base64 = frame;
    payload.image = frame;
    payload.realtime_mode = "YOLO_FIRST_FORCED_HP_LIVE";
    payload.source = payload.source || "final_live_force_yolo_frame";
    payload.no_fake_detection = true;
    payload.no_fake_gps = true;
    payload.no_fake_clearance = true;
    payload.legacy_vision_redirected_to_frame = true;

    return payload;
  }

  window.fetch = function (input, init) {
    var url = "";

    try {
      if (typeof input === "string") url = input;
      else if (input && input.url) url = input.url;
    } catch (e) {}

    if (url.indexOf("/api/field/session/vision-analyze") !== -1) {
      var body = {};
      try {
        if (init && init.body && typeof init.body === "string") {
          body = JSON.parse(init.body);
        }
      } catch (e) {
        body = {};
      }

      var payload = normalizePayload(body);

      setToast("Vision legacy dialihkan ke YOLO frame", false);

      return originalFetch("/api/field/session/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    return originalFetch(input, init);
  };

  function extractBoxes(data) {
    var boxes = [];

    function pushBox(item) {
      if (!item || typeof item !== "object") return;

      var b = item.bbox_xyxy || item.bbox || item.box || item.tree_bbox;
      if (!b && item.x1 !== undefined) b = [item.x1, item.y1, item.x2, item.y2];

      if (typeof b === "string") {
        try { b = JSON.parse(b); } catch (e) { b = null; }
      }

      if (!Array.isArray(b) || b.length < 4) return;

      boxes.push({
        bbox: [Number(b[0]), Number(b[1]), Number(b[2]), Number(b[3])],
        label: item.class_name || item.label || item.name || "pohon_sono",
        conf: item.confidence || item.conf || item.tree_confidence || data.tree_confidence || ""
      });
    }

    if (data && Array.isArray(data.detections)) data.detections.forEach(pushBox);
    if (data && Array.isArray(data.tracked_detections)) data.tracked_detections.forEach(pushBox);
    if (data && data.progress6_18_tracking && Array.isArray(data.progress6_18_tracking.tracked_detections)) {
      data.progress6_18_tracking.tracked_detections.forEach(pushBox);
    }
    if (data && data.tree_bbox) {
      pushBox({ tree_bbox: data.tree_bbox, label: "pohon_sono", tree_confidence: data.tree_confidence });
    }

    return boxes;
  }

  function drawBoxes(data) {
    var c = ensureCanvas();
    var ctx = c.getContext("2d");
    var dpr = window.devicePixelRatio || 1;
    var w = Math.floor(window.innerWidth * dpr);
    var h = Math.floor(window.innerHeight * dpr);

    if (c.width !== w || c.height !== h) {
      c.width = w;
      c.height = h;
    }

    ctx.clearRect(0, 0, c.width, c.height);

    var boxes = extractBoxes(data || {});
    lastBoxData = boxes;

    if (!boxes.length) return;

    var v = videoEl();
    var scaleX = c.width / 640;
    var scaleY = c.height / 480;

    if (v && v.videoWidth && v.videoHeight) {
      scaleX = c.width / v.videoWidth;
      scaleY = c.height / v.videoHeight;
    }

    ctx.lineWidth = Math.max(3, 3 * dpr);
    ctx.font = Math.max(16, 16 * dpr) + "px system-ui";
    ctx.textBaseline = "top";

    boxes.forEach(function (box) {
      var b = box.bbox;
      var x1 = Math.max(0, b[0] * scaleX);
      var y1 = Math.max(0, b[1] * scaleY);
      var x2 = Math.min(c.width, b[2] * scaleX);
      var y2 = Math.min(c.height, b[3] * scaleY);

      ctx.strokeStyle = "#00ff7b";
      ctx.fillStyle = "rgba(0,255,123,0.18)";
      ctx.strokeRect(x1, y1, Math.max(1, x2 - x1), Math.max(1, y2 - y1));
      ctx.fillRect(x1, y1, Math.max(1, x2 - x1), Math.max(1, y2 - y1));

      var label = String(box.label || "pohon_sono");
      if (box.conf !== "") label += " " + String(box.conf).slice(0, 5);

      var tw = ctx.measureText(label).width + 12 * dpr;
      ctx.fillStyle = "rgba(0,80,45,0.92)";
      ctx.fillRect(x1, Math.max(0, y1 - 26 * dpr), tw, 24 * dpr);
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, x1 + 6 * dpr, Math.max(0, y1 - 24 * dpr));
    });
  }

  function setToast(msg, danger) {
    var el = document.getElementById("final-live-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "final-live-toast";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.className = danger ? "final-live-toast danger" : "final-live-toast";
  }

  function updateCompactHud(data) {
    var hud = document.getElementById("final-live-mini-hud");
    if (!hud) {
      hud = document.createElement("div");
      hud.id = "final-live-mini-hud";
      hud.innerHTML = '<span title="GPS">📍</span><span title="Camera">📷</span><span title="YOLO">🤖</span><span title="Shutter">●</span>';
      document.body.appendChild(hud);
    }

    var gps = /GPS_READY/i.test(document.body.innerText || "") ? "📍" : "⌖";
    var cam = /CAMERA_STREAM_READY/i.test(document.body.innerText || "") ? "📷" : "▣";
    var yolo = isYoloOn() ? "🤖" : "△";
    var det = data && (extractBoxes(data).length || data.tree_detected) ? "🌳" : "●";

    hud.innerHTML =
      '<span title="GPS">' + gps + '</span>' +
      '<span title="Camera">' + cam + '</span>' +
      '<span title="YOLO">' + yolo + '</span>' +
      '<span title="Detection">' + det + '</span>';
  }

  function compactLegacyText() {
    document.body.classList.add("final-live-compact-ui");

    var pairs = [
      [/^GPS_READY/i, "📍"],
      [/^GPS_WAITING/i, "⌖"],
      [/^CAMERA_STREAM_READY/i, "📷"],
      [/^CAMERA_WAITING/i, "▣"],
      [/^SHUTTER_WAITING/i, "●"],
      [/^SHUTTER_SAVING/i, "●"],
      [/^TREE_MODEL_READY_CANDIDATE/i, "🌳"],
      [/^ROUTE_REPAIR_READY/i, "↔"],
      [/^YOLO-FIRST\s*200/i, "🤖"],
      [/^YOLO-FIRST\s*OFF/i, "△"]
    ];

    var els = Array.prototype.slice.call(document.querySelectorAll("div,span,b,strong,p"));
    els.forEach(function (el) {
      if (el.children && el.children.length > 0) return;
      var t = (el.textContent || "").trim();
      if (!t || t.length > 80) return;

      for (var i = 0; i < pairs.length; i++) {
        if (pairs[i][0].test(t)) {
          el.setAttribute("title", t);
          el.setAttribute("data-final-icon", pairs[i][1]);
          el.classList.add("final-live-icon-chip");
          el.textContent = pairs[i][1];
          return;
        }
      }
    });
  }

  async function sendFrame(reason) {
    if (!isYoloOn()) {
      updateCompactHud(null);
      return;
    }

    var now = Date.now();
    if (now - lastSentAt < 900) return;
    lastSentAt = now;

    var sid = sessionId();
    if (!sid) {
      setToast("Session ID belum terbaca", true);
      return;
    }

    var frame = captureFrame();
    if (!frame) {
      setToast("Kamera belum siap untuk frame", true);
      return;
    }

    var payload = {
      session_id: sid,
      frame_base64: frame,
      image_base64: frame,
      image: frame,
      source: reason || "final_live_force_yolo_frame_loop",
      realtime_mode: "YOLO_FIRST_HP_LIVE_1S",
      no_fake_detection: true,
      no_fake_gps: true,
      no_fake_clearance: true
    };

    try {
      var res = await originalFetch("/api/field/session/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      var data = null;
      try { data = await res.json(); } catch (e) { data = { ok: false, status: "NON_JSON_RESPONSE" }; }

      drawBoxes(data);
      updateCompactHud(data);

      var boxes = extractBoxes(data);
      if (res.ok && boxes.length) {
        setToast("YOLO frame OK: pohon_sono terdeteksi", false);
      } else if (res.ok) {
        setToast("YOLO frame OK: belum ada objek project", false);
      } else {
        setToast("YOLO frame HTTP " + res.status, true);
      }
    } catch (err) {
      setToast("YOLO frame error: " + (err && err.message ? err.message : err), true);
    }
  }

  function boot() {
    if (loopStarted) return;
    loopStarted = true;

    ensureCanvas();
    updateCompactHud(null);
    compactLegacyText();

    window.setInterval(function () {
      compactLegacyText();
      sendFrame("final_live_interval_1s");
    }, 1000);

    window.addEventListener("resize", function () {
      drawBoxes({ detections: lastBoxData || [] });
    });

    document.addEventListener("click", function () {
      window.setTimeout(function () {
        compactLegacyText();
        sendFrame("final_live_after_click");
      }, 250);
    }, true);

    setToast("YOLO-first live patch aktif", false);
    try { console.log("[FINAL LIVE] " + PATCH + " loaded"); } catch (e) {}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
