/* PROGRESS_6_24_REALTIME_VISION_FIELD_DETECTION_SWITCH */
/* Switch-controlled Vision API detection loop. Shutter remains documentation only. */

(function () {
  "use strict";

  const VERSION = "PROGRESS_6_24_REALTIME_VISION_FIELD_DETECTION_SWITCH";
  const VISION_ENDPOINT = "/api/field/session/vision-analyze";
  const FRAME_ENDPOINT = "/api/field/session/frame";
  const LOOP_INTERVAL_MS = 1000;
  const REQUEST_TIMEOUT_MS = 18000;
  const CLOUD_MIN_INTERVAL_MS = 5000;
  const JPEG_QUALITY = 0.66;
  const MAX_FRAME_WIDTH = 720;

  const COLOR = {
    struktur_penyangga: "rgba(76,166,255,0.98)",
    konduktor: "rgba(255,215,77,0.98)",
    pohon_sono_candidate: "rgba(36,245,143,0.98)",
    general_object: "rgba(226,232,238,0.88)",
    default: "rgba(226,232,238,0.88)"
  };

  const state = {
    running: false,
    pending: false,
    lastResult: null,
    lastError: "",
    lastRequestAt: 0,
    tickCount: 0,
    canvas: null,
    ctx: null,
    nativeFetch: window.fetch ? window.fetch.bind(window) : null,
    suppressLegacyFrame: true,
    suppressShutterVision: true
  };

  function q(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function compact(text, n) {
    text = String(text || "").replace(/\s+/g, " ").trim();
    return text.length > n ? text.slice(0, n - 1) + "…" : text;
  }

  function nowMs() {
    return Date.now ? Date.now() : new Date().getTime();
  }

  function getUrlFromFetchInput(input) {
    if (typeof input === "string") return input;
    if (input && typeof input.url === "string") return input.url;
    return "";
  }

  function getBodyText(init) {
    if (!init || init.body == null) return "";
    if (typeof init.body === "string") return init.body;
    try { return JSON.stringify(init.body); } catch (_) { return ""; }
  }

  function jsonResponse(obj, status) {
    return Promise.resolve(new Response(JSON.stringify(obj), {
      status: status || 200,
      headers: {"Content-Type": "application/json"}
    }));
  }

  function installFetchGuard() {
    if (!state.nativeFetch || window.__P624_FETCH_GUARD_INSTALLED__) return;
    window.__P624_FETCH_GUARD_INSTALLED__ = true;

    window.fetch = function (input, init) {
      const url = getUrlFromFetchInput(input);
      const body = getBodyText(init);

      if (state.suppressLegacyFrame && url.includes(FRAME_ENDPOINT)) {
        return jsonResponse({
          ok: true,
          status: "P624_LEGACY_FRAME_SUPPRESSED",
          reason: "Vision API switch runtime replaces legacy YOLO frame loop.",
          detections: [],
          no_fake_detection: true,
          no_fake_clearance: true
        }, 200);
      }

      if (state.suppressShutterVision && url.includes(VISION_ENDPOINT) && body.includes("shutter_after_save")) {
        return jsonResponse({
          ok: true,
          status: "P624_SHUTTER_VISION_SUPPRESSED",
          reason: "Shutter is documentation only. Realtime detection uses switch loop.",
          selected_provider: state.lastResult && state.lastResult.selected_provider || "none",
          selected_model: state.lastResult && state.lastResult.selected_model || "none",
          detections: state.lastResult && state.lastResult.detections || [],
          overlay_json: state.lastResult && state.lastResult.overlay_json || {"boxes": []},
          no_fake_detection: true,
          no_fake_clearance: true,
          clearance_status: "CLEARANCE_NOT_FINAL_MONO_SCALING_NOT_STARTED"
        }, 200);
      }

      
      if (url.includes("/api/field/session/shutter") && init && typeof init.body === "string") {
        try {
          const lastRaw = window.localStorage.getItem("P625_LAST_VISION_RESULT");
          if (lastRaw) {
            const bodyObj = JSON.parse(init.body);
            bodyObj.vision_result_cache = JSON.parse(lastRaw);
            bodyObj.vision_result_cache_status = "P625_ATTACHED_FRONTEND_CACHE";
            const nextInit = Object.assign({}, init, { body: JSON.stringify(bodyObj) });
            return state.nativeFetch(input, nextInit);
          }
        } catch (_) {}
      }

      return state.nativeFetch(input, init);
    };
  }

  function getSessionId() {
    const url = new URL(window.location.href);
    const fromQuery = url.searchParams.get("session_id");
    if (fromQuery) return fromQuery;

    const candidates = [
      window.FIELD_SESSION_ID,
      window.sessionId,
      window.currentSessionId,
      document.body && document.body.getAttribute("data-session-id"),
      document.documentElement.getAttribute("data-session-id")
    ].filter(Boolean);

    if (candidates.length) return String(candidates[0]);

    const text = document.body ? document.body.innerText || "" : "";
    const m = text.match(/FS_[0-9]{8}_[0-9]{6}_[a-zA-Z0-9]+/);
    return m ? m[0] : "";
  }

  function getPointId() {
    const el = q('input[name="point_id"], #point_id, #pointId, [data-field="point_id"]');
    if (el && el.value) return String(el.value).trim();

    const text = document.body ? document.body.innerText || "" : "";
    const m = text.match(/[PVK][0-9]{3}_[a-zA-Z0-9_]+/);
    return m ? m[0] : "V001_pohon_sono";
  }

  function findVideo() {
    const videos = qa("video").filter(function (v) {
      const r = v.getBoundingClientRect();
      return r.width > 120 && r.height > 120;
    });
    return videos[0] || q("video");
  }

  function ensureCanvas() {
    const video = findVideo();
    if (!video) return null;

    if (!state.canvas) {
      const canvas = document.createElement("canvas");
      canvas.id = "p624VisionCanvas";
      canvas.setAttribute("data-progress6-24", "realtime-colored-vision-boxes");
      document.body.appendChild(canvas);
      state.canvas = canvas;
      state.ctx = canvas.getContext("2d");
    }

    const r = video.getBoundingClientRect();
    const dpr = Math.max(1, Math.min(3, window.devicePixelRatio || 1));

    state.canvas.style.left = r.left + "px";
    state.canvas.style.top = r.top + "px";
    state.canvas.style.width = r.width + "px";
    state.canvas.style.height = r.height + "px";

    const w = Math.max(1, Math.round(r.width * dpr));
    const h = Math.max(1, Math.round(r.height * dpr));

    if (state.canvas.width !== w || state.canvas.height !== h) {
      state.canvas.width = w;
      state.canvas.height = h;
    }

    if (state.ctx) {
      state.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    return { video: video, rect: r };
  }

  function clearCanvas() {
    if (!state.canvas || !state.ctx) return;
    const r = state.canvas.getBoundingClientRect();
    state.ctx.clearRect(0, 0, r.width, r.height);
  }

  function ensureHud() {
    if (q("#p624IconHud")) return;

    const hud = document.createElement("div");
    hud.id = "p624IconHud";
    hud.innerHTML = [
      '<div class="p624-status-icons">',
      '<span id="p624CamDot" class="p624-dot off" title="Camera">◉</span>',
      '<span id="p624GpsDot" class="p624-dot off" title="GPS">⌖</span>',
      '<span id="p624AiDot" class="p624-dot off" title="Vision AI">◈</span>',
      '<span id="p624RiskDot" class="p624-dot off" title="Prediction">△</span>',
      '</div>',
      '<div id="p624SwitchWrap" class="p624-off" role="button" aria-label="Toggle realtime vision detection">',
      '<span id="p624SwitchLabel">AI DETECTION</span>',
      '<div id="p624SwitchButton"><div id="p624SwitchKnob"></div></div>',
      '</div>'
    ].join("");
    document.body.appendChild(hud);

    const prediction = document.createElement("div");
    prediction.id = "p624PredictionPanel";
    prediction.className = "off";
    prediction.innerHTML = [
      '<div id="p624PredictionIcon">△</div>',
      '<div id="p624PredictionText">AI detection OFF. Shutter hanya untuk dokumentasi evidence.</div>'
    ].join("");
    document.body.appendChild(prediction);

    const legend = document.createElement("div");
    legend.id = "p624Legend";
    legend.innerHTML = [
      '<span class="p624-legend-item p624-blue" title="struktur_penyangga"></span>',
      '<span class="p624-legend-item p624-yellow" title="konduktor"></span>',
      '<span class="p624-legend-item p624-green" title="pohon_sono_candidate"></span>',
      '<span class="p624-legend-item p624-gray" title="general_object"></span>'
    ].join("");
    document.body.appendChild(legend);

    q("#p624SwitchWrap").addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      setRunning(!state.running);
    });
  }

  function setDot(id, mode, title) {
    const el = q("#" + id);
    if (!el) return;
    el.className = "p624-dot " + (mode || "off");
    if (title) el.title = title;
  }

  function setPrediction(mode, icon, text) {
    const panel = q("#p624PredictionPanel");
    const iconEl = q("#p624PredictionIcon");
    const textEl = q("#p624PredictionText");
    if (panel) panel.className = mode || "off";
    if (iconEl) iconEl.textContent = icon || "△";
    if (textEl) textEl.textContent = compact(text || "", 210);
  }

  function updateStatusDots() {
    const video = findVideo();
    const bodyText = document.body ? document.body.innerText || "" : "";

    if (video && video.readyState >= 2) {
      setDot("p624CamDot", "ok", "Camera ready");
    } else {
      setDot("p624CamDot", "off", "Camera waiting");
    }

    if (bodyText.includes("GPS_READY")) {
      setDot("p624GpsDot", "ok", "GPS ready");
    } else if (bodyText.includes("GPS_TIMEOUT") || bodyText.includes("GPS_EVIDENCE_ONLY")) {
      setDot("p624GpsDot", "busy", "GPS evidence only / waiting");
    } else {
      setDot("p624GpsDot", "off", "GPS waiting");
    }

    if (state.pending) {
      setDot("p624AiDot", "busy", "Vision API request running");
    } else if (state.running) {
      setDot("p624AiDot", "ok", "Realtime Vision ON");
    } else if (state.lastError) {
      setDot("p624AiDot", "err", state.lastError);
    } else {
      setDot("p624AiDot", "off", "Realtime Vision OFF");
    }
  }

  function setRunning(value) {
    state.running = !!value;
    const sw = q("#p624SwitchWrap");
    if (sw) {
      sw.classList.toggle("p624-on", state.running);
      sw.classList.toggle("p624-off", !state.running);
    }

    if (state.running) {
      setPrediction("busy", "◈", "AI detection ON. Sistem membaca frame setiap 1 detik, latest-only, tanpa menekan Shutter.");
      runVisionTick("switch_on_immediate");
    } else {
      setPrediction("off", "△", "AI detection OFF. Bounding box terakhir tetap ditampilkan; Shutter hanya dokumentasi evidence.");
      setDot("p624AiDot", "off", "Realtime Vision OFF");
    }
  }

  function getDetections(result) {
    if (!result) return [];

    if (result.overlay_json && Array.isArray(result.overlay_json.boxes)) {
      return result.overlay_json.boxes.map(function (b) {
        return {
          label: b.label || b.class_name || b.object_group || "object",
          object_group: b.object_group || b.group || b.class_name || "general_object",
          box_2d: b.box_2d || b.bbox_norm_yxyx_1000 || b.bbox || b.box,
          confidence: b.confidence
        };
      });
    }

    if (Array.isArray(result.detections)) return result.detections;
    return [];
  }

  function normalizeGroup(group, label) {
    const g = String(group || "").toLowerCase();
    const l = String(label || "").toLowerCase();

    if (g.includes("struktur") || g.includes("pole") || l.includes("tiang") || l.includes("pole")) return "struktur_penyangga";
    if (g.includes("konduktor") || g.includes("conductor") || l.includes("kabel listrik") || l.includes("overhead")) return "konduktor";
    if (g.includes("pohon") || g.includes("tree") || g.includes("vegetation") || l.includes("pohon") || l.includes("daun") || l.includes("vegetasi")) return "pohon_sono_candidate";
    return "general_object";
  }

  function normalizeBox(det, width, height) {
    let box = det.box_2d || det.bbox_norm_yxyx_1000 || det.bbox || det.box || null;
    if (!Array.isArray(box) || box.length < 4) return null;

    let y1 = Number(box[0]);
    let x1 = Number(box[1]);
    let y2 = Number(box[2]);
    let x2 = Number(box[3]);

    if (![x1, y1, x2, y2].every(Number.isFinite)) return null;

    x1 = Math.max(0, Math.min(width, x1 / 1000 * width));
    x2 = Math.max(0, Math.min(width, x2 / 1000 * width));
    y1 = Math.max(0, Math.min(height, y1 / 1000 * height));
    y2 = Math.max(0, Math.min(height, y2 / 1000 * height));

    if (x2 < x1) [x1, x2] = [x2, x1];
    if (y2 < y1) [y1, y2] = [y2, y1];

    if ((x2 - x1) < 5 || (y2 - y1) < 5) return null;
    return { x1: x1, y1: y1, x2: x2, y2: y2, w: x2 - x1, h: y2 - y1 };
  }

  function drawResult(result) {
    const info = ensureCanvas();
    if (!info || !state.ctx) return;

    const ctx = state.ctx;
    const rect = info.rect;
    clearCanvas();

    const detections = getDetections(result);
    let drawn = 0;

    ctx.save();
    ctx.lineJoin = "round";
    ctx.lineCap = "round";

    detections.forEach(function (det) {
      const group = normalizeGroup(det.object_group || det.group, det.label);
      const box = normalizeBox(det, rect.width, rect.height);
      if (!box) return;

      const color = COLOR[group] || COLOR.default;
      const labelBase = det.label || group;
      const conf = det.confidence != null && Number.isFinite(Number(det.confidence)) ? " " + Number(det.confidence).toFixed(2) : "";
      const label = compact(labelBase + conf, 32);

      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(2.6, Math.min(5.5, rect.width / 150));
      ctx.shadowColor = color;
      ctx.shadowBlur = 10;
      ctx.strokeRect(box.x1, box.y1, box.w, box.h);
      ctx.shadowBlur = 0;

      ctx.font = "900 13px system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
      const tw = Math.min(rect.width - 10, ctx.measureText(label).width + 16);
      const th = 22;
      const lx = Math.max(4, Math.min(box.x1, rect.width - tw - 4));
      const ly = Math.max(4, box.y1 - th - 2);

      ctx.fillStyle = "rgba(0, 20, 15, .82)";
      ctx.fillRect(lx, ly, tw, th);
      ctx.fillStyle = color;
      ctx.fillText(label, lx + 8, ly + 15);

      drawn += 1;
    });

    ctx.restore();

    updatePrediction(result, detections, drawn);
  }

  function updatePrediction(result, detections, drawn) {
    let hasTree = false;
    let hasPole = false;
    let hasConductor = false;
    let hasGeneral = false;

    detections.forEach(function (det) {
      const group = normalizeGroup(det.object_group || det.group, det.label);
      if (group === "pohon_sono_candidate") hasTree = true;
      else if (group === "struktur_penyangga") hasPole = true;
      else if (group === "konduktor") hasConductor = true;
      else hasGeneral = true;
    });

    if (result && result.tree_detected === true) hasTree = true;
    if (result && result.pole_detected === true) hasPole = true;
    if (result && result.conductor_detected === true) hasConductor = true;

    const provider = result && (result.selected_provider || result.provider) || "vision";
    const model = result && (result.selected_model || result.model) || "api";

    if (!state.running) {
      setDot("p624RiskDot", "off", "Prediction inactive");
      return;
    }

    if (state.pending) {
      setDot("p624RiskDot", "busy", "Prediction updating");
    }

    if (hasTree && (hasConductor || hasPole)) {
      setDot("p624RiskDot", "busy", "Pantau kandidat vegetasi dekat jaringan");
      setPrediction(
        "warn",
        "!",
        "PANTAU: kandidat vegetasi + referensi jaringan terdeteksi. Clearance belum final; monocular scaling/kalibrasi tetap diperlukan. " + provider + " | " + model
      );
      return;
    }

    if (hasTree && !hasConductor && !hasPole) {
      setDot("p624RiskDot", "busy", "Vegetasi terlihat, referensi jaringan belum cukup");
      setPrediction(
        "warn",
        "△",
        "VEGETASI TERLIHAT: pohon/vegetasi terdeteksi, tetapi konduktor/struktur penyangga belum cukup terlihat. Status evidence, bukan clearance final."
      );
      return;
    }

    if (!hasTree && (hasConductor || hasPole)) {
      setDot("p624RiskDot", "ok", "Aman visual sementara");
      setPrediction(
        "ok",
        "✓",
        "AMAN VISUAL SEMENTARA: referensi jaringan terlihat tanpa kandidat vegetasi pada frame ini. Tetap evidence sementara, bukan hasil clearance final."
      );
      return;
    }

    if (drawn > 0 && hasGeneral) {
      setDot("p624RiskDot", "ok", "General object only");
      setPrediction(
        "ok",
        "□",
        "GENERAL OBJECT: objek non-PLN terdeteksi. Sistem tidak menganggapnya sebagai pohon_sono/konduktor/struktur penyangga."
      );
      return;
    }

    setDot("p624RiskDot", "off", "No detection");
    setPrediction(
      "off",
      "△",
      "BELUM ADA KANDIDAT: belum ada objek inspeksi yang cukup pada frame ini."
    );
  }

  function captureFrameBase64(video) {
    return new Promise(function (resolve, reject) {
      try {
        if (!video) return reject(new Error("NO_VIDEO_ELEMENT"));

        const srcW = video.videoWidth || video.clientWidth || 720;
        const srcH = video.videoHeight || video.clientHeight || 1280;

        if (!srcW || !srcH) return reject(new Error("VIDEO_DIMENSION_NOT_READY"));

        const scale = Math.min(1, MAX_FRAME_WIDTH / srcW);
        const dstW = Math.max(1, Math.round(srcW * scale));
        const dstH = Math.max(1, Math.round(srcH * scale));

        const canvas = document.createElement("canvas");
        canvas.width = dstW;
        canvas.height = dstH;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, dstW, dstH);

        canvas.toBlob(function (blob) {
          if (!blob) {
            try {
              const fallback = canvas.toDataURL("image/jpeg", JPEG_QUALITY);
              return resolve(fallback.split(",")[1]);
            } catch (e) {
              return reject(e);
            }
          }

          const reader = new FileReader();
          reader.onload = function () {
            const dataUrl = String(reader.result || "");
            resolve(dataUrl.split(",")[1] || dataUrl);
          };
          reader.onerror = function () {
            reject(new Error("FRAME_BLOB_READ_FAILED"));
          };
          reader.readAsDataURL(blob);
        }, "image/jpeg", JPEG_QUALITY);
      } catch (err) {
        reject(err);
      }
    });
  }

  async function parseJsonResponse(resp) {
    const contentType = (resp.headers.get("content-type") || "").toLowerCase();
    const text = await resp.text();

    if (!contentType.includes("application/json")) {
      throw new Error("VISION_NON_JSON_" + text.slice(0, 60).replace(/\s+/g, "_"));
    }

    return JSON.parse(text);
  }

  async function callVisionApi(imageBase64, reason) {
    if (!state.nativeFetch) throw new Error("FETCH_NOT_AVAILABLE");

    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    const timer = controller ? window.setTimeout(function () {
      try { controller.abort("P625_VISION_CLOUD_TIMEOUT_AFTER_18S"); } catch (_) {}
    }, REQUEST_TIMEOUT_MS) : null;

    const payload = {
      session_id: getSessionId(),
      point_id: getPointId(),
      image_base64: imageBase64,
      frontend_version: VERSION,
      reason: reason || "realtime_switch_tick",
      mode: "REALTIME_SWITCH_1FPS_LATEST_ONLY",
      no_fake_detection: true,
      no_fake_clearance: true
    };

    try {
      const resp = await state.nativeFetch(VISION_ENDPOINT, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
        cache: "no-store",
        signal: controller ? controller.signal : undefined
      });

      const data = await parseJsonResponse(resp);

      if (!resp.ok || data.ok === false) {
        throw new Error(data.error || data.status || ("VISION_HTTP_" + resp.status));
      }

      return data;
    } finally {
      if (timer) window.clearTimeout(timer);
    }
  }

  async function runVisionTick(reason) {
    if (!state.running) return;
    if (state.pending) return;

    const elapsed = nowMs() - state.lastRequestAt;
    if (elapsed < CLOUD_MIN_INTERVAL_MS - 50) return;

    const video = findVideo();
    if (!video || video.readyState < 2) {
      setPrediction("err", "×", "Camera belum siap. Vision loop menunggu stream kamera.");
      setDot("p624CamDot", "err", "Camera not ready");
      return;
    }

    const sessionId = getSessionId();
    if (!sessionId) {
      setPrediction("err", "×", "Session ID kosong. Kembali ke /field-capture lalu Start ulang.");
      setDot("p624AiDot", "err", "Session ID empty");
      return;
    }

    state.pending = true;
    state.lastRequestAt = nowMs();
    state.tickCount += 1;

    updateStatusDots();
    setPrediction("busy", "◈", "AI membaca frame realtime... tick " + state.tickCount + " | cloud latest-only");

    try {
      const imageBase64 = await captureFrameBase64(video);
      const result = await callVisionApi(imageBase64, reason || "realtime_switch_tick");

      state.lastResult = result;
      state.lastError = "";

      drawResult(result);

      const provider = result.selected_provider || result.provider || "vision";
      const model = result.selected_model || result.model || "api";
      setDot("p624AiDot", "ok", "Vision OK: " + provider + " " + model);

      
      window.PROGRESS_6_24_LAST_REALTIME_VISION_RESULT = result;
      try {
        window.localStorage.setItem("P625_LAST_VISION_RESULT", JSON.stringify({
          saved_at: new Date().toISOString(),
          session_id: getSessionId(),
          point_id: getPointId(),
          result: result
        }));
      } catch (_) {}
    } catch (err) {
      
      const rawError = err && err.message ? err.message : String(err);
      if (rawError === "signal is aborted without reason" || rawError.includes("aborted without reason")) {
        state.lastError = "VISION_TIMEOUT_CLIENT_ABORT_PREVENTED_BY_P625_RELOAD_REQUIRED";
      } else if (rawError.includes("P625_VISION_CLOUD_TIMEOUT_AFTER_18S")) {
        state.lastError = "VISION_CLOUD_TIMEOUT_AFTER_18S";
      } else {
        state.lastError = rawError;
      }
      setDot("p624AiDot", "err", state.lastError);
      setPrediction("err", "×", "Vision API error: " + state.lastError + ". Last result tetap dipertahankan jika ada.");
      if (state.lastResult) drawResult(state.lastResult);
    } finally {
      state.pending = false;
      updateStatusDots();
    }
  }

  function installLoop() {
    window.setInterval(function () {
      document.body.classList.add("p624-realtime-vision-mode");
      ensureHud();
      ensureCanvas();
      updateStatusDots();

      if (state.lastResult) drawResult(state.lastResult);

      if (state.running) {
        runVisionTick("interval_1s");
      }
    }, LOOP_INTERVAL_MS);

    window.addEventListener("resize", function () {
      ensureCanvas();
      if (state.lastResult) drawResult(state.lastResult);
    });

    window.addEventListener("orientationchange", function () {
      window.setTimeout(function () {
        ensureCanvas();
        if (state.lastResult) drawResult(state.lastResult);
      }, 700);
    });
  }

  function install() {
    document.documentElement.setAttribute("data-progress6-24-realtime-vision-switch", "ready");
    document.body.classList.add("p624-realtime-vision-mode");

    installFetchGuard();
    ensureHud();
    ensureCanvas();
    updateStatusDots();
    installLoop();

    window.PROGRESS_6_24_REALTIME_VISION_SWITCH = {
      version: VERSION,
      status: "READY",
      loop_interval_ms: LOOP_INTERVAL_MS,
      request_timeout_ms: REQUEST_TIMEOUT_MS,
      cloud_min_interval_ms: CLOUD_MIN_INTERVAL_MS,
      patch_6_25: "ABORT_FIX_CLOUD_SAFE",
      setRunning: setRunning,
      runVisionTick: runVisionTick,
      note: "Switch-controlled realtime Vision API. Shutter documentation only."
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }
})();
