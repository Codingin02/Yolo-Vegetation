(function () {
  const output = document.getElementById("status-output");
  const debug = document.getElementById("network-debug");
  const video = document.getElementById("camera");
  const canvas = document.getElementById("frame");
  const submitButton = document.getElementById("upload-btn");
  let capturedBlob = null;
  let inFlight = false;
  let lastSubmitAt = 0;
  const debounceMs = 2000;

  function setStatus(payload) {
    output.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  }

  function setDebug(payload) {
    debug.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  }

  function setFieldStatus(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
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

  document.getElementById("open-camera").addEventListener("click", async function () {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setFieldStatus("camera-status", window.isSecureContext ? "NOT_AVAILABLE" : "BLOCKED_INSECURE_CONTEXT");
        setStatus("CAMERA_NOT_AVAILABLE_USE_FILE_UPLOAD_FALLBACK");
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      video.srcObject = stream;
      setFieldStatus("camera-status", "AVAILABLE");
      setFieldStatus("mode-label", "FILE_UPLOAD_FALLBACK");
      setStatus("CAMERA_READY");
    } catch (error) {
      const message = String(error);
      const blocked = !window.isSecureContext;
      setFieldStatus("camera-status", blocked ? "BLOCKED_INSECURE_CONTEXT" : "PERMISSION_DENIED");
      setStatus({ status: blocked ? "CAMERA_BLOCKED_INSECURE_CONTEXT" : "CAMERA_PERMISSION_DENIED", message, fallback: "Gunakan upload file foto." });
    }
  });

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
    navigator.geolocation.getCurrentPosition(
      function (position) {
        document.getElementById("lat").value = position.coords.latitude.toFixed(7);
        document.getElementById("lon").value = position.coords.longitude.toFixed(7);
        setFieldStatus("gps-status", "AVAILABLE");
        setStatus("GPS_READY");
      },
      function (error) {
        const blocked = !window.isSecureContext;
        setFieldStatus("gps-status", blocked ? "BLOCKED_INSECURE_CONTEXT" : error.code === 1 ? "PERMISSION_DENIED" : "SIGNAL_NOT_READY");
        setStatus({ status: "GPS_PERMISSION_OR_SIGNAL_NOT_READY", message: String(error.message || error), fallback: "Isi latitude/longitude manual jika tersedia." });
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
