(function () {
  const output = document.getElementById("status-output");
  const debug = document.getElementById("network-debug");
  const video = document.getElementById("camera");
  const frameCanvas = document.getElementById("frame");
  const overlayCanvas = document.getElementById("overlay-canvas");
  let realtimeActive = false;
  let frameInFlight = false;
  let realtimeTimer = null;
  let gpsWatchId = null;
  let latestGps = { gps_source: "GPS_NOT_PROVIDED" };
  let latestMeasurement = {};
  let latestFrameBase64 = "";
  let lastReportUrl = "/field-reports/field_capture_autosave.csv";
  let lastMapUrl = "";
  let lastPublicUrl = "";
  let lastLanUrl = "";
  let debugMode = false;
  let realtimeIntervalMs = 1000;
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

  function currentUrlMode() {
    const host = window.location.hostname;
    const isLocal = host === "localhost" || host === "127.0.0.1" || host === "::1";
    const isPublicHttps = window.location.protocol === "https:";
    if (isPublicHttps) return "HTTPS_PUBLIC_READY";
    if (isLocal) return "LOCALHOST_DEBUG_ONLY";
    return "LAN_HTTP_DEBUG_ONLY";
  }

  function isInsecureFieldContext() {
    return currentUrlMode() === "LAN_HTTP_DEBUG_ONLY" && !window.isSecureContext;
  }

  function updateLanWarning(mode) {
    const warning = document.getElementById("lan-http-warning");
    if (warning) warning.hidden = mode !== "LAN_HTTP_DEBUG_ONLY";
  }

  function value(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
  }

  function setValue(id, next) {
    const el = document.getElementById(id);
    if (el) el.value = next === undefined || next === null ? "" : next;
  }

  function addClick(id, fn) {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", fn);
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
    const mode = currentUrlMode();
    setFieldStatus("current-url-mode", mode);
    updateLanWarning(mode);
    if (mode === "HTTPS_PUBLIC_READY") {
      setFieldStatus("secure-context-status", "SECURE_CONTEXT_OK");
      setFieldStatus("secure-context-top", "SECURE_CONTEXT_OK");
    } else if (mode === "LOCALHOST_DEBUG_ONLY") {
      setFieldStatus("secure-context-status", "LOCAL_DEV_CONTEXT");
      setFieldStatus("secure-context-top", "LOCAL_DEV_CONTEXT");
    } else {
      setFieldStatus("secure-context-status", "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED");
      setFieldStatus("secure-context-top", "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED");
    }
  }

  async function refreshRuntimeStatus() {
    const runtime = await safeFetchJson("/api/runtime/status");
    const realtime = await safeFetchJson("/api/field/realtime-status");
    const calibration = await safeFetchJson("/api/field/calibration-status");
    const secureDiagnostic = await safeFetchJson("/api/runtime/secure-context-diagnostic");
    setFieldStatus("server-status", runtime.status || "RUNTIME_STATUS_READY");
    setFieldStatus("model-status", realtime.model_status || runtime.model_status || "MODEL_NOT_READY");
    setFieldStatus("output-model-status", realtime.model_status || runtime.model_status || "MODEL_NOT_READY");
    setFieldStatus("model-runtime-status", realtime.model_status || runtime.model_status || "MODEL_NOT_READY");
    setFieldStatus("custom-model-status", realtime.model_status || runtime.model_status || "MODEL_NOT_READY");
    setFieldStatus("tunnel-status", runtime.tunnel_status || (runtime.public_links || {}).tunnel_status || (runtime.public_links || {}).status || "PUBLIC_TUNNEL_NOT_RUNNING");
    setFieldStatus("public-tunnel-status", runtime.tunnel_status || (runtime.public_links || {}).tunnel_status || "PUBLIC_TUNNEL_NOT_RUNNING");
    setFieldStatus("current-url-mode", secureDiagnostic.current_url_mode || currentUrlMode());
    setFieldStatus("secure-context-top", secureDiagnostic.secure_context_status || document.getElementById("secure-context-status").textContent);
    setFieldStatus("realtime-transport-status", (runtime.websocket || {}).status || "HTTP_FALLBACK_READY");
    setFieldStatus("calibration-status", calibration.status || "CALIBRATION_NOT_READY");
    setFieldStatus("refresh-interval-display", `${realtime.result_update_interval_ms || 1000} ms stable update`);
    lastPublicUrl = ((runtime.public_links || {}).public_field_capture_url || "");
    lastLanUrl = ((runtime.public_links || {}).lan_field_capture_url || "");
    setFieldStatus("public-url-display", lastPublicUrl || "PUBLIC_TUNNEL_NOT_RUNNING");
    updateLanWarning(secureDiagnostic.current_url_mode || currentUrlMode());
    setDebug({ runtime, realtime, calibration, secureDiagnostic });
  }

  async function refreshTunnelStatus() {
    const tunnel = await safeFetchJson("/api/runtime/tunnel-status");
    setFieldStatus("tunnel-status", tunnel.status || "PUBLIC_TUNNEL_NOT_RUNNING");
    setFieldStatus("public-tunnel-status", tunnel.status || "PUBLIC_TUNNEL_NOT_RUNNING");
    if (tunnel.field_capture_public_url) lastPublicUrl = tunnel.field_capture_public_url;
    if (tunnel.public_field_capture_url) lastPublicUrl = tunnel.public_field_capture_url;
    setFieldStatus("public-url-display", lastPublicUrl || "PUBLIC_TUNNEL_NOT_RUNNING");
    setStatus(tunnel);
    setDebug(tunnel);
  }

  async function startCamera() {
    updateSecureContextStatus();
    if (isInsecureFieldContext()) {
      const status = "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED_OPEN_HTTPS_TUNNEL";
      setFieldStatus("camera-status", status);
      setFieldStatus("camera-permission-status", status);
      setFieldStatus("last-error-status", "Buka public HTTPS URL terlebih dahulu.");
      setStatus({ status, message: "Buka public HTTPS URL terlebih dahulu.", recommended_url: lastPublicUrl || "ngrok http 5000" });
      return false;
    }
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setFieldStatus("camera-status", "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT");
        setFieldStatus("camera-permission-status", "CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT");
        setStatus("CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT");
        return false;
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      video.srcObject = stream;
      setFieldStatus("camera-status", "CAMERA_READY");
      setFieldStatus("camera-permission-status", "CAMERA_READY");
      setStatus("CAMERA_READY");
      return true;
    } catch (error) {
      const blocked = !window.isSecureContext && window.location.protocol !== "https:";
      const status = blocked ? "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED_OPEN_HTTPS_TUNNEL" : "CAMERA_PERMISSION_DENIED";
      setFieldStatus("camera-status", status);
      setFieldStatus("camera-permission-status", status);
      setFieldStatus("last-error-status", String(error).slice(0, 120));
      setStatus({ status, message: String(error), fallback: "Buka public HTTPS URL terlebih dahulu atau gunakan fallback upload image." });
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
    if (isInsecureFieldContext()) {
      const status = "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED_OPEN_HTTPS_TUNNEL";
      setFieldStatus("gps-status", status);
      setFieldStatus("gps-permission-status", status);
      setFieldStatus("last-error-status", "Buka public HTTPS URL terlebih dahulu.");
      setStatus({ status, message: "Buka public HTTPS URL terlebih dahulu.", recommended_url: lastPublicUrl || "ngrok http 5000" });
      return;
    }
    if (!navigator.geolocation) {
      setFieldStatus("gps-status", "GPS_API_UNAVAILABLE_IN_THIS_CONTEXT");
      setFieldStatus("gps-permission-status", "GPS_API_UNAVAILABLE_IN_THIS_CONTEXT");
      setStatus("GPS_API_UNAVAILABLE_IN_THIS_CONTEXT");
      return;
    }
    if (gpsWatchId !== null) navigator.geolocation.clearWatch(gpsWatchId);
    gpsWatchId = navigator.geolocation.watchPosition(
      function (position) {
        const accuracy = position.coords.accuracy || 0;
        latestGps = {
          gps_lat: position.coords.latitude,
          gps_lon: position.coords.longitude,
          gps_accuracy_m: accuracy,
          gps_source: "GPS_SOURCE_BROWSER",
          heading: position.coords.heading || ""
        };
        setValue("lat", position.coords.latitude.toFixed(7));
        setValue("lon", position.coords.longitude.toFixed(7));
        setValue("gps_accuracy_m", accuracy ? accuracy.toFixed(1) : "");
        setValue("gps_source", "GPS_SOURCE_BROWSER");
        setFieldStatus("gps-status", accuracy > 20 ? "LOW_ACCURACY" : "GPS_ACTIVE");
        setFieldStatus("gps-permission-status", "GPS_ACTIVE");
        setFieldStatus("gps-source-status", "GPS_SOURCE_BROWSER");
        setFieldStatus("gps-accuracy-status", accuracy ? `${accuracy.toFixed(1)} m` : "-");
        setStatus(accuracy > 20 ? "GPS_ACTIVE_LOW_ACCURACY" : "GPS_ACTIVE");
      },
      function (error) {
        const code = error && error.code;
        const status = code === 1 ? "GPS_PERMISSION_DENIED" : code === 3 ? "GPS_TIMEOUT" : "GPS_SIGNAL_NOT_READY";
        setFieldStatus("gps-status", status);
        setFieldStatus("gps-permission-status", status);
        setFieldStatus("last-error-status", String((error && error.message) || error).slice(0, 120));
        setStatus({ status, message: String((error && error.message) || error), fallback: "Tanpa GPS, shutter tetap bisa tersimpan tetapi map marker tidak dibuat." });
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  }

  function markGpsManualIfTyped() {
    if ((value("lat") || value("lon")) && value("gps_source") !== "GPS_SOURCE_BROWSER") {
      latestGps = {
        gps_lat: value("lat"),
        gps_lon: value("lon"),
        gps_accuracy_m: value("gps_accuracy_m"),
        gps_source: "GPS_SOURCE_MANUAL"
      };
      setValue("gps_source", "GPS_SOURCE_MANUAL");
      setFieldStatus("gps-source-status", "GPS_SOURCE_MANUAL");
    }
  }

  function collectOperatorPayload() {
    markGpsManualIfTyped();
    return {
      point_id: value("point_id") || "V001_pohon_sono",
      species: value("species") || "pohon_sono",
      asset_type: value("asset_type") || "span",
      operator_name: value("operator_name"),
      notes: value("operator_note"),
      operator_notes: value("operator_note"),
      timestamp: new Date().toISOString(),
      ...latestGps
    };
  }

  function collectLegacyManualPayload() {
    return {
      ...collectOperatorPayload(),
      latitude: value("lat"),
      longitude: value("lon"),
      clearance_m: value("clearance_m"),
      tree_height_m: value("tree_height_m"),
      asset_height_m: value("asset_height_m"),
      span_lowest_point_height_m: value("span_lowest_point_height_m"),
      growth_rate_m_per_day: value("growth_rate_m_per_day"),
      measurement_source: value("measurement_source") || "manual",
      environment_source: value("environment_source") || "not_available"
    };
  }

  function applyPredictionOutput(payload) {
    const measurement = payload.measurement_result || payload;
    latestMeasurement = measurement || {};
    debugMode = Boolean(payload.debug_mode || measurement.debug_mode);
    setFieldStatus("output-model-status", payload.model_status || measurement.model_status || "MODEL_NOT_READY");
    setFieldStatus("model-status", payload.model_status || measurement.model_status || "MODEL_NOT_READY");
    setFieldStatus("inference-source", payload.detection_source || payload.inference_source || "-");
    setFieldStatus("confidence-status", measurement.confidence_status || payload.confidence_status || "-");
    setFieldStatus("measurement-quality-label", measurement.measurement_quality_label || payload.measurement_quality_label || "-");
    setFieldStatus("object-detected", JSON.stringify(payload.object_detected || {
      pole: measurement.pole_detected,
      conductor: measurement.conductor_detected,
      tree: measurement.tree_detected
    }));
    setFieldStatus("tree-height-m", measurement.tree_height_m);
    setFieldStatus("pole-height-reference-m", measurement.pole_reference_height_m);
    setFieldStatus("cable-height-m", measurement.cable_height_m);
    setFieldStatus("clearance-raw", measurement.clearance_m || payload.clearance_raw_m);
    setFieldStatus("clearance-display-floor", measurement.clearance_m === undefined || measurement.clearance_m === null ? payload.clearance_display_m_integer_floor : Math.floor(Number(measurement.clearance_m)));
    setFieldStatus("eta-days", measurement.eta_days || payload.eta_days);
    setFieldStatus("eta-months", measurement.eta_months || payload.eta_months);
    setFieldStatus("risk-status", measurement.zone_status || payload.risk_status || payload.risk_priority || "-");
    setFieldStatus("action-priority", measurement.action_recommendation || payload.action_priority || payload.risk_priority || "-");
    const reasonCodes = measurement.reason_codes || payload.reason_codes || [];
    setFieldStatus("reason-codes", Array.isArray(reasonCodes) ? reasonCodes.join(";") : reasonCodes);
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
    } else if (payload.map_status) {
      setFieldStatus("map-path", payload.map_status);
    }
    setStatus(payload);
  }

  async function runManualPrediction() {
    const payload = await safeFetchJson("/api/field/manual-prediction", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectLegacyManualPayload())
    });
    applyPredictionOutput(payload);
    setDebug(payload);
  }

  async function sendSnapshotReport() {
    await shutterCapture();
  }

  async function startRealtimeDetection() {
    realtimeActive = true;
    debugMode = false;
    setFieldStatus("mode-label", "REALTIME_CAMERA_GEOMETRY");
    const cameraOk = await startCamera();
    if (!cameraOk) return;
    requestGps();
    setRealtimeInterval(realtimeIntervalMs);
    setFieldStatus("refresh-interval-display", `${realtimeIntervalMs} ms stable update`);
    setStatus("REALTIME_CAMERA_GEOMETRY_STARTED_NO_FAKE_DETECTION");
  }

  function setRealtimeInterval(intervalMs) {
    realtimeIntervalMs = Math.max(1000, Math.min(3000, Number(intervalMs) || 1000));
    if (realtimeTimer) window.clearInterval(realtimeTimer);
    realtimeTimer = window.setInterval(sendRealtimeFrame, realtimeIntervalMs);
    setFieldStatus("frame-interval-status", `${realtimeIntervalMs} ms`);
  }

  function stopRealtimeDetection() {
    realtimeActive = false;
    frameInFlight = false;
    if (realtimeTimer) window.clearInterval(realtimeTimer);
    realtimeTimer = null;
    setFieldStatus("realtime-transport-status", "STOPPED");
    setStatus("REALTIME_DETECTION_STOPPED");
  }

  async function sendRealtimeFrame() {
    if (!realtimeActive || frameInFlight) return;
    const imageBase64 = captureFrameBase64();
    if (!imageBase64) {
      setStatus("CAMERA_FRAME_NOT_READY_NO_FAKE_DETECTION");
      return;
    }
    latestFrameBase64 = imageBase64;
    frameInFlight = true;
    try {
      const payload = await safeFetchJson("/api/field/realtime-frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildFramePayload(imageBase64))
      });
      frameInFlight = false;
      handleRealtimeResult(payload);
    } catch (error) {
      frameInFlight = false;
      setFieldStatus("realtime-transport-status", "HTTP_FALLBACK_SEND_FAILED");
      setStatus({ status: "REALTIME_FRAME_SEND_FAILED", message: String(error) });
    }
  }

  async function debugCocoOverlay() {
    debugMode = true;
    const cameraOk = await startCamera();
    if (!cameraOk) return;
    const imageBase64 = captureFrameBase64();
    if (!imageBase64) {
      setStatus("DEBUG_COCO_CAMERA_FRAME_NOT_READY");
      return;
    }
    latestFrameBase64 = imageBase64;
    const payload = await safeFetchJson("/api/field/debug-coco-frame", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildFramePayload(imageBase64))
    });
    handleRealtimeResult(payload);
  }

  function buildFramePayload(imageBase64) {
    return {
      ...collectOperatorPayload(),
      frame_id: `p54_${Date.now()}`,
      timestamp_client_ms: Date.now(),
      image_jpeg_base64: imageBase64,
      camera_width: video.videoWidth || frameCanvas.width || "",
      camera_height: video.videoHeight || frameCanvas.height || "",
      client_mode: window.location.protocol === "https:" ? "remote_https" : "lan_http",
      requested_interval_ms: realtimeIntervalMs,
      secure_context_status: document.getElementById("secure-context-status").textContent,
      current_url_mode: document.getElementById("current-url-mode").textContent,
      public_tunnel_status: document.getElementById("public-tunnel-status").textContent,
      debug_mode: debugMode
    };
  }

  function captureFrameBase64() {
    if (!video.videoWidth) return "";
    const maxWidth = 960;
    const scale = Math.min(1, maxWidth / video.videoWidth);
    frameCanvas.width = Math.floor(video.videoWidth * scale);
    frameCanvas.height = Math.floor(video.videoHeight * scale);
    frameCanvas.getContext("2d").drawImage(video, 0, 0, frameCanvas.width, frameCanvas.height);
    const dataUrl = frameCanvas.toDataURL("image/jpeg", 0.72);
    return dataUrl.split(",", 2)[1] || "";
  }

  function handleRealtimeResult(payload) {
    const latency = payload.latency_ms || payload.processing_time_ms || 0;
    if (latency > maxDisplayAgeMs || payload.latency_status === "HIGH_LATENCY") {
      setFieldStatus("realtime-transport-status", "HIGH_LATENCY");
      setRealtimeInterval(realtimeIntervalMs + 1000);
    } else {
      setFieldStatus("realtime-transport-status", "HTTP_FALLBACK_1FPS");
    }
    setFieldStatus("latency-display", `${latency} ms`);
    applyPredictionOutput(payload);
    drawOverlay(payload.overlay_json || {}, payload);
    setDebug(payload);
  }

  function drawOverlay(overlay, payload) {
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
    const line = overlay.measurement_line || {};
    if (line.status === "AVAILABLE" && line.tree_top_px !== undefined && line.cable_px !== undefined) {
      ctx.strokeStyle = "#e11d48";
      ctx.setLineDash([8, 6]);
      ctx.beginPath();
      ctx.moveTo(24, line.cable_px);
      ctx.lineTo(Math.max(24, overlayCanvas.width - 24), line.cable_px);
      ctx.moveTo(24, line.tree_top_px);
      ctx.lineTo(Math.max(24, overlayCanvas.width - 24), line.tree_top_px);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    const message = overlay.message || (payload && payload.model_status === "MODEL_NOT_READY" ? "MODEL_NOT_READY_NO_FAKE_DETECTION" : "");
    if (message && !(overlay.boxes || []).length) {
      ctx.fillStyle = "rgba(0, 0, 0, 0.62)";
      ctx.fillRect(16, 16, Math.min(overlayCanvas.width - 32, 420), 44);
      ctx.fillStyle = "#ffffff";
      ctx.font = "18px Arial";
      ctx.fillText(message, 28, 45);
    }
  }

  function captureStillFrame() {
    const imageBase64 = captureFrameBase64();
    if (!imageBase64) {
      setStatus("CAMERA_FRAME_NOT_READY_USE_FILE_UPLOAD_FALLBACK");
      return;
    }
    latestFrameBase64 = imageBase64;
    setFieldStatus("mode-label", "CAPTURED_FRAME_REFERENCE_ONLY");
    setStatus("FRAME_CAPTURED_REFERENCE_READY");
  }

  async function shutterCapture() {
    const imageBase64 = captureFrameBase64() || latestFrameBase64;
    const payload = await safeFetchJson("/api/field/shutter-capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...collectOperatorPayload(),
        timestamp_client_ms: Date.now(),
        image_jpeg_base64: imageBase64,
        camera_width: video.videoWidth || frameCanvas.width || "",
        camera_height: video.videoHeight || frameCanvas.height || "",
        model_status: document.getElementById("model-status").textContent || "MODEL_NOT_READY",
        secure_context_status: document.getElementById("secure-context-status").textContent,
        current_url_mode: document.getElementById("current-url-mode").textContent,
        public_tunnel_status: document.getElementById("public-tunnel-status").textContent,
        debug_mode: debugMode,
        measurement_result: latestMeasurement
      })
    });
    applyPredictionOutput(payload);
    setDebug(payload);
  }

  async function openReportLink() {
    if (lastReportUrl) {
      window.open(lastReportUrl, "_blank", "noopener");
      return;
    }
    const latest = await safeFetchJson("/api/field/report-latest");
    setStatus(latest);
  }

  async function copyTextOrShow(text, fallbackStatus) {
    if (!text) {
      setStatus(fallbackStatus);
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setStatus({ status: "LINK_COPIED", link: text });
    } catch (error) {
      setStatus({ status: "LINK_READY_COPY_MANUAL", link: text, message: String(error) });
    }
  }

  async function copyPublicUrl() {
    if (!lastPublicUrl) await refreshTunnelStatus();
    copyTextOrShow(lastPublicUrl, "PUBLIC_TUNNEL_NOT_RUNNING_RUN_NGROK_HTTP_5000");
  }

  async function openPublicUrl() {
    if (!lastPublicUrl) await refreshTunnelStatus();
    if (!lastPublicUrl) {
      setStatus("PUBLIC_TUNNEL_NOT_RUNNING_RUN_NGROK_HTTP_5000");
      return;
    }
    window.open(lastPublicUrl, "_blank", "noopener");
  }

  async function copyLanUrl() {
    if (!lastLanUrl) {
      const links = await safeFetchJson("/api/runtime/public-links");
      lastLanUrl = links.lan_field_capture_url || "";
    }
    copyTextOrShow(lastLanUrl, "LAN_URL_NOT_DETECTED_CHECK_IPCONFIG_OR_USE_NGROK");
  }

  async function failureRecoveryHelp() {
    const payload = await safeFetchJson("/api/operator/failure-recovery", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        hp_can_open_url: true,
        tunnel_status: document.getElementById("tunnel-status").textContent,
        server_status: document.getElementById("server-status").textContent,
        camera_status: document.getElementById("camera-status").textContent,
        gps_status: document.getElementById("gps-status").textContent,
        websocket_status: document.getElementById("realtime-transport-status").textContent,
        report_status: document.getElementById("report-path").textContent,
        map_status: document.getElementById("map-path").textContent,
        model_status: document.getElementById("model-status").textContent,
        calibration_status: document.getElementById("calibration-status").textContent
      })
    });
    setStatus(payload);
    setDebug(payload);
  }

  function openMapReport() {
    if (lastMapUrl) {
      window.open(lastMapUrl, "_blank", "noopener");
      return;
    }
    setStatus("MAP_NOT_AVAILABLE_YET_NO_GPS_NO_MARKER_OR_SHUTTER_NOT_SENT");
  }

  addClick("ping-btn", async function () {
    const payload = await safeFetchJson("/api/network/health");
    setFieldStatus("server-status", payload.status || "NETWORK_HEALTH_READY");
    setStatus(payload);
    setDebug(payload);
  });
  addClick("gps-btn", requestGps);
  addClick("camera-permission", startCamera);
  addClick("start-camera", startCamera);
  addClick("stop-camera", stopCamera);
  addClick("start-realtime", startRealtimeDetection);
  addClick("stop-realtime", stopRealtimeDetection);
  addClick("capture-frame", captureStillFrame);
  addClick("legacy-shutter-capture", shutterCapture);
  addClick("manual-prediction", runManualPrediction);
  addClick("snapshot-report", sendSnapshotReport);
  addClick("copy-report-link", openReportLink);
  addClick("legacy-open-map-report", openMapReport);
  addClick("debug-coco-overlay", debugCocoOverlay);
  addClick("refresh-tunnel-status", refreshTunnelStatus);
  addClick("refresh-tunnel-status-secondary", refreshTunnelStatus);
  addClick("copy-public-url", copyPublicUrl);
  addClick("open-public-url", openPublicUrl);
  addClick("copy-lan-url", copyLanUrl);
  addClick("failure-recovery-help", failureRecoveryHelp);

  updateSecureContextStatus();
  refreshRuntimeStatus();
})();
