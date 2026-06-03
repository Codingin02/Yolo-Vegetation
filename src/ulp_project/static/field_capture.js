(function () {
  const output = document.getElementById("status-output");
  const debug = document.getElementById("network-debug");
  const video = document.getElementById("camera");
  const canvas = document.getElementById("frame");
  const overlayCanvas = document.getElementById("overlay-canvas");
  const submitButton = document.getElementById("upload-btn");
  const startButton = document.getElementById("start-realtime");
  const stopButton = document.getElementById("stop-realtime");
  const snapshotButton = document.getElementById("snapshot-report");
  let capturedBlob = null;
  let inFlight = false;
  let lastSubmitAt = 0;
  let realtimeActive = false;
  let frameInFlight = false;
  let lastFrameSentAt = 0;
  let realtimeTimer = null;
  let gpsTimer = null;
  let realtimeSessionId = "";
  let realtimeSessionToken = "";
  let ws = null;
  let latestGps = { lat: "", lon: "" };
  const debounceMs = 2000;
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

  function updateProtocolStatus() {
    const secure = window.isSecureContext || window.location.protocol === "https:";
    setFieldStatus("protocol-status", secure ? "HTTPS_SECURE" : "HTTP_LAN");
    if (!secure) {
      setFieldStatus("camera-status", "BLOCKED_INSECURE_CONTEXT");
      setFieldStatus("gps-status", "BLOCKED_INSECURE_CONTEXT");
    }
  }

  async function safeFetchJson(endpoint, options) {
    const response = await fetch(endpoint, options);
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

  function captureFingerprint() {
    const bucket = Math.floor(Date.now() / 5000);
    const selected = document.getElementById("image").files[0];
    return [
      document.getElementById("point_id").value,
      bucket,
      selected ? selected.name : capturedBlob ? "captured-frame" : "",
      document.getElementById("lat").value,
      document.getElementById("lon").value
    ].join("|");
  }

  async function startCamera() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setFieldStatus("camera-status", window.isSecureContext ? "NOT_AVAILABLE" : "BLOCKED_INSECURE_CONTEXT");
        setStatus("CAMERA_NOT_AVAILABLE_USE_FILE_UPLOAD_FALLBACK");
        return false;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      video.srcObject = stream;
      setFieldStatus("camera-status", "AVAILABLE");
      setStatus("CAMERA_READY");
      return true;
    } catch (error) {
      const message = String(error);
      const blocked = !window.isSecureContext;
      setFieldStatus("camera-status", blocked ? "BLOCKED_INSECURE_CONTEXT" : "PERMISSION_DENIED");
      setStatus({ status: blocked ? "CAMERA_BLOCKED_INSECURE_CONTEXT" : "CAMERA_PERMISSION_DENIED", message, fallback: "Gunakan upload file foto." });
      return false;
    }
  }

  document.getElementById("open-camera").addEventListener("click", startCamera);

  document.getElementById("capture-frame").addEventListener("click", function () {
    if (!video.videoWidth) {
      setStatus("CAMERA_FRAME_NOT_READY_USE_FILE_UPLOAD_FALLBACK");
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob(function (blob) {
      capturedBlob = blob;
      setFieldStatus("mode-label", "FILE_UPLOAD_FALLBACK");
      setStatus("FRAME_CAPTURED_READY_TO_UPLOAD");
    }, "image/jpeg", 0.82);
  });

  function requestGps() {
    if (!navigator.geolocation) {
      setFieldStatus("gps-status", "SIGNAL_NOT_READY");
      setStatus("GPS_NOT_AVAILABLE_IN_BROWSER");
      return;
    }
    if (!window.isSecureContext) {
      setFieldStatus("gps-status", "BLOCKED_INSECURE_CONTEXT");
    }
    navigator.geolocation.getCurrentPosition(
      function (position) {
        latestGps = { lat: position.coords.latitude.toFixed(7), lon: position.coords.longitude.toFixed(7) };
        document.getElementById("lat").value = latestGps.lat;
        document.getElementById("lon").value = latestGps.lon;
        setFieldStatus("gps-status", "AVAILABLE");
        setStatus("GPS_READY");
      },
      function (error) {
        const blocked = !window.isSecureContext;
        setFieldStatus("gps-status", blocked ? "BLOCKED_INSECURE_CONTEXT" : error.code === 1 ? "PERMISSION_DENIED" : "SIGNAL_NOT_READY");
        setStatus({ status: "GPS_PERMISSION_OR_SIGNAL_NOT_READY", message: String(error.message || error), fallback: "YOLO tetap bisa berjalan; map tidak membuat marker jika GPS kosong." });
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  }

  document.getElementById("gps-btn").addEventListener("click", requestGps);
  document.getElementById("gps-btn-secondary").addEventListener("click", requestGps);

  document.getElementById("ping-btn").addEventListener("click", async function () {
    const payload = await safeFetchJson("/api/network/whoami");
    setDebug(payload);
    setStatus(payload);
  });

  async function createRealtimeSession() {
    const session = await safeFetchJson("/api/realtime/session/new");
    realtimeSessionId = session.session_id || "";
    realtimeSessionToken = session.session_token || "";
    setFieldStatus("realtime-transport-status", "SESSION_READY");
    return session;
  }

  function openRealtimeWebSocket() {
    if (!realtimeSessionId) return false;
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    try {
      ws = new WebSocket(`${scheme}://${window.location.host}/ws/realtime-detect`);
      ws.onopen = function () {
        setFieldStatus("realtime-transport-status", "WEBSOCKET_CONNECTED");
      };
      ws.onmessage = function (event) {
        frameInFlight = false;
        const payload = JSON.parse(event.data);
        handleRealtimeResult(payload);
      };
      ws.onerror = function () {
        setFieldStatus("realtime-transport-status", "WEBSOCKET_ERROR_HTTP_FALLBACK");
      };
      ws.onclose = function () {
        if (realtimeActive) setFieldStatus("realtime-transport-status", "RECONNECTING_HTTP_FALLBACK");
      };
      return true;
    } catch (error) {
      setFieldStatus("realtime-transport-status", "WEBSOCKET_UNAVAILABLE_HTTP_FALLBACK");
      return false;
    }
  }

  async function startRealtimeDetection() {
    realtimeActive = true;
    setFieldStatus("mode-label", "AUTO_YOLO_REALTIME");
    await startCamera();
    await createRealtimeSession();
    openRealtimeWebSocket();
    requestGps();
    gpsTimer = window.setInterval(requestGps, 8000);
    realtimeTimer = window.setInterval(sendRealtimeFrame, requestedIntervalMs);
    setFieldStatus("refresh-interval-display", `${requestedIntervalMs} ms`);
    setStatus("REALTIME_DETECTION_STARTED_LATEST_ONLY_1FPS");
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
      point_id: document.getElementById("point_id").value || "V001_pohon_sono",
      species_hint: document.getElementById("species").value || "pohon_sono",
      asset_type: document.getElementById("asset_type").value || "span",
      gps_lat: document.getElementById("lat").value || latestGps.lat,
      gps_lon: document.getElementById("lon").value || latestGps.lon,
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
      setFieldStatus("realtime-transport-status", "RECONNECTING_WITH_BACKOFF");
      setStatus({ status: "REALTIME_FRAME_SEND_FAILED", message: String(error) });
    }
  }

  function captureFrameBase64() {
    if (!video.videoWidth) return "";
    const maxWidth = 960;
    const scale = Math.min(1, maxWidth / video.videoWidth);
    canvas.width = Math.floor(video.videoWidth * scale);
    canvas.height = Math.floor(video.videoHeight * scale);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.7);
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
    setFieldStatus("model-status", payload.model_status || "MODEL_NOT_READY");
    setFieldStatus("auto-measurement-status", payload.measurement_status || payload.detection_status || "MODEL_NOT_READY");
    setFieldStatus("latest-eta", payload.eta_days !== undefined && payload.eta_days !== null ? `${payload.eta_days} hari / ${payload.eta_months} bulan` : "-");
    setFieldStatus("risk-priority", payload.risk_priority || "-");
    setFieldStatus("clearance-display", payload.selected_clearance_display_m !== undefined && payload.selected_clearance_display_m !== null ? `${payload.selected_clearance_display_m} m` : "-");
    setFieldStatus("distance-zone-status", payload.distance_zone_status || "-");
    drawOverlay(payload.overlay_json || {});
    setDebug(payload);
    setStatus(payload);
  }

  function drawOverlay(overlay) {
    if (!overlayCanvas || !video.videoWidth) return;
    overlayCanvas.width = video.videoWidth;
    overlayCanvas.height = video.videoHeight;
    const ctx = overlayCanvas.getContext("2d");
    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    const boxes = overlay.boxes || [];
    boxes.forEach(function (box) {
      const bbox = box.bbox || [];
      if (bbox.length !== 4) return;
      ctx.strokeStyle = box.color || "#00ff66";
      ctx.lineWidth = 3;
      ctx.strokeRect(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]);
      ctx.fillStyle = ctx.strokeStyle;
      ctx.font = "16px Arial";
      ctx.fillText(`${box.label || "object"} ${box.confidence || ""}`, bbox[0], Math.max(16, bbox[1] - 4));
    });
    if (overlay.safe_zone) {
      ctx.fillStyle = "rgba(255, 255, 255, 0.85)";
      ctx.fillRect(8, 8, 300, 58);
      ctx.fillStyle = "#111";
      ctx.font = "16px Arial";
      ctx.fillText(`Zona 3m: ${overlay.safe_zone.distance_zone_status || "-"}`, 16, 30);
      ctx.fillText(`ETA: ${(overlay.eta_label || {}).eta_days || "-"} hari`, 16, 52);
    }
  }

  snapshotButton.addEventListener("click", async function () {
    if (!realtimeSessionId) {
      setStatus("REALTIME_SESSION_NOT_STARTED");
      return;
    }
    const payload = await safeFetchJson("/api/realtime/report-snapshot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: realtimeSessionId, session_token: realtimeSessionToken, report_trigger: "operator_snapshot" })
    });
    setStatus(payload);
    setDebug(payload);
    if (payload.report_path) setFieldStatus("report-path", payload.report_path);
    if (payload.map_path) setFieldStatus("map-path", payload.map_path);
  });

  startButton.addEventListener("click", startRealtimeDetection);
  stopButton.addEventListener("click", stopRealtimeDetection);

  document.getElementById("upload-btn").addEventListener("click", async function () {
    const now = Date.now();
    if (inFlight || now - lastSubmitAt < debounceMs) {
      setStatus({ status: "SUBMIT_DEBOUNCED", message: "Tunggu minimal 2 detik sebelum submit ulang." });
      return;
    }
    inFlight = true;
    lastSubmitAt = now;
    submitButton.disabled = true;
    submitButton.textContent = "Submitting...";
    const form = new FormData();
    form.append("point_id", document.getElementById("point_id").value);
    form.append("species", document.getElementById("species").value);
    form.append("asset_type", document.getElementById("asset_type").value);
    form.append("clearance_m", document.getElementById("clearance_m").value);
    form.append("growth_rate_m_per_day", document.getElementById("growth_rate_m_per_day").value);
    form.append("tree_height_m", document.getElementById("tree_height_m").value);
    form.append("cable_or_span_height_m", document.getElementById("cable_or_span_height_m").value);
    form.append("asset_height_m", document.getElementById("asset_height_m").value);
    form.append("span_lowest_point_height_m", document.getElementById("span_lowest_point_height_m").value);
    form.append("season", document.getElementById("season").value);
    form.append("rainfall_mm", document.getElementById("rainfall_mm").value);
    form.append("temperature_c", document.getElementById("temperature_c").value);
    form.append("relative_humidity_percent", document.getElementById("relative_humidity_percent").value);
    form.append("lat", document.getElementById("lat").value);
    form.append("lon", document.getElementById("lon").value);
    form.append("timestamp", new Date().toISOString());
    form.append("operator_note", document.getElementById("operator_note").value);
    form.append("network_mode", navigator.onLine ? "same_lan_mode" : "offline_queue_mode");
    form.append("capture_fingerprint", captureFingerprint());
    const selected = document.getElementById("image").files[0];
    if (capturedBlob) {
      form.append("image", capturedBlob, "field_capture_frame.jpg");
    } else if (selected) {
      form.append("image", selected);
    }
    try {
      const payload = await safeFetchJson("/api/field-capture/upload", { method: "POST", body: form });
      if (payload.auto_measurement_status) setFieldStatus("auto-measurement-status", payload.auto_measurement_status);
      if (payload.model_status) setFieldStatus("model-status", payload.model_status);
      if (payload.calibration_status) setFieldStatus("calibration-status", payload.calibration_status);
      if (payload.environmental_data_status) setFieldStatus("environmental-status", payload.environmental_data_status);
      if (payload.eta_days !== undefined && payload.eta_days !== null) setFieldStatus("latest-eta", `${payload.eta_days} hari / ${payload.eta_months} bulan`);
      if (payload.risk_priority) setFieldStatus("risk-priority", payload.risk_priority);
      if (payload.report_path) setFieldStatus("report-path", payload.report_path);
      if (payload.map_path) setFieldStatus("map-path", payload.map_path);
      if (payload.auto_model_status) setFieldStatus("mode-label", payload.auto_model_status === "MODEL_NOT_READY" ? "AUTO_YOLO_NOT_READY" : "AUTO_YOLO_READY_UNVALIDATED");
      setDebug(payload);
      setStatus(payload);
    } catch (error) {
      localStorage.setItem("field_capture_pending_upload", "true");
      setStatus({ status: "OFFLINE_QUEUE_PENDING", message: String(error) });
    } finally {
      inFlight = false;
      submitButton.disabled = false;
      submitButton.textContent = "Submit Inspection";
    }
  });

  updateProtocolStatus();
})();
