(function () {
  const output = document.getElementById("status-output");
  const debug = document.getElementById("network-debug");
  const video = document.getElementById("camera");
  const frameCanvas = document.getElementById("frame");
  const overlayCanvas = document.getElementById("overlay-canvas");
  let capturedBlob = null;
  let realtimeActive = false;
  let frameInFlight = false;
  let lastFrameSentAt = 0;
  let realtimeTimer = null;
  let gpsTimer = null;
  let realtimeSessionId = "";
  let realtimeSessionToken = "";
  let ws = null;
  let lastPrediction = {};
  let lastReportUrl = "/field-reports/phase5_2_field_trial_snapshot.csv";
  let lastMapUrl = "";
  const requestedIntervalMs = 1000;
  const maxDisplayAgeMs = 3000;

  function setStatus(payload) {
    output.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  }

  function setDebug(payload) {
    debug.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  }

  function setFieldStatus(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value === undefined || value === null || value === "" ? "-" : value;
  }

  function value(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
  }

  function setValue(id, next) {
    const el = document.getElementById(id);
    if (el) el.value = next === undefined || next === null ? "" : next;
  }

  async function safeFetchJson(endpoint, options) {
    const started = performance.now();
    const response = await fetch(endpoint, options);
    const latency = Math.round(performance.now() - started);
    setFieldStatus("latency-display", `${latency} ms`);
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      const text = await response.text();
      return {
        status: "API_ERROR_NON_JSON_RESPONSE",
        endpoint,
        status_code: response.status,
        response_ok: response.ok,
        preview: text.slice(0, 300)
      };
    }
    const payload = await response.json();
    if (!response.ok) {
      return {
        status: "API_ERROR_JSON_RESPONSE",
        endpoint,
        status_code: response.status,
        payload
      };
    }
    return payload;
  }

  function updateSecureContextStatus() {
    const host = window.location.hostname;
    const local = host === "localhost" || host === "127.0.0.1" || host === "::1";
    if (window.location.protocol === "https:") {
      setFieldStatus("secure-context-status", "SECURE_CONTEXT_EXPECTED");
    } else if (local) {
      setFieldStatus("secure-context-status", "LOCAL_DEV_CONTEXT");
    } else {
      setFieldStatus("secure-context-status", "INSECURE_CONTEXT_CAMERA_GPS_MAY_FAIL");
    }
  }

  async function refreshRuntimeStatus() {
    const runtime = await safeFetchJson("/api/runtime/status");
    setFieldStatus("server-status", runtime.status || "RUNTIME_STATUS_READY");
    setFieldStatus("model-status", runtime.model_status || "MODEL_NOT_READY");
    setFieldStatus("output-model-status", runtime.model_status || "MODEL_NOT_READY");
    setFieldStatus("tunnel-status", (runtime.public_links || {}).status || "NO_PUBLIC_TUNNEL_CONFIGURED");
    setFieldStatus("realtime-transport-status", (runtime.websocket || {}).status || "HTTP_FALLBACK_READY");
    const calibration = await safeFetchJson("/api/calibration/status");
    setFieldStatus("calibration-status", calibration.status || "CALIBRATION_NOT_READY");
    setDebug({ runtime, calibration });
  }

  async function startCamera() {
    updateSecureContextStatus();
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setFieldStatus("camera-status", "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT");
        setStatus("CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT");
        return false;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      video.srcObject = stream;
      setFieldStatus("camera-status", "CAMERA_READY");
      setStatus("CAMERA_READY");
      return true;
    } catch (error) {
      const blocked = !window.isSecureContext && window.location.protocol !== "https:";
      setFieldStatus("camera-status", blocked ? "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT" : "CAMERA_PERMISSION_DENIED");
      setStatus({ status: blocked ? "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT" : "CAMERA_PERMISSION_DENIED", message: String(error), fallback: "Gunakan fallback upload image." });
      return false;
    }
  }

  function stopCamera() {
    const stream = video.srcObject;
    if (stream && stream.getTracks) {
      stream.getTracks().forEach(function (track) {
        track.stop();
      });
    }
    video.srcObject = null;
    setFieldStatus("camera-status", "CAMERA_STOPPED");
  }

  function requestGps() {
    updateSecureContextStatus();
    if (!navigator.geolocation) {
      setFieldStatus("gps-status", "GPS_API_UNAVAILABLE_IN_THIS_CONTEXT");
      setStatus("GPS_API_UNAVAILABLE_IN_THIS_CONTEXT");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      function (position) {
        setValue("lat", position.coords.latitude.toFixed(7));
        setValue("lon", position.coords.longitude.toFixed(7));
        setValue("gps_accuracy_m", position.coords.accuracy ? position.coords.accuracy.toFixed(1) : "");
        setValue("gps_source", "GPS_SOURCE_BROWSER");
        setFieldStatus("gps-status", "GPS_READY");
        setFieldStatus("gps-source-status", "GPS_SOURCE_BROWSER");
        setStatus("GPS_READY");
      },
      function (error) {
        const code = error && error.code;
        const status = code === 1 ? "GPS_PERMISSION_DENIED" : code === 3 ? "GPS_TIMEOUT" : "GPS_SIGNAL_NOT_READY";
        setFieldStatus("gps-status", status);
        setStatus({ status, message: String((error && error.message) || error), fallback: "Isi latitude/longitude manual jika tersedia. Tanpa GPS, map marker tidak dibuat." });
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  }

  function markGpsManualIfTyped() {
    if ((value("lat") || value("lon")) && value("gps_source") !== "GPS_SOURCE_BROWSER") {
      setValue("gps_source", "GPS_SOURCE_MANUAL");
      setFieldStatus("gps-source-status", "GPS_SOURCE_MANUAL");
    }
  }

  function collectPayload() {
    markGpsManualIfTyped();
    return {
      point_id: value("point_id") || "V001_pohon_sono",
      species: value("species") || "pohon_sono",
      asset_type: value("asset_type") || "span",
      latitude: value("lat"),
      longitude: value("lon"),
      gps_accuracy_m: value("gps_accuracy_m"),
      gps_source: value("gps_source") || "GPS_NOT_PROVIDED",
      clearance_m: value("clearance_m"),
      tree_height_m: value("tree_height_m"),
      asset_height_m: value("asset_height_m"),
      span_lowest_point_height_m: value("span_lowest_point_height_m"),
      growth_rate_m_per_day: value("growth_rate_m_per_day"),
      measurement_source: value("measurement_source") || "manual",
      environment_source: value("environment_source") || "not_available",
      notes: value("operator_note"),
      operator_notes: value("operator_note"),
      image_reference: (document.getElementById("image").files[0] || {}).name || (capturedBlob ? "captured-frame-not-stored" : ""),
      timestamp: new Date().toISOString()
    };
  }

  function applyPredictionOutput(payload) {
    lastPrediction = payload || {};
    setFieldStatus("output-model-status", payload.model_status || "MODEL_NOT_READY");
    setFieldStatus("model-status", payload.model_status || "MODEL_NOT_READY");
    setFieldStatus("inference-source", payload.inference_source || "-");
    setFieldStatus("confidence-status", payload.confidence_status || "-");
    setFieldStatus("measurement-quality-label", payload.measurement_quality_label || "-");
    setFieldStatus("clearance-display-floor", payload.clearance_display_m_integer_floor);
    setFieldStatus("clearance-raw", payload.clearance_raw_m);
    setFieldStatus("eta-days", payload.eta_days);
    setFieldStatus("eta-months", payload.eta_months);
    setFieldStatus("risk-status", payload.risk_status || payload.risk_priority || "-");
    setFieldStatus("action-priority", payload.action_priority || payload.risk_priority || "-");
    setFieldStatus("reason-codes", Array.isArray(payload.reason_codes) ? payload.reason_codes.join(";") : payload.reason_codes);
    setFieldStatus("report-id", payload.report_id || payload.job_id || payload.session_id || "-");
    if (payload.report_csv_url) {
      lastReportUrl = payload.report_csv_url;
      setFieldStatus("report-path", payload.report_csv_url);
    } else if (payload.report_csv_path || payload.report_path) {
      setFieldStatus("report-path", payload.report_csv_path || payload.report_path);
    }
    if (payload.map_url) {
      lastMapUrl = payload.map_url;
      setFieldStatus("map-path", payload.map_url);
    } else if (payload.map_path) {
      setFieldStatus("map-path", payload.map_path);
    }
    setStatus(payload);
  }

  async function runManualPrediction() {
    const payload = await safeFetchJson("/api/field/manual-prediction", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectPayload())
    });
    applyPredictionOutput(payload);
    setDebug(payload);
  }

  async function sendSnapshotReport() {
    const payload = await safeFetchJson("/api/field/snapshot-report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...collectPayload(), latest_prediction_status: lastPrediction.status, report_trigger: "MANUAL_SNAPSHOT" })
    });
    applyPredictionOutput(payload);
    setDebug(payload);
  }

  async function createRealtimeSession() {
    const session = await safeFetchJson("/api/realtime/session/new");
    realtimeSessionId = session.session_id || "";
    realtimeSessionToken = session.session_token || "";
    setFieldStatus("realtime-transport-status", "SESSION_READY_HTTP_FALLBACK");
    return session;
  }

  function openRealtimeWebSocket() {
    if (!realtimeSessionId || typeof WebSocket === "undefined") return false;
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    try {
      ws = new WebSocket(`${scheme}://${window.location.host}/ws/realtime-detect`);
      ws.onopen = function () {
        setFieldStatus("realtime-transport-status", "WEBSOCKET_CONNECTED");
      };
      ws.onmessage = function (event) {
        frameInFlight = false;
        handleRealtimeResult(JSON.parse(event.data));
      };
      ws.onerror = function () {
        setFieldStatus("realtime-transport-status", "WEBSOCKET_ERROR_HTTP_FALLBACK");
      };
      ws.onclose = function () {
        if (realtimeActive) setFieldStatus("realtime-transport-status", "HTTP_FALLBACK_1FPS");
      };
      return true;
    } catch (error) {
      setFieldStatus("realtime-transport-status", "WEBSOCKET_UNAVAILABLE_HTTP_FALLBACK");
      return false;
    }
  }

  async function startRealtimeDetection() {
    realtimeActive = true;
    setFieldStatus("mode-label", "REALTIME_OR_HTTP_FALLBACK");
    await startCamera();
    await createRealtimeSession();
    openRealtimeWebSocket();
    requestGps();
    gpsTimer = window.setInterval(requestGps, 8000);
    realtimeTimer = window.setInterval(sendRealtimeFrame, requestedIntervalMs);
    setFieldStatus("refresh-interval-display", `${requestedIntervalMs} ms`);
    setStatus("REALTIME_DETECTION_STARTED_NO_FAKE_DETECTION");
  }

  function stopRealtimeDetection() {
    realtimeActive = false;
    frameInFlight = false;
    if (realtimeTimer) window.clearInterval(realtimeTimer);
    if (gpsTimer) window.clearInterval(gpsTimer);
    realtimeTimer = null;
    gpsTimer = null;
    if (ws) ws.close();
    ws = null;
    setFieldStatus("realtime-transport-status", "STOPPED");
    setStatus("REALTIME_DETECTION_STOPPED");
  }

  async function sendRealtimeFrame() {
    if (!realtimeActive || !realtimeSessionId) return;
    const now = Date.now();
    if (now - lastFrameSentAt < requestedIntervalMs || frameInFlight) {
      setFieldStatus("realtime-transport-status", "LATEST_ONLY_DROPPING_FRAME");
      return;
    }
    const imageBase64 = captureFrameBase64();
    if (!imageBase64) {
      setStatus("CAMERA_FRAME_NOT_READY_NO_FAKE_DETECTION");
      return;
    }
    frameInFlight = true;
    lastFrameSentAt = now;
    const payload = {
      session_id: realtimeSessionId,
      session_token: realtimeSessionToken,
      frame_id: `frame_${now}`,
      timestamp_client_ms: now,
      point_id: value("point_id") || "V001_pohon_sono",
      species_hint: value("species") || "pohon_sono",
      asset_type: value("asset_type") || "span",
      gps_lat: value("lat"),
      gps_lon: value("lon"),
      image_jpeg_base64: imageBase64,
      client_mode: window.location.protocol === "https:" ? "remote_https" : "lan_http",
      requested_interval_ms: requestedIntervalMs
    };
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
      return;
    }
    try {
      const response = await safeFetchJson("/api/realtime/frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      frameInFlight = false;
      handleRealtimeResult(response);
    } catch (error) {
      frameInFlight = false;
      setFieldStatus("realtime-transport-status", "HTTP_FALLBACK_SEND_FAILED");
      setStatus({ status: "REALTIME_FRAME_SEND_FAILED", message: String(error) });
    }
  }

  function captureFrameBase64() {
    if (!video.videoWidth) return "";
    const maxWidth = 960;
    const scale = Math.min(1, maxWidth / video.videoWidth);
    frameCanvas.width = Math.floor(video.videoWidth * scale);
    frameCanvas.height = Math.floor(video.videoHeight * scale);
    frameCanvas.getContext("2d").drawImage(video, 0, 0, frameCanvas.width, frameCanvas.height);
    const dataUrl = frameCanvas.toDataURL("image/jpeg", 0.7);
    return dataUrl.split(",", 2)[1] || "";
  }

  function handleRealtimeResult(payload) {
    const latency = payload.latency_ms || 0;
    if (latency > maxDisplayAgeMs || payload.queue_status === "HIGH_LATENCY_DROPPING_OLD_FRAMES") {
      setFieldStatus("realtime-transport-status", "HIGH_LATENCY_DROPPING_OLD_FRAMES");
    } else if (payload.status === "FRAME_RATE_LIMITED") {
      setFieldStatus("realtime-transport-status", "FRAME_RATE_LIMITED_1FPS");
    } else {
      setFieldStatus("realtime-transport-status", payload.queue_status || "REALTIME_OK");
    }
    setFieldStatus("latency-display", `${latency} ms`);
    applyPredictionOutput({
      ...payload,
      inference_source: (payload.inference_contract || {}).detection_source || payload.detection_status,
      confidence_status: payload.confidence_status,
      clearance_raw_m: payload.selected_clearance_m_raw,
      clearance_display_m_integer_floor: payload.selected_clearance_display_m,
      risk_status: payload.distance_zone_status || payload.risk_priority,
      action_priority: payload.risk_priority,
      reason_codes: [payload.detection_status, payload.queue_status, payload.eta_status].filter(Boolean)
    });
    drawOverlay(payload.overlay_json || {});
    setDebug(payload);
  }

  function drawOverlay(overlay) {
    if (!overlayCanvas || !video.videoWidth) return;
    overlayCanvas.width = video.videoWidth;
    overlayCanvas.height = video.videoHeight;
    const ctx = overlayCanvas.getContext("2d");
    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    (overlay.boxes || []).forEach(function (box) {
      const bbox = box.bbox || [];
      if (bbox.length !== 4) return;
      ctx.strokeStyle = box.color || "#1b5b52";
      ctx.lineWidth = 3;
      ctx.strokeRect(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]);
      ctx.fillStyle = ctx.strokeStyle;
      ctx.font = "16px Arial";
      ctx.fillText(`${box.label || "object"} ${box.confidence || ""}`, bbox[0], Math.max(16, bbox[1] - 4));
    });
  }

  function captureStillFrame() {
    if (!video.videoWidth) {
      setStatus("CAMERA_FRAME_NOT_READY_USE_FILE_UPLOAD_FALLBACK");
      return;
    }
    frameCanvas.width = video.videoWidth;
    frameCanvas.height = video.videoHeight;
    frameCanvas.getContext("2d").drawImage(video, 0, 0);
    frameCanvas.toBlob(function (blob) {
      capturedBlob = blob;
      setFieldStatus("mode-label", "CAPTURED_FRAME_REFERENCE_ONLY");
      setStatus("FRAME_CAPTURED_REFERENCE_READY");
    }, "image/jpeg", 0.82);
  }

  async function copyReportLink() {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}${lastReportUrl}`);
      setStatus("REPORT_LINK_COPIED");
    } catch (error) {
      setStatus({ status: "REPORT_LINK_READY_COPY_MANUAL", link: `${window.location.origin}${lastReportUrl}`, message: String(error) });
    }
  }

  function openMapReport() {
    if (lastMapUrl) {
      window.open(lastMapUrl, "_blank", "noopener");
      return;
    }
    setStatus("MAP_NOT_AVAILABLE_YET_NO_GPS_NO_MARKER_OR_SNAPSHOT_NOT_SENT");
  }

  document.getElementById("ping-btn").addEventListener("click", async function () {
    const payload = await safeFetchJson("/api/network/health");
    setFieldStatus("server-status", payload.status || "NETWORK_HEALTH_READY");
    setStatus(payload);
    setDebug(payload);
  });
  document.getElementById("gps-btn").addEventListener("click", requestGps);
  document.getElementById("camera-permission").addEventListener("click", startCamera);
  document.getElementById("start-camera").addEventListener("click", startCamera);
  document.getElementById("stop-camera").addEventListener("click", stopCamera);
  document.getElementById("start-realtime").addEventListener("click", startRealtimeDetection);
  document.getElementById("stop-realtime").addEventListener("click", stopRealtimeDetection);
  document.getElementById("capture-frame").addEventListener("click", captureStillFrame);
  document.getElementById("manual-prediction").addEventListener("click", runManualPrediction);
  document.getElementById("snapshot-report").addEventListener("click", sendSnapshotReport);
  document.getElementById("copy-report-link").addEventListener("click", copyReportLink);
  document.getElementById("open-map-report").addEventListener("click", openMapReport);
  document.getElementById("lat").addEventListener("change", markGpsManualIfTyped);
  document.getElementById("lon").addEventListener("change", markGpsManualIfTyped);

  updateSecureContextStatus();
  refreshRuntimeStatus();
})();
