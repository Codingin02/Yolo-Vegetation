(function () {
  "use strict";

  if (window.__PROGRESS626_YOLO_FIRST_ACTIVE__) return;
  window.__PROGRESS626_YOLO_FIRST_ACTIVE__ = true;
  window.PROGRESS626_ALLOW_CLOUD_REVIEW = false;
  window.PROGRESS626_LAST_YOLO_RESULT = null;

  const FRAME_ENDPOINT = "/api/field/session/frame";
  const VISION_ENDPOINT = "/api/field/session/vision-analyze";
  const LOOP_INTERVAL_MS = 1000;
  const JPEG_QUALITY = 0.72;
  const MAX_CAPTURE_WIDTH = 640;

  const state = {
    running: false,
    pending: false,
    abortController: null,
    loopTimer: null,
    tick: 0,
    sessionId: new URLSearchParams(window.location.search).get("session_id") || "",
    lastResult: null,
    lastFrameDataUrl: null,
    lastFrameTs: null,
  };

  const classColor = {
    pohon_sono: "#35e37a",
    konduktor: "#ffbd32",
    struktur_penyangga: "#43a8ff",
  };

  const originalFetch = window.fetch ? window.fetch.bind(window) : null;

  if (originalFetch) {
    window.fetch = function patchedProgress626Fetch(input, init) {
      const url = typeof input === "string" ? input : (input && input.url ? input.url : "");
      if (url && url.includes(VISION_ENDPOINT) && !window.PROGRESS626_ALLOW_CLOUD_REVIEW) {
        return Promise.resolve(new Response(JSON.stringify({
          ok: true,
          status: "CLOUD_VISION_BLOCKED_AS_CORE_LOOP_BY_PROGRESS_6_26",
          message: "Vision API cloud tidak dipakai sebagai core realtime. Gunakan YOLO lokal via /api/field/session/frame.",
          detections: [],
          no_fake_detection: true
        }), {
          status: 200,
          headers: {"Content-Type": "application/json"}
        }));
      }
      return originalFetch(input, init);
    };
  }

  function ensureCanvas() {
    let canvas = document.getElementById("progress626YoloCanvas");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "progress626YoloCanvas";
      canvas.className = "progress626-yolo-canvas";
      document.body.appendChild(canvas);
    }
    return canvas;
  }

  function ensurePredictionPanel() {
    let panel = document.getElementById("progress626PredictionPanel");
    if (!panel) {
      panel = document.createElement("section");
      panel.id = "progress626PredictionPanel";
      panel.className = "progress626-prediction-panel";
      panel.innerHTML = [
        '<div class="p626-title">Realtime Prediction</div>',
        '<div class="p626-row"><span>Object</span><b id="p626Object">-</b></div>',
        '<div class="p626-row"><span>Clearance</span><b id="p626Clearance">NOT_FINAL</b></div>',
        '<div class="p626-row"><span>ETA</span><b id="p626Eta">INSUFFICIENT</b></div>',
        '<div class="p626-row"><span>Risk</span><b id="p626Risk">EVIDENCE_ONLY</b></div>',
        '<div class="p626-row"><span>Source</span><b id="p626Source">YOLO_LOCAL</b></div>',
        '<div class="p626-limit" id="p626Limit">No fake clearance. No final pruning decision.</div>'
      ].join("");
      document.body.appendChild(panel);
    }
    return panel;
  }

  function ensureIconHud() {
    let hud = document.getElementById("progress626IconHud");
    if (!hud) {
      hud = document.createElement("div");
      hud.id = "progress626IconHud";
      hud.className = "progress626-icon-hud";
      hud.innerHTML = [
        '<span class="p626-icon amber" id="p626CamIcon" title="Camera">C</span>',
        '<span class="p626-icon amber" id="p626GpsIcon" title="GPS">G</span>',
        '<span class="p626-icon gray" id="p626YoloIcon" title="YOLO">Y</span>',
        '<span class="p626-icon gray" id="p626ModelIcon" title="Model">M</span>',
        '<span class="p626-icon gray" id="p626ShutterIcon" title="Shutter">S</span>'
      ].join("");
      document.body.appendChild(hud);
    }
    return hud;
  }

  function ensureSwitch() {
    let box = document.getElementById("progress626SwitchBox");
    if (!box) {
      box = document.createElement("div");
      box.id = "progress626SwitchBox";
      box.className = "progress626-switch-box";
      box.innerHTML = [
        '<span class="p626-switch-label">YOLO</span>',
        '<button type="button" id="progress626SwitchButton" class="progress626-switch-button" aria-pressed="false">',
        '<span></span>',
        '</button>'
      ].join("");
      document.body.appendChild(box);
    }
    const btn = document.getElementById("progress626SwitchButton");
    if (btn && !btn.dataset.p626Bound) {
      btn.dataset.p626Bound = "1";
      btn.addEventListener("click", function () {
        if (state.running) stopRealtime();
        else startRealtime();
      });
    }

    const oldSwitches = Array.from(document.querySelectorAll('input[type="checkbox"], button'));
    oldSwitches.forEach((el) => {
      const txt = ((el.id || "") + " " + (el.className || "") + " " + (el.textContent || "")).toLowerCase();
      if (txt.includes("ai") || txt.includes("detection") || txt.includes("vision")) {
        if (!el.dataset.p626BoundOld) {
          el.dataset.p626BoundOld = "1";
          el.addEventListener("click", function (ev) {
            setTimeout(() => {
              const isOn = el.checked === true || el.getAttribute("aria-pressed") === "true" || el.classList.contains("active");
              if (isOn && !state.running) startRealtime();
              if (!isOn && state.running) stopRealtime();
            }, 60);
          }, true);
        }
      }
    });
  }

  function setIcon(id, status) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("green", "amber", "red", "gray");
    el.classList.add(status || "gray");
  }

  function updateSwitchVisual() {
    const btn = document.getElementById("progress626SwitchButton");
    if (!btn) return;
    btn.setAttribute("aria-pressed", state.running ? "true" : "false");
    btn.classList.toggle("on", state.running);
  }

  function findVideo() {
    const videos = Array.from(document.querySelectorAll("video"));
    return videos.find(v => v.readyState >= 2 && v.videoWidth > 0 && v.videoHeight > 0) || videos[0] || null;
  }

  function resizeCanvasToVideo(canvas, video) {
    const rect = video.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = Math.max(1, Math.round(rect.width * dpr));
    const h = Math.max(1, Math.round(rect.height * dpr));
    if (canvas.width !== w) canvas.width = w;
    if (canvas.height !== h) canvas.height = h;
    canvas.style.left = rect.left + "px";
    canvas.style.top = rect.top + "px";
    canvas.style.width = rect.width + "px";
    canvas.style.height = rect.height + "px";
    canvas.dataset.dpr = String(dpr);
  }

  function clearOverlay() {
    const canvas = ensureCanvas();
    const ctx = canvas.getContext("2d");
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    window.PROGRESS626_LAST_YOLO_RESULT = null;
  }

  function captureFrame(video) {
    const sourceW = video.videoWidth || 640;
    const sourceH = video.videoHeight || 480;
    const scale = Math.min(1, MAX_CAPTURE_WIDTH / sourceW);
    const w = Math.max(1, Math.round(sourceW * scale));
    const h = Math.max(1, Math.round(sourceH * scale));
    const c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    const ctx = c.getContext("2d", { willReadFrequently: false });
    ctx.drawImage(video, 0, 0, w, h);
    const dataUrl = c.toDataURL("image/jpeg", JPEG_QUALITY);
    state.lastFrameDataUrl = dataUrl;
    state.lastFrameTs = new Date().toISOString();
    return dataUrl;
  }

  function drawDetections(result) {
    const video = findVideo();
    const canvas = ensureCanvas();
    if (!video) return;

    resizeCanvasToVideo(canvas, video);
    const ctx = canvas.getContext("2d");
    const dpr = Number(canvas.dataset.dpr || "1");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const detections = Array.isArray(result.detections) ? result.detections : [];
    detections.forEach((det) => {
      const cls = det.class_name || det.object_group || "unknown";
      if (!["pohon_sono", "konduktor", "struktur_penyangga"].includes(cls)) return;

      let y1, x1, y2, x2;
      if (Array.isArray(det.bbox_norm_yxyx_1000) && det.bbox_norm_yxyx_1000.length === 4) {
        y1 = det.bbox_norm_yxyx_1000[0] / 1000 * canvas.height;
        x1 = det.bbox_norm_yxyx_1000[1] / 1000 * canvas.width;
        y2 = det.bbox_norm_yxyx_1000[2] / 1000 * canvas.height;
        x2 = det.bbox_norm_yxyx_1000[3] / 1000 * canvas.width;
      } else {
        return;
      }

      const color = classColor[cls] || "#b0b0b0";
      const conf = typeof det.confidence === "number" ? det.confidence.toFixed(2) : "-";
      const label = cls + " " + conf + (det.track_id ? " T" + det.track_id : "");

      ctx.save();
      ctx.lineWidth = Math.max(2, 2.5 * dpr);
      ctx.strokeStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 10 * dpr;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

      ctx.shadowBlur = 0;
      ctx.font = `${Math.max(12, 12 * dpr)}px system-ui, -apple-system, Segoe UI, sans-serif`;
      const textW = ctx.measureText(label).width + 12 * dpr;
      const textH = 20 * dpr;
      ctx.fillStyle = "rgba(20, 34, 31, 0.82)";
      ctx.fillRect(x1, Math.max(0, y1 - textH), textW, textH);
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, x1 + 6 * dpr, Math.max(14 * dpr, y1 - 6 * dpr));
      ctx.restore();
    });
  }

  function updatePredictionPanel(result) {
    ensurePredictionPanel();
    const detections = Array.isArray(result.detections) ? result.detections : [];
    const prediction = result.prediction || {};
    const classes = detections.map(d => d.class_name || d.object_group).filter(Boolean);
    const objectText = classes.length ? Array.from(new Set(classes)).join(", ") : "belum cukup";
    const clearanceText = prediction.clearance_status || "NOT_FINAL";
    const etaText = prediction.eta_days !== undefined && prediction.eta_days !== null ? (prediction.eta_days + " hari") : (prediction.eta_status || "INSUFFICIENT");
    const riskText = prediction.risk_status || "EVIDENCE_ONLY";
    const sourceText = result.runtime_mode || "YOLO_FIRST";
    const limitText = Array.isArray(prediction.limitations) ? prediction.limitations.join(" | ") : (prediction.display_summary || "No final claim.");

    const set = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = String(value);
    };
    set("p626Object", objectText);
    set("p626Clearance", clearanceText);
    set("p626Eta", etaText);
    set("p626Risk", riskText);
    set("p626Source", sourceText);
    set("p626Limit", limitText);
  }

  function hideLegacyTextChips() {
    const badTokens = [
      "GPS_TIMEOUT",
      "CAMERA_STREAM_READY",
      "P624_LEGACY_FRAME",
      "SHUTTER_WAITING",
      "TREE_MODEL_READY_CANDIDATE",
      "MODEL_NOT_READY",
      "YOLO_STILL_RUNNING",
      "GPS_EVIDENCE_ONLY",
      "CLEARANCE_NOT_FINAL",
      "FRAME_WAITING"
    ];
    const nodes = Array.from(document.querySelectorAll("span, div, p, small, b"));
    nodes.forEach((el) => {
      const txt = (el.textContent || "").trim();
      if (!txt || txt.length > 80) return;
      if (badTokens.some(t => txt.includes(t))) {
        el.dataset.p626HiddenChip = "1";
      }
    });
  }

  async function tickRealtime() {
    if (!state.running || state.pending) return;

    const video = findVideo();
    if (!video || video.readyState < 2) {
      setIcon("p626CamIcon", "amber");
      return;
    }

    if (!state.sessionId) {
      state.sessionId = new URLSearchParams(window.location.search).get("session_id") || "";
    }

    state.pending = true;
    state.tick += 1;
    setIcon("p626CamIcon", "green");
    setIcon("p626YoloIcon", "amber");

    try {
      if (state.abortController) {
        try { state.abortController.abort("P626_LATEST_ONLY_ABORT_OLD_FRAME"); } catch (_) {}
      }
      state.abortController = new AbortController();

      const dataUrl = captureFrame(video);
      const payload = {
        session_id: state.sessionId,
        point_id: window.PROGRESS626_POINT_ID || "V001_pohon_sono",
        image_base64: dataUrl,
        frame_ts: new Date().toISOString(),
        mode: "YOLO_FIRST_REALTIME",
        ai_switch_on: true
      };

      const res = await fetch(FRAME_ENDPOINT, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
        signal: state.abortController.signal
      });

      const data = await res.json();
      state.lastResult = data;
      window.PROGRESS626_LAST_YOLO_RESULT = data;

      drawDetections(data);
      updatePredictionPanel(data);

      const models = data.models || {};
      setIcon("p626YoloIcon", data.ok ? "green" : "red");
      setIcon("p626ModelIcon", models.tree === "TREE_MODEL_READY_CANDIDATE" || models.multiclass === "MULTICLASS_MODEL_READY_CANDIDATE" ? "amber" : "gray");
      setIcon("p626GpsIcon", "amber");
    } catch (err) {
      if (state.running) {
        setIcon("p626YoloIcon", "red");
      }
    } finally {
      state.pending = false;
      hideLegacyTextChips();
    }
  }

  function startRealtime() {
    state.running = true;
    updateSwitchVisual();
    ensureCanvas();
    ensurePredictionPanel();
    ensureIconHud();
    clearOverlay();

    if (state.loopTimer) clearInterval(state.loopTimer);
    tickRealtime();
    state.loopTimer = setInterval(tickRealtime, LOOP_INTERVAL_MS);
  }

  function stopRealtime() {
    state.running = false;
    updateSwitchVisual();

    if (state.loopTimer) {
      clearInterval(state.loopTimer);
      state.loopTimer = null;
    }

    if (state.abortController) {
      try { state.abortController.abort("P626_SWITCH_OFF"); } catch (_) {}
      state.abortController = null;
    }

    clearOverlay();
    setIcon("p626YoloIcon", "gray");

    if (state.sessionId) {
      fetch(FRAME_ENDPOINT, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          session_id: state.sessionId,
          ai_switch_on: false,
          mode: "YOLO_FIRST_REALTIME_OFF"
        })
      }).catch(() => {});
    }

    const limit = document.getElementById("p626Limit");
    if (limit) limit.textContent = "Realtime OFF. Overlay dibersihkan. Shutter tetap hanya evidence.";
  }

  function hookShutterEvidenceOnly() {
    const candidates = Array.from(document.querySelectorAll("button, a, div"));
    candidates.forEach((el) => {
      const txt = ((el.id || "") + " " + (el.className || "") + " " + (el.textContent || "")).toLowerCase();
      if (!txt.includes("shutter")) return;
      if (el.dataset.p626ShutterBound) return;
      el.dataset.p626ShutterBound = "1";
      el.addEventListener("click", function () {
        setIcon("p626ShutterIcon", "amber");
        window.PROGRESS626_SHUTTER_EVIDENCE = {
          last_yolo_result: state.lastResult,
          last_frame_ts: state.lastFrameTs,
          note: "Shutter is evidence only. Detection core is /api/field/session/frame."
        };
        setTimeout(() => setIcon("p626ShutterIcon", "green"), 1200);
      }, true);
    });
  }

  function init() {
    document.documentElement.classList.add("progress6-26-yolo-first");
    ensureCanvas();
    ensurePredictionPanel();
    ensureIconHud();
    ensureSwitch();
    hookShutterEvidenceOnly();
    hideLegacyTextChips();
    updateSwitchVisual();

    setInterval(function () {
      ensureSwitch();
      hookShutterEvidenceOnly();
      hideLegacyTextChips();
    }, 1500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.PROGRESS626_START_YOLO = startRealtime;
  window.PROGRESS626_STOP_YOLO = stopRealtime;
})();
