(function () {
  "use strict";

  var PATCH_ID = "PROGRESS_6_27_YOLO_FIRST_LOCK";
  var state = {
    enabled: false,
    busy: false,
    timer: null,
    tick: 0,
    lastResult: null,
    lastSessionId: "",
    blockedVisionAnalyzeCount: 0,
    lastFrameAt: 0
  };

  function qs(name) {
    return new URLSearchParams(window.location.search).get(name) || "";
  }

  function sessionId() {
    var sid = qs("session_id") || qs("session") || state.lastSessionId || "";
    if (sid) state.lastSessionId = sid;
    return sid;
  }

  function ensureBadge() {
    var badge = document.getElementById("progress627YoloFirstBadge");
    if (badge) return badge;

    badge = document.createElement("button");
    badge.id = "progress627YoloFirstBadge";
    badge.type = "button";
    badge.textContent = "YOLO-FIRST OFF";
    badge.style.position = "fixed";
    badge.style.right = "10px";
    badge.style.top = "calc(10px + env(safe-area-inset-top))";
    badge.style.zIndex = "99999";
    badge.style.border = "1px solid rgba(255,255,255,.25)";
    badge.style.borderRadius = "999px";
    badge.style.padding = "8px 12px";
    badge.style.font = "700 12px system-ui";
    badge.style.color = "#fff";
    badge.style.background = "rgba(40,40,40,.68)";
    badge.style.backdropFilter = "blur(10px)";
    badge.style.boxShadow = "0 10px 24px rgba(0,0,0,.35)";
    badge.addEventListener("click", function () {
      if (state.enabled) stopLoop("manual_badge_toggle");
      else startLoop("manual_badge_toggle");
    });
    document.body.appendChild(badge);
    return badge;
  }

  function setBadge(text, on) {
    var badge = ensureBadge();
    badge.textContent = text;
    badge.style.background = on ? "rgba(0,110,80,.78)" : "rgba(40,40,40,.68)";
  }

  function findVideo() {
    return document.querySelector("video") ||
      document.getElementById("video") ||
      document.getElementById("cameraVideo") ||
      document.getElementById("fieldVideo");
  }

  function canvasFromVideo(video) {
    if (!video || !video.videoWidth || !video.videoHeight) return null;

    var maxW = 640;
    var scale = Math.min(1, maxW / video.videoWidth);
    var w = Math.max(1, Math.round(video.videoWidth * scale));
    var h = Math.max(1, Math.round(video.videoHeight * scale));

    var c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    var ctx = c.getContext("2d", { willReadFrequently: false });
    ctx.drawImage(video, 0, 0, w, h);
    return c;
  }

  function ensureOverlayCanvas(video) {
    var c = document.getElementById("progress627YoloFirstOverlay");
    if (!c) {
      c = document.createElement("canvas");
      c.id = "progress627YoloFirstOverlay";
      c.style.position = "fixed";
      c.style.inset = "0";
      c.style.width = "100vw";
      c.style.height = "100dvh";
      c.style.pointerEvents = "none";
      c.style.zIndex = "99990";
      document.body.appendChild(c);
    }

    var rect = video ? video.getBoundingClientRect() : { width: window.innerWidth, height: window.innerHeight };
    c.width = Math.max(1, Math.round(rect.width || window.innerWidth));
    c.height = Math.max(1, Math.round(rect.height || window.innerHeight));
    return c;
  }

  function clearOverlay() {
    var c = document.getElementById("progress627YoloFirstOverlay");
    if (!c) return;
    var ctx = c.getContext("2d");
    ctx.clearRect(0, 0, c.width, c.height);
  }

  function renderResult(result) {
    var video = findVideo();
    var c = ensureOverlayCanvas(video);
    var ctx = c.getContext("2d");
    ctx.clearRect(0, 0, c.width, c.height);

    ctx.font = "700 14px system-ui";
    ctx.fillStyle = "rgba(0,0,0,.48)";
    ctx.fillRect(12, 52, Math.min(520, c.width - 24), 66);
    ctx.fillStyle = "#ffffff";

    var status = result && (result.tracking_status || result.frame_status || result.status) || "FRAME_SENT";
    var model = result && (result.model_status || result.tree_model_status || "MODEL_STATUS_UNKNOWN");
    var count = result && (result.detection_count || result.total_detections || 0);

    ctx.fillText("YOLO-FIRST: " + status, 24, 78);
    ctx.fillText("Model: " + model + " | Deteksi: " + count, 24, 101);

    var detections = [];
    if (result && Array.isArray(result.detections)) detections = result.detections;
    if (result && result.progress6_18_tracking && Array.isArray(result.progress6_18_tracking.detections)) {
      detections = result.progress6_18_tracking.detections;
    }

    detections.slice(0, 20).forEach(function (d) {
      var box = d.xyxy || d.box || d.bbox || null;
      if (!box || box.length < 4) return;
      var x1 = Number(box[0]), y1 = Number(box[1]), x2 = Number(box[2]), y2 = Number(box[3]);
      if (!isFinite(x1 + y1 + x2 + y2)) return;

      ctx.strokeStyle = "rgba(0,255,180,.95)";
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, Math.max(1, x2 - x1), Math.max(1, y2 - y1));

      var label = d.label || d.class_name || d.name || "object";
      var conf = d.confidence || d.conf || "";
      ctx.fillStyle = "rgba(0,80,60,.9)";
      ctx.fillRect(x1, Math.max(0, y1 - 22), 190, 22);
      ctx.fillStyle = "#fff";
      ctx.fillText(label + (conf ? " " + Number(conf).toFixed(2) : ""), x1 + 6, Math.max(16, y1 - 6));
    });
  }

  async function sendFrameOnce() {
    if (!state.enabled || state.busy) return;

    var sid = sessionId();
    var video = findVideo();

    if (!sid) {
      setBadge("YOLO-FIRST NO SESSION", false);
      return;
    }

    if (!video || video.readyState < 2) {
      setBadge("YOLO-FIRST WAIT VIDEO", true);
      return;
    }

    var canvas = canvasFromVideo(video);
    if (!canvas) {
      setBadge("YOLO-FIRST NO FRAME", true);
      return;
    }

    var dataUrl = canvas.toDataURL("image/jpeg", 0.72);
    state.busy = true;
    state.tick += 1;

    try {
      var response = await fetch("/api/field/session/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sid,
          frame_base64: dataUrl,
          image_base64: dataUrl,
          source: PATCH_ID,
          realtime_mode: "YOLO_FIRST",
          no_fake_detection: true,
          shutter_triggered: false,
          client_tick: state.tick,
          client_time: new Date().toISOString()
        })
      });

      var result = {};
      try { result = await response.json(); } catch (e) { result = { ok: response.ok, status: "NON_JSON_RESPONSE" }; }

      result.http_status = response.status;
      state.lastResult = result;
      state.lastFrameAt = Date.now();

      setBadge("YOLO-FIRST " + response.status, response.ok);
      renderResult(result);
    } catch (err) {
      setBadge("YOLO-FIRST ERROR", false);
      state.lastResult = { ok: false, status: "FRAME_SEND_ERROR", message: String(err) };
    } finally {
      state.busy = false;
    }
  }

  function startLoop(reason) {
    if (state.enabled) return;

    state.enabled = true;
    warmupYoloFirstOnce();
    setBadge("YOLO-FIRST ON", true);
    clearOverlay();

    if (state.timer) clearInterval(state.timer);
    state.timer = setInterval(sendFrameOnce, 1000);
    sendFrameOnce();

    try {
      console.log("[6.27] YOLO-FIRST loop started:", reason || "");
    } catch (e) {}
  }

  function stopLoop(reason) {
    state.enabled = false;
    if (state.timer) clearInterval(state.timer);
    state.timer = null;
    state.busy = false;
    clearOverlay();
    setBadge("YOLO-FIRST OFF", false);

    try {
      console.log("[6.27] YOLO-FIRST loop stopped:", reason || "");
    } catch (e) {}
  }

  // Blokir cloud vision agar tidak menjadi realtime core ketika YOLO-FIRST ON.
  var originalFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    var url = "";
    try { url = typeof input === "string" ? input : (input && input.url) || ""; } catch (e) {}

    if (state.enabled && url.indexOf("/api/field/session/vision-analyze") !== -1) {
      state.blockedVisionAnalyzeCount += 1;
      return Promise.resolve(new Response(JSON.stringify({
        ok: true,
        status: "VISION_ANALYZE_BLOCKED_IN_REALTIME",
        reason: "YOLO_FIRST_RUNTIME_LOCK_ACTIVE",
        route_policy: "vision-analyze is validator/review only, not realtime core",
        blocked_count: state.blockedVisionAnalyzeCount,
        no_fake_detection: true,
        detections: []
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }));
    }

    return originalFetch(input, init);
  };

  function attachToExistingControls() {
    var candidates = Array.from(document.querySelectorAll("input,button,[role='switch']"));

    candidates.forEach(function (el) {
      if (el.dataset && el.dataset.progress627Bound === "1") return;

      var text = (
        (el.id || "") + " " +
        (el.name || "") + " " +
        (el.getAttribute("aria-label") || "") + " " +
        (el.textContent || "")
      ).toLowerCase();

      var looksLikeDetectionControl =
        text.indexOf("ai") >= 0 ||
        text.indexOf("detection") >= 0 ||
        text.indexOf("deteksi") >= 0 ||
        text.indexOf("yolo") >= 0 ||
        text.indexOf("vision") >= 0;

      if (!looksLikeDetectionControl) return;

      if (el.dataset) el.dataset.progress627Bound = "1";

      el.addEventListener("change", function () {
        if (el.checked === true) startLoop("existing_switch_change");
        else if (el.checked === false) stopLoop("existing_switch_change");
      });

      el.addEventListener("click", function () {
        if (el.tagName && el.tagName.toLowerCase() === "button") {
          if (state.enabled) stopLoop("existing_button_click");
          else startLoop("existing_button_click");
        }
      });
    });
  }


  // PROGRESS_6_27B_WARMUP_BEFORE_SWITCH
  async function warmupYoloFirstOnce() {
    var sid = sessionId();
    if (!sid || state.progress627WarmupDone === true) return;

    state.progress627WarmupDone = true;

    try {
      var c = document.createElement("canvas");
      c.width = 320;
      c.height = 240;
      var ctx = c.getContext("2d");
      ctx.fillStyle = "rgb(18,18,18)";
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.fillStyle = "rgb(80,110,80)";
      ctx.fillRect(120, 60, 80, 120);

      var dataUrl = c.toDataURL("image/jpeg", 0.65);

      await fetch("/api/field/session/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sid,
          frame_base64: dataUrl,
          image_base64: dataUrl,
          source: "PROGRESS_6_27B_WARMUP_BEFORE_SWITCH",
          realtime_mode: "YOLO_FIRST_WARMUP",
          synthetic_warmup: true,
          no_fake_detection: true,
          shutter_triggered: false
        })
      });

      try { console.log("[6.27B] YOLO warmup sent before realtime switch"); } catch (e) {}
    } catch (err) {
      try { console.warn("[6.27B] YOLO warmup failed", err); } catch (e) {}
    }
  }

  window.ULP_PROGRESS_6_27_YOLO_FIRST = {
    start: startLoop,
    stop: stopLoop,
    state: state,
    sendFrameOnce: sendFrameOnce,
    clearOverlay: clearOverlay
  };

  document.addEventListener("DOMContentLoaded", function () {
    ensureBadge();
    warmupYoloFirstOnce();
    attachToExistingControls();
    setInterval(attachToExistingControls, 1500);
    setBadge("YOLO-FIRST OFF", false);
  });
})();
