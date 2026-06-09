/* PROGRESS_6_22_FRONTEND_VISION_OVERLAY */
(function () {
  "use strict";

  const VERSION = "PROGRESS_6_22_FRONTEND_VISION_OVERLAY";
  const ENDPOINT = "/api/field/session/vision-analyze";

  const state = {
    busy: false,
    lastResult: null,
    canvas: null,
    ctx: null,
    hud: null,
    summary: null,
    fab: null,
    lastSessionId: "",
    drawTimer: null
  };

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function compact(s, n) {
    s = String(s || "").replace(/\s+/g, " ").trim();
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  function getSessionId() {
    const url = new URL(window.location.href);
    let sid = url.searchParams.get("session_id") || "";
    if (sid) return sid;

    const candidates = [
      window.FIELD_SESSION_ID,
      window.sessionId,
      window.currentSessionId,
      document.body.getAttribute("data-session-id"),
      document.documentElement.getAttribute("data-session-id")
    ].filter(Boolean);

    if (candidates.length) return String(candidates[0]);

    const text = document.body ? document.body.innerText || "" : "";
    const m = text.match(/FS_[0-9]{8}_[0-9]{6}_[a-zA-Z0-9]+/);
    return m ? m[0] : "";
  }

  function getPointId() {
    const el = qs('input[name="point_id"], #point_id, #pointId, [data-field="point_id"]');
    if (el && el.value) return String(el.value).trim();
    const text = document.body ? document.body.innerText || "" : "";
    const m = text.match(/[PVK][0-9]{3}_[a-zA-Z0-9_]+/);
    return m ? m[0] : "V001_pohon_sono";
  }

  function findVideo() {
    const videos = qsa("video").filter(v => {
      const r = v.getBoundingClientRect();
      return r.width > 80 && r.height > 80;
    });
    return videos[0] || qs("video");
  }

  function ensureHud() {
    if (state.hud) return state.hud;

    const hud = document.createElement("div");
    hud.id = "p622VisionHud";
    hud.innerHTML = [
      '<span id="p622ChipVision" class="p622-pill muted">VISION_READY</span>',
      '<span id="p622ChipGps" class="p622-pill muted">GPS_EVIDENCE_ONLY</span>',
      '<span id="p622ChipClearance" class="p622-pill muted">CLEARANCE_NOT_FINAL</span>'
    ].join("");
    document.body.appendChild(hud);

    const summary = document.createElement("div");
    summary.id = "p622VisionSummary";
    summary.textContent = "";
    document.body.appendChild(summary);

    const fab = document.createElement("button");
    fab.id = "p622VisionFab";
    fab.type = "button";
    fab.textContent = "Vision";
    fab.title = "Analyze current frame with Vision API";
    fab.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      runVisionAnalyze("manual_button");
    });
    document.body.appendChild(fab);

    state.hud = hud;
    state.summary = summary;
    state.fab = fab;
    return hud;
  }

  function setChip(id, text, mode) {
    ensureHud();
    const el = qs("#" + id);
    if (!el) return;
    el.textContent = compact(text, 34);
    el.className = "p622-pill " + (mode || "muted");
  }

  function hideLegacyYoloCanvases() {
    const own = state.canvas;
    qsa("canvas").forEach(c => {
      if (c === own) return;
      const r = c.getBoundingClientRect();
      const style = window.getComputedStyle(c);
      const likelyOverlay = (
        r.width > 120 &&
        r.height > 120 &&
        (style.position === "absolute" || style.position === "fixed" || c.id.toLowerCase().includes("overlay") || String(c.className).toLowerCase().includes("overlay"))
      );
      if (likelyOverlay) c.classList.add("p622-hidden-legacy-canvas");
    });
  }

  function softenLegacyTextBadges() {
    const badTokens = [
      "YOLO_READY_NO_TREE_DETECTED",
      "YOLO_NOT_BLOCKED",
      "REALTIME_YOLO_PIPELINE_OK",
      "TREE_MODEL_READY_CANDIDATE",
      "FRAME_WAITING"
    ];

    qsa("span,div,p,strong,em").forEach(el => {
      if (!el || el.id && el.id.startsWith("p622")) return;
      const txt = (el.innerText || el.textContent || "").trim();
      if (!txt) return;
      if (badTokens.some(t => txt.includes(t))) {
        el.style.opacity = "0.38";
        el.style.maxWidth = "160px";
        el.style.overflow = "hidden";
        el.style.textOverflow = "ellipsis";
        el.style.whiteSpace = "nowrap";
      }
    });

    qsa("details").forEach(d => { d.open = false; });
  }

  function ensureCanvas() {
    const video = findVideo();
    if (!video) return null;

    if (!state.canvas) {
      const canvas = document.createElement("canvas");
      canvas.id = "p622VisionCanvas";
      canvas.setAttribute("data-progress6-22", "vision-overlay");
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

    return {video, rect: r, dpr};
  }

  function clearCanvas() {
    if (!state.canvas || !state.ctx) return;
    const r = state.canvas.getBoundingClientRect();
    state.ctx.clearRect(0, 0, r.width, r.height);
  }

  function getDetections(result) {
    if (!result) return [];
    const a = result.overlay_json && Array.isArray(result.overlay_json.boxes) ? result.overlay_json.boxes : null;
    const b = Array.isArray(result.detections) ? result.detections : null;
    return a || b || [];
  }

  function colorForGroup(group) {
    group = String(group || "").toLowerCase();
    if (group.includes("konduktor")) return "rgba(255, 214, 92, 0.98)";
    if (group.includes("struktur")) return "rgba(92, 184, 255, 0.98)";
    if (group.includes("pohon") || group.includes("tree") || group.includes("vegetation")) return "rgba(34, 245, 153, 0.98)";
    return "rgba(210, 218, 225, 0.86)";
  }

  function normalizeBox(det, width, height) {
    let box = det.box_2d || det.bbox_norm_yxyx_1000 || det.bbox || null;
    if (!Array.isArray(box) || box.length < 4) return null;

    let y1 = Number(box[0]);
    let x1 = Number(box[1]);
    let y2 = Number(box[2]);
    let x2 = Number(box[3]);

    if (![x1, y1, x2, y2].every(Number.isFinite)) return null;

    // Gemini/Object Vision contract: [y_min, x_min, y_max, x_max] normalized 0-1000.
    x1 = Math.max(0, Math.min(width, x1 / 1000 * width));
    x2 = Math.max(0, Math.min(width, x2 / 1000 * width));
    y1 = Math.max(0, Math.min(height, y1 / 1000 * height));
    y2 = Math.max(0, Math.min(height, y2 / 1000 * height));

    if (x2 < x1) [x1, x2] = [x2, x1];
    if (y2 < y1) [y1, y2] = [y2, y1];

    if ((x2 - x1) < 4 || (y2 - y1) < 4) return null;
    return {x1, y1, x2, y2, w: x2 - x1, h: y2 - y1};
  }

  function drawVisionResult(result) {
    const info = ensureCanvas();
    if (!info || !state.ctx) return;

    hideLegacyYoloCanvases();
    clearCanvas();

    const detections = getDetections(result);
    const rect = info.rect;
    const ctx = state.ctx;

    ctx.save();
    ctx.lineJoin = "round";
    ctx.lineCap = "round";

    let drawn = 0;

    detections.forEach((det) => {
      const group = det.object_group || det.group || "general_object";
      const box = normalizeBox(det, rect.width, rect.height);
      if (!box) return;

      const color = colorForGroup(group);
      const label = compact((det.label || group || "object") + " " + (det.confidence != null ? Number(det.confidence).toFixed(2) : ""), 30);

      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(2.2, Math.min(5, rect.width / 180));
      ctx.strokeRect(box.x1, box.y1, box.w, box.h);

      ctx.font = "800 13px system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
      const textW = Math.min(rect.width - 12, ctx.measureText(label).width + 14);
      const labelX = Math.max(4, Math.min(box.x1, rect.width - textW - 4));
      const labelY = Math.max(4, box.y1 - 24);

      ctx.fillStyle = "rgba(0, 22, 16, .78)";
      ctx.fillRect(labelX, labelY, textW, 22);
      ctx.fillStyle = color;
      ctx.fillText(label, labelX + 7, labelY + 15);

      drawn += 1;
    });

    ctx.restore();

    const tree = !!result.tree_detected;
    const pole = !!result.pole_detected;
    const conductor = !!result.conductor_detected;
    const model = result.selected_model || result.model || "vision";
    const provider = result.selected_provider || result.provider || "api";

    if (drawn > 0) {
      setChip("p622ChipVision", "VISION_BOX_" + drawn + " " + provider, "ok");
    } else {
      setChip("p622ChipVision", "VISION_NO_BOX", "muted");
    }

    setChip("p622ChipClearance", result.clearance_status || "CLEARANCE_NOT_FINAL", "muted");

    const summary = state.summary;
    if (summary) {
      summary.style.display = "block";
      summary.textContent = compact(
        "Vision: " +
        (tree ? "tree " : "") +
        (conductor ? "conductor " : "") +
        (pole ? "support " : "") +
        "| " + model + " | " +
        (result.frame_summary || "AI-assisted field evidence only."),
        190
      );
    }
  }

  function captureFrameBase64(video) {
    return new Promise((resolve, reject) => {
      try {
        if (!video) return reject(new Error("NO_VIDEO_ELEMENT"));
        const vw = video.videoWidth || video.clientWidth || 720;
        const vh = video.videoHeight || video.clientHeight || 1280;

        if (!vw || !vh) return reject(new Error("VIDEO_DIMENSION_NOT_READY"));

        const canvas = document.createElement("canvas");
        canvas.width = vw;
        canvas.height = vh;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, vw, vh);

        if (canvas.toBlob) {
          canvas.toBlob(function (blob) {
            if (!blob) {
              try {
                const fallback = canvas.toDataURL("image/jpeg", 0.82);
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
          }, "image/jpeg", 0.82);
        } else {
          const dataUrl = canvas.toDataURL("image/jpeg", 0.82);
          resolve(dataUrl.split(",")[1]);
        }
      } catch (err) {
        reject(err);
      }
    });
  }

  async function parseJsonResponse(resp) {
    const contentType = (resp.headers.get("content-type") || "").toLowerCase();
    const text = await resp.text();

    if (!contentType.includes("application/json")) {
      throw new Error("VISION_ANALYZE_NON_JSON_" + text.slice(0, 48).replace(/\s+/g, "_"));
    }

    try {
      return JSON.parse(text);
    } catch (err) {
      throw new Error("VISION_ANALYZE_JSON_PARSE_FAILED_" + (err && err.message || err));
    }
  }

  async function runVisionAnalyze(reason) {
    if (state.busy) return;
    state.busy = true;

    try {
      document.body.classList.add("p622-clean-vision-mode");
      ensureHud();
      hideLegacyYoloCanvases();
      softenLegacyTextBadges();

      setChip("p622ChipVision", "VISION_ANALYZING", "busy");

      const video = findVideo();
      if (!video) throw new Error("NO_CAMERA_VIDEO_FOUND");

      const sessionId = getSessionId();
      state.lastSessionId = sessionId;

      if (!sessionId) throw new Error("FIELD_SESSION_ID_EMPTY_FOR_VISION");

      const imageBase64 = await captureFrameBase64(video);

      const payload = {
        session_id: sessionId,
        point_id: getPointId(),
        image_base64: imageBase64,
        frontend_version: VERSION,
        reason: reason || "shutter",
        no_fake_detection: true,
        no_fake_clearance: true
      };

      const resp = await fetch(ENDPOINT, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
        cache: "no-store"
      });

      const data = await parseJsonResponse(resp);

      if (!resp.ok || data.ok === false || data.status === "VISION_API_UNAVAILABLE") {
        throw new Error(data.error || data.status || ("VISION_HTTP_" + resp.status));
      }

      state.lastResult = data;
      drawVisionResult(data);

      window.PROGRESS_6_22_LAST_VISION_RESULT = data;
      document.documentElement.setAttribute("data-progress6-22-vision-last-status", data.status || "VISION_DONE");

      return data;
    } catch (err) {
      console.error("[P6.22] Vision analyze failed", err);
      setChip("p622ChipVision", "VISION_ERROR", "err");
      if (state.summary) {
        state.summary.style.display = "block";
        state.summary.textContent = compact("Vision error: " + (err && err.message ? err.message : String(err)), 180);
      }
    } finally {
      state.busy = false;
    }
  }

  function isShutterControl(el) {
    if (!el) return false;
    const hay = [
      el.id || "",
      el.className || "",
      el.getAttribute("aria-label") || "",
      el.getAttribute("data-action") || "",
      el.getAttribute("data-role") || "",
      el.innerText || "",
      el.textContent || ""
    ].join(" ").toLowerCase();

    if (hay.includes("map") || hay.includes("result") || hay.includes("manual") || hay.includes("home")) return false;
    return hay.includes("shutter") || hay.includes("jepret") || hay.includes("capture") || hay.includes("snapshot");
  }

  function installShutterHook() {
    document.addEventListener("click", function (ev) {
      const target = ev.target && ev.target.closest ? ev.target.closest("button,a,[role='button'],div") : null;
      if (!isShutterControl(target)) return;

      // Biarkan shutter lama menyimpan evidence dulu, Vision dipanggil sesudahnya.
      setTimeout(function () {
        runVisionAnalyze("shutter_after_save");
      }, 450);
    }, true);
  }

  function installRuntimeLoop() {
    window.addEventListener("resize", function () {
      ensureCanvas();
      if (state.lastResult) drawVisionResult(state.lastResult);
    });

    window.addEventListener("orientationchange", function () {
      setTimeout(function () {
        ensureCanvas();
        if (state.lastResult) drawVisionResult(state.lastResult);
      }, 800);
    });

    setInterval(function () {
      document.body.classList.add("p622-clean-vision-mode");
      ensureCanvas();
      hideLegacyYoloCanvases();
      softenLegacyTextBadges();
      if (state.lastResult) drawVisionResult(state.lastResult);
    }, 1200);
  }

  function install() {
    document.documentElement.setAttribute("data-progress6-22-frontend-vision-overlay", "ready");
    document.body.classList.add("p622-clean-vision-mode");

    ensureHud();
    ensureCanvas();
    hideLegacyYoloCanvases();
    softenLegacyTextBadges();
    installShutterHook();
    installRuntimeLoop();

    setChip("p622ChipVision", "VISION_READY", "ok");
    setChip("p622ChipGps", "GPS_EVIDENCE_ONLY", "muted");
    setChip("p622ChipClearance", "CLEARANCE_NOT_FINAL", "muted");

    window.PROGRESS_6_22_RUN_VISION_ANALYZE = runVisionAnalyze;
    window.PROGRESS_6_22_FRONTEND_VISION_OVERLAY = {
      version: VERSION,
      status: "FIELD_CAMERA_VISION_FRONTEND_READY",
      runVisionAnalyze: runVisionAnalyze
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }
})();
