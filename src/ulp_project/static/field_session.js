(function () {
  const gpsOptions = {
    enableHighAccuracy: true,
    timeout: 15000,
    maximumAge: 0
  };

  const legacyStatusTokens = {
    degradedFallback: "SESSION_API_DEGRADED_FALLBACK_USED"
  };

  const state = {
    session_id: window.localStorage.getItem("field_session_id") || "",
    session_status: "RECORDING_STOPPED",
    baseGpsPosition: null,
    currentGpsPosition: null,
    derivedGps: {
      horizontal_distance_from_tree_m: null,
      gps_accuracy_status: "GPS_ACCURACY_UNKNOWN",
      gps_quality_reason: "GPS_WAITING_PERMISSION",
      movement_status: "GPS_NOT_READY",
      is_distance_reliable: false,
      distance_reliability_status: "DISTANCE_NOT_AVAILABLE"
    },
    visibility_state: document.visibilityState || "visible",
    foreground_recording_status: document.hidden ? "PAGE_HIDDEN_BROWSER_MAY_THROTTLE" : "FOREGROUND_RECORDING_REQUIRED",
    hidden_started_at: "",
    hidden_duration_ms: 0,
    frame_loop_paused_due_to_hidden: false,
    browser_throttle_warning: "",
    gpsWatchId: null,
    cameraStream: null,
    frameTimer: null,
    frameInFlight: false,
    startInFlight: false,
    shutterInFlight: false,
    shutterDone: false,
    mapUrl: "",
    spreadsheetUrl: "",
    frameConsecutiveErrors: 0,
    gpsLastSentAt: 0,
    gpsLastSignature: "",
    frame_process_interval_ms: 1000,
    max_allowed_latency_ms: 3000,
    gpsSamples: [],
    gpsSampleWindowStartedAt: 0,
    baseGpsLocked: false,
    baseGpsLockStatus: "GPS_BASE_NOT_LOCKED",
    wakeLock: null,
    startIdempotencyKey: "",
    sessionRouteFallbackUsed: false,
    latestMeasurement: {},
    latestResult: {},
    latestFrameBase64: "",
    lastError: ""
  };

  function el(id) {
    return document.getElementById(id);
  }

  function text(id, value) {
    const node = el(id);
    if (node) node.textContent = value === undefined || value === null || value === "" ? "-" : value;
  }

  function value(id) {
    const node = el(id);
    return node ? node.value : "";
  }

  function setValue(id, next) {
    const node = el(id);
    if (node) node.value = next === undefined || next === null ? "" : next;
  }

  function currentUrlMode() {
    const host = window.location.hostname;
    const isLocal = host === "localhost" || host === "127.0.0.1" || host === "::1";
    if (window.location.protocol === "https:") return "HTTPS_PUBLIC_READY";
    if (isLocal) return "LOCALHOST_DEBUG_ONLY";
    return "LAN_HTTP_DEBUG_ONLY";
  }

  function secureContextStatus() {
    return window.isSecureContext ? "SECURE_CONTEXT_OK" : "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED";
  }

  function requireSecureFieldContext() {
    const mode = currentUrlMode();
    if (mode === "LAN_HTTP_DEBUG_ONLY" && !window.isSecureContext) {
      handleError("INSECURE_CONTEXT_CAMERA_GPS_BLOCKED_OPEN_HTTPS_TUNNEL", "Buka Public HTTPS URL. Kamera dan GPS membutuhkan HTTPS.");
      return false;
    }
    return true;
  }

  function gpsFromPosition(position) {
    return {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
      altitude: position.coords.altitude,
      altitudeAccuracy: position.coords.altitudeAccuracy,
      heading: position.coords.heading,
      speed: position.coords.speed,
      timestamp: new Date(position.timestamp || Date.now()).toISOString(),
      source: "GPS_SOURCE_BROWSER"
    };
  }

  function isValidCoordinatePair(gps) {
    if (!gps) return false;
    const lat = Number(gps.latitude);
    const lon = Number(gps.longitude);
    return Number.isFinite(lat) && Number.isFinite(lon) && !(lat === 0 && lon === 0) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
  }

  function rememberGpsSample(gps) {
    if (!state.gpsSampleWindowStartedAt) state.gpsSampleWindowStartedAt = Date.now();
    if (isValidCoordinatePair(gps)) state.gpsSamples.push(gps);
    if (state.gpsSamples.length > 24) state.gpsSamples = state.gpsSamples.slice(-24);
    const best = selectBestGpsSample(state.gpsSamples);
    if (best && !state.baseGpsLocked) {
      state.baseGpsPosition = best;
      const elapsed = Date.now() - state.gpsSampleWindowStartedAt;
      if (state.gpsSamples.length >= 5 || elapsed >= 8000) {
        state.baseGpsLocked = true;
        const accuracy = Number(best.accuracy);
        if (Number.isFinite(accuracy) && accuracy <= 5) {
          state.baseGpsLockStatus = "GPS_BASE_LOCKED_BEST_SAMPLE";
        } else if (Number.isFinite(accuracy) && accuracy <= 10) {
          state.baseGpsLockStatus = "GPS_BASE_LOCKED_LOW_ACCURACY_LIMITED";
        } else {
          state.baseGpsLockStatus = "GPS_BASE_NOT_RELIABLE_SAVE_EVIDENCE_ONLY";
        }
      } else {
        state.baseGpsLockStatus = "GPS_BASE_PROVISIONAL_WAITING_FOR_5_SAMPLES_OR_8S";
      }
    }
    text("gps-base-lock-status", state.baseGpsLockStatus);
  }

  function selectBestGpsSample(samples) {
    const valid = (samples || []).filter(isValidCoordinatePair);
    if (!valid.length) return null;
    return valid.slice().sort(function (a, b) {
      const aa = Number.isFinite(Number(a.accuracy)) ? Number(a.accuracy) : 999999;
      const ba = Number.isFinite(Number(b.accuracy)) ? Number(b.accuracy) : 999999;
      if (aa !== ba) return aa - ba;
      return String(b.timestamp || "").localeCompare(String(a.timestamp || ""));
    })[0];
  }

  function requestHighAccuracyGps() {
    if (!requireSecureFieldContext()) return Promise.reject(new Error("INSECURE_CONTEXT_CAMERA_GPS_BLOCKED_OPEN_HTTPS_TUNNEL"));
    if (!navigator.geolocation) return Promise.reject(new Error("BROWSER_GEOLOCATION_API_UNAVAILABLE"));
    text("glass-gps-status", "GPS_WAITING_PERMISSION");
    text("gps-permission-status", "GPS_WAITING_PERMISSION");
    return new Promise(function (resolve, reject) {
      navigator.geolocation.getCurrentPosition(
        function (position) {
          const gps = gpsFromPosition(position);
          rememberGpsSample(gps);
          if (!state.baseGpsPosition) state.baseGpsPosition = gps;
          state.currentGpsPosition = gps;
          updateGpsQuality();
          resolve(gps);
        },
        function (error) {
          const status = error && error.code === 1 ? "GPS_PERMISSION_DENIED" : error && error.code === 3 ? "GPS_TIMEOUT" : "GPS_NOT_READY";
          handleError(status, error && error.message ? error.message : String(error));
          reject(error);
        },
        gpsOptions
      );
    });
  }

  function startGpsWatch() {
    if (!navigator.geolocation) {
      handleError("BROWSER_GEOLOCATION_API_UNAVAILABLE", "Browser tidak menyediakan navigator.geolocation.");
      return null;
    }
    stopGpsWatch();
    state.gpsWatchId = navigator.geolocation.watchPosition(
      function (position) {
        state.currentGpsPosition = gpsFromPosition(position);
        rememberGpsSample(state.currentGpsPosition);
        updateGpsQuality();
        sendGpsUpdate(state.currentGpsPosition, false);
      },
      function (error) {
        const status = error && error.code === 1 ? "GPS_PERMISSION_DENIED" : error && error.code === 3 ? "GPS_TIMEOUT" : "GPS_NOT_READY";
        handleError(status, error && error.message ? error.message : String(error));
      },
      gpsOptions
    );
    return state.gpsWatchId;
  }

  function stopGpsWatch() {
    if (state.gpsWatchId !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(state.gpsWatchId);
    }
    state.gpsWatchId = null;
  }

  async function startCamera() {
    if (!requireSecureFieldContext()) return false;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      handleError("CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT", "Browser tidak menyediakan navigator.mediaDevices.getUserMedia.");
      return false;
    }
    const video = el("camera");
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          frameRate: { ideal: 30, max: 30 }
        },
        audio: false
      });
    } catch (firstError) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      } catch (secondError) {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }
    }
    state.cameraStream = stream;
    if (video) video.srcObject = state.cameraStream;
    text("glass-camera-status", "CAMERA_READY");
    text("camera-status", "CAMERA_READY");
    text("camera-permission-status", "CAMERA_READY");
    return true;
  }

  async function requestWakeLock() {
    if (!("wakeLock" in navigator) || !navigator.wakeLock || !navigator.wakeLock.request) return;
    try {
      state.wakeLock = await navigator.wakeLock.request("screen");
      text("wake-lock-status", "WAKE_LOCK_REQUESTED");
    } catch (error) {
      text("wake-lock-status", "WAKE_LOCK_NOT_AVAILABLE");
    }
  }

  async function releaseWakeLock() {
    if (state.wakeLock && state.wakeLock.release) {
      try {
        await state.wakeLock.release();
      } catch (error) {
        // Browser may release wake lock implicitly when page visibility changes.
      }
    }
    state.wakeLock = null;
  }

  function stopCamera() {
    if (state.cameraStream && state.cameraStream.getTracks) {
      state.cameraStream.getTracks().forEach(function (track) {
        track.stop();
      });
    }
    state.cameraStream = null;
    const video = el("camera");
    if (video) video.srcObject = null;
    text("glass-camera-status", "CAMERA_STOPPED");
    text("camera-status", "CAMERA_STOPPED");
  }

  async function startSession() {
    if (state.startInFlight) {
      showToast("START_SESSION_ALREADY_IN_PROGRESS");
      return;
    }
    state.startInFlight = true;
    const startButton = el("session-start");
    if (startButton) startButton.disabled = true;
    try {
      text("glass-url-mode", currentUrlMode());
      if (!requireSecureFieldContext()) return;
      await requestWakeLock();
      try {
        await requestHighAccuracyGps();
      } catch (gpsError) {
        handleError("GPS_INITIAL_FIX_TIMEOUT_SESSION_CONTINUES", String(gpsError));
      }
      startGpsWatch();
      await startCamera();
      state.startIdempotencyKey = state.startIdempotencyKey || `START_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
      const payload = collectSessionPayload();
      const result = await postJson("/api/field/session/start", payload);
      state.session_id = result.session_id || result.session && result.session.session_id || state.session_id;
      if (!state.session_id) {
        throw new Error("FIELD_SESSION_START_RETURNED_EMPTY_SESSION_ID");
      }
      if (state.session_id) window.localStorage.setItem("field_session_id", state.session_id);
      state.session_status = "RECORDING_ACTIVE";
      text("session-id", state.session_id);
      if (document.body && document.body.dataset.page === "field-capture-preflight") {
        const target = `/field-camera?session_id=${encodeURIComponent(state.session_id || "")}`;
        window.location.assign(target);
        return;
      }
      document.body.classList.add("camera-mode-active");
      startFrameLoop();
      renderStatus();
    } catch (error) {
      handleError("FIELD_SESSION_START_FAILED", String(error));
    } finally {
      state.startInFlight = false;
      if (startButton) startButton.disabled = false;
    }
  }

  async function stopSession() {
    stopGpsWatch();
    stopCamera();
    stopFrameLoop();
    await releaseWakeLock();
    state.session_status = "RECORDING_STOPPED";
    document.body.classList.remove("camera-mode-active");
    try {
      await postJson("/api/field/session/stop", collectSessionPayload());
    } catch (error) {
      handleError("FIELD_SESSION_STOP_FAILED_JSON_GUARD", String(error));
    }
    renderStatus();
  }

  async function homeFromCamera() {
    try {
      await stopSession();
    } finally {
      window.location.assign("/field-capture");
    }
  }

  function startFrameLoop() {
    stopFrameLoop();
    state.frameTimer = window.setInterval(sendFrame, state.frame_process_interval_ms);
    text("frame-interval-status", `${state.frame_process_interval_ms} ms`);
  }

  function stopFrameLoop() {
    if (state.frameTimer) window.clearInterval(state.frameTimer);
    state.frameTimer = null;
  }

  function updateGpsQuality() {
    const current = state.currentGpsPosition;
    const base = state.baseGpsPosition;
    const distance = computeHaversineMeters(base, current);
    const currentAccuracy = current && Number.isFinite(Number(current.accuracy)) ? Number(current.accuracy) : null;
    const baseAccuracy = base && Number.isFinite(Number(base.accuracy)) ? Number(base.accuracy) : null;
    let gps_accuracy_status = "GPS_ACCURACY_UNKNOWN";
    let gps_quality_reason = "GPS_ACCURACY_UNKNOWN";
    if (currentAccuracy !== null) {
      if (currentAccuracy <= 5) {
        gps_accuracy_status = "GPS_ACCURACY_GOOD";
        gps_quality_reason = "GPS_ACCURACY_LE_5M";
      } else if (currentAccuracy <= 10) {
        gps_accuracy_status = "GPS_ACCURACY_MEDIUM";
        gps_quality_reason = "GPS_ACCURACY_5_TO_10M";
      } else {
        gps_accuracy_status = "GPS_ACCURACY_LOW";
        gps_quality_reason = "GPS_ACCURACY_GT_10M";
      }
    }
    let distance_reliability_status = "DISTANCE_NOT_AVAILABLE";
    let is_distance_reliable = false;
    if (distance !== null) {
      if (baseAccuracy === null || currentAccuracy === null) {
        distance_reliability_status = "GPS_ACCURACY_UNKNOWN";
      } else if (Math.max(baseAccuracy, currentAccuracy) > distance) {
        distance_reliability_status = "DISTANCE_NOT_RELIABLE_ACCURACY_GT_DISTANCE";
      } else if (distance < 1) {
        distance_reliability_status = "DISTANCE_TOO_SMALL_FOR_GPS_RELIABILITY";
      } else if (distance >= 2 * Math.max(baseAccuracy, currentAccuracy)) {
        distance_reliability_status = "DISTANCE_REASONABLY_RELIABLE_FOR_FIELD_EVIDENCE";
        is_distance_reliable = true;
      } else {
        distance_reliability_status = "DISTANCE_ESTIMATE_WEAK_FOR_FIELD_EVIDENCE";
      }
    }
    state.derivedGps = {
      horizontal_distance_from_tree_m: distance,
      gps_accuracy_status,
      gps_quality_reason,
      movement_status: distance && distance > 0.5 ? "MOVED_FROM_TREE_BASE" : "AT_TREE_BASE",
      is_distance_reliable,
      distance_reliability_status
    };
    renderStatus();
  }

  function computeHaversineMeters(base, current) {
    if (!base || !current) return null;
    const lat1 = Number(base.latitude);
    const lon1 = Number(base.longitude);
    const lat2 = Number(current.latitude);
    const lon2 = Number(current.longitude);
    if (![lat1, lon1, lat2, lon2].every(Number.isFinite)) return null;
    const radiusM = 6371000;
    const phi1 = lat1 * Math.PI / 180;
    const phi2 = lat2 * Math.PI / 180;
    const dPhi = (lat2 - lat1) * Math.PI / 180;
    const dLambda = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dPhi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2) ** 2;
    return Math.round(radiusM * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)) * 1000) / 1000;
  }

  async function sendGpsUpdate(gps, setBase) {
    if (!state.session_id) return;
    const signature = [
      gps && gps.latitude,
      gps && gps.longitude,
      gps && gps.accuracy,
      Boolean(setBase)
    ].join("|");
    const now = Date.now();
    if (!setBase && signature === state.gpsLastSignature && now - state.gpsLastSentAt < 1500) return;
    if (!setBase && now - state.gpsLastSentAt < 1200) return;
    state.gpsLastSignature = signature;
    state.gpsLastSentAt = now;
    await postJson("/api/field/session/gps-update", {
      ...gps,
      ...visibilityPayload(),
      session_id: state.session_id,
      set_base: Boolean(setBase)
    });
  }

  async function sendFrame() {
    if (state.frameInFlight) return;
    if (!state.session_id) {
      stopFrameLoop();
      handleError("FIELD_SESSION_ID_REQUIRED", "Session ID kosong. Kembali ke Home lalu tekan Start ulang.");
      return;
    }
    const video = el("camera");
    if (!video || !video.videoWidth) {
      renderOverlay("CAMERA_FRAME_NOT_READY");
      return;
    }
    state.frameInFlight = true;
    const started = performance.now();
    try {
      const image = captureFrameBase64(0.58);
      const result = await postJson("/api/field/session/frame", {
        session_id: state.session_id,
        point_id: value("point_id") || "V001_pohon_sono",
        image_base64: image,
        frame_image_base64: image,
        timestamp_client_ms: Date.now(),
        gps: state.currentGpsPosition,
        current_latitude: state.currentGpsPosition && state.currentGpsPosition.latitude,
        current_longitude: state.currentGpsPosition && state.currentGpsPosition.longitude,
        current_accuracy_m: state.currentGpsPosition && state.currentGpsPosition.accuracy,
        ...visibilityPayload()
      });
      state.frameConsecutiveErrors = 0;
      if (state.frame_process_interval_ms > 1000 && document.visibilityState !== "hidden") {
        state.frame_process_interval_ms = 1000;
        startFrameLoop();
      }
      const latency = Math.round(performance.now() - started);
      if (latency > state.max_allowed_latency_ms) {
        state.frame_process_interval_ms = Math.min(3000, Math.max(2000, state.frame_process_interval_ms + 1000));
        text("last-error-status", "HIGH_LATENCY_REDUCED_FPS");
        startFrameLoop();
      }
      state.latestMeasurement = result.measurement_result || {};
      state.latestResult = result;
      renderOverlay(result);
      renderStatus();
    } catch (error) {
      state.frameConsecutiveErrors += 1;
      if (String(error).includes("FIELD_SESSION_ID_REQUIRED")) {
        stopFrameLoop();
      } else if (state.frameConsecutiveErrors >= 3) {
        state.frame_process_interval_ms = 3000;
        text("last-error-status", "FRAME_BACKOFF_ACTIVE");
        startFrameLoop();
      }
      handleError("FIELD_SESSION_FRAME_FAILED", String(error));
    } finally {
      state.frameInFlight = false;
    }
  }

  async function shutterCapture() {
    press3D(el("shutter-capture"));
    safeVibrate(20);
    if (!state.session_id) {
      showToast("FIELD_SESSION_ID_REQUIRED");
      return { status: "FIELD_SESSION_ID_REQUIRED" };
    }
    if (state.shutterInFlight) {
      handleError("DUPLICATE_SHUTTER_IGNORED_CLIENT_IN_FLIGHT", "Shutter sedang menyimpan. Tunggu toast selesai.");
      return { status: "DUPLICATE_SHUTTER_IGNORED_CLIENT_IN_FLIGHT" };
    }
    state.shutterInFlight = true;
    setShutterDisabled(true);
    const image = captureFrameBase64(0.72);
    const idempotencyKey = `SHUTTER_${state.session_id || "NOSESSION"}_${Date.now()}`;
    const payload = {
      session_id: state.session_id,
      point_id: value("point_id") || "V001_pohon_sono",
      operator_name: value("operator_name"),
      notes: value("operator_note"),
      image_base64: image,
      base_gps: state.baseGpsPosition,
      current_gps: state.currentGpsPosition,
      gps_samples: state.gpsSamples,
      base_gps_lock_status: state.baseGpsLockStatus,
      latest_measurement: state.latestMeasurement,
      model_status: state.latestResult.model_status || "MODEL_NOT_READY",
      idempotency_key: idempotencyKey,
      source_mode: "LIVE_OPERATOR",
      ...visibilityPayload()
    };
    let result;
    try {
      result = await postJson("/api/field/session/shutter", payload);
    } catch (error) {
      handleError("FIELD_SESSION_SHUTTER_FAILED", String(error));
      return { status: "FIELD_SESSION_SHUTTER_FAILED", message: String(error) };
    } finally {
      state.shutterInFlight = false;
      setShutterDisabled(false);
    }
    if (result.status === "FIELD_SESSION_SHUTTER_SAVED" || result.status === "DUPLICATE_SHUTTER_IGNORED") {
      state.shutterDone = true;
      state.mapUrl = result.map_url || state.mapUrl || (state.session_id ? `/field-map/session/${encodeURIComponent(state.session_id)}` : "");
      state.spreadsheetUrl = result.spreadsheet_url || result.result_page_url || state.spreadsheetUrl || (state.session_id ? `/field-spreadsheet/session/${encodeURIComponent(state.session_id)}` : "");
      setEvidenceButtonsEnabled(true);
      shutterPulse();
    }
    if (result.report_csv_url) text("report-path", result.report_csv_url);
    if (result.map_url) text("map-path", result.map_url);
    if (result.report_id) text("report-id", result.report_id);
    showToast(result.status || "FIELD_SESSION_SHUTTER_SAVED");
    renderStatus();
    return result;
  }

  function setShutterDisabled(disabled) {
    const button = el("shutter-capture");
    if (button) {
      button.disabled = Boolean(disabled);
      button.setAttribute("aria-busy", disabled ? "true" : "false");
    }
  }

  function setEvidenceButtonsEnabled(enabled) {
    ["open-map-report", "session-result"].forEach(function (id) {
      const button = el(id);
      if (button) {
        button.disabled = !enabled;
        button.setAttribute("aria-disabled", enabled ? "false" : "true");
      }
    });
  }

  function showToast(message) {
    const toast = el("field-toast");
    if (!toast) return;
    toast.hidden = false;
    toast.textContent = message;
    window.clearTimeout(showToast._timer);
    showToast._timer = window.setTimeout(function () {
      toast.hidden = true;
    }, 2400);
  }

  function captureFrameBase64(quality) {
    const video = el("camera");
    const canvas = el("frame");
    if (!video || !canvas || !video.videoWidth) return "";
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    state.latestFrameBase64 = canvas.toDataURL("image/jpeg", quality || 0.65);
    return state.latestFrameBase64;
  }

  function renderStatus() {
    text("glass-url-mode", currentUrlMode());
    text("glass-recording-status", state.session_status);
    text("glass-gps-status", state.derivedGps.gps_accuracy_status);
    text("glass-model-status", state.latestResult.model_status || "MODEL_NOT_READY");
    text("session-id", state.session_id);
    text("foreground-recording-status", state.foreground_recording_status);
    text("visibility-state", state.visibility_state);
    text("hidden-duration-ms", state.hidden_duration_ms);
    text("browser-throttle-warning", state.browser_throttle_warning);
    text("horizontal-distance-from-tree", state.derivedGps.horizontal_distance_from_tree_m);
    text("distance-reliability-status", state.derivedGps.distance_reliability_status);
    text("gps-quality-reason", state.derivedGps.gps_quality_reason);
    text("movement-status", state.derivedGps.movement_status);
    text("gps-base-lock-status", state.baseGpsLockStatus);
    text("camera-session-chip", state.session_id ? state.session_id.slice(-8) : "-");
    text("camera-frame-chip", state.frameConsecutiveErrors >= 3 ? "FRAME_BACKOFF_ACTIVE" : (state.latestResult.status || "FRAME_WAITING"));
    text("camera-shutter-chip", state.shutterDone ? "SHUTTER_DONE" : "SHUTTER_REQUIRED");
    text("camera-gps-chip", state.derivedGps.gps_accuracy_status);
    text("camera-distance-chip", state.derivedGps.horizontal_distance_from_tree_m === null ? "DISTANCE_NOT_AVAILABLE" : `${state.derivedGps.horizontal_distance_from_tree_m} m`);
    text("gps-status", state.derivedGps.gps_accuracy_status === "GPS_ACCURACY_UNKNOWN" ? "GPS_WAITING_PERMISSION" : "GPS_READY");
    text("gps-source-status", state.currentGpsPosition ? "GPS_SOURCE_BROWSER" : "GPS_NOT_PROVIDED");
    text("gps-accuracy-status", state.currentGpsPosition && state.currentGpsPosition.accuracy ? `${Number(state.currentGpsPosition.accuracy).toFixed(1)} m` : "-");
    const warning = el("foreground-warning");
    if (warning) {
      warning.hidden = state.foreground_recording_status !== "PAGE_HIDDEN_BROWSER_MAY_THROTTLE";
      warning.textContent = state.browser_throttle_warning || "FOREGROUND_RECORDING_REQUIRED: jika tab hidden, layar mati, atau browser diminimize, proses web bisa throttled.";
    }
  }

  function renderOverlay(payload) {
    const canvas = el("overlay-canvas");
    if (!canvas) return;
    const video = el("camera");
    canvas.width = video && video.videoWidth ? video.videoWidth : canvas.clientWidth || 640;
    canvas.height = video && video.videoHeight ? video.videoHeight : canvas.clientHeight || 360;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "rgba(14, 124, 102, 0.78)";
    ctx.font = "22px Arial";
    const status = typeof payload === "string" ? payload : payload && payload.model_status === "MODEL_NOT_READY" ? "MODEL_NOT_READY_NO_FAKE_DETECTION" : "FIELD_RESULT_PROVISIONAL";
    ctx.fillText(status || "FIELD_SESSION_READY", 18, 34);
    const detections = payload && payload.detections ? payload.detections : [];
    ctx.strokeStyle = "#00d084";
    ctx.lineWidth = 3;
    detections.forEach(function (detection) {
      const box = detection.bbox || detection.box || {};
      const x = box.x || box.x1 || 0;
      const y = box.y || box.y1 || 0;
      const w = box.width || (box.x2 ? box.x2 - x : 0);
      const h = box.height || (box.y2 ? box.y2 - y : 0);
      ctx.strokeRect(x, y, w, h);
    });
  }

  function handleError(status, message) {
    state.lastError = `${status}: ${message}`;
    text("last-error-status", state.lastError.slice(0, 160));
    text("glass-recording-status", status);
    const output = el("status-output");
    if (output) output.textContent = JSON.stringify({ status, message }, null, 2);
  }

  function collectSessionPayload() {
    const isPreflight = document.body && document.body.dataset.page === "field-capture-preflight";
    return {
      session_id: isPreflight ? "" : state.session_id,
      point_id: value("point_id") || "V001_pohon_sono",
      operator_name: value("operator_name"),
      notes: value("operator_note"),
      secure_context_status: secureContextStatus(),
      current_url_mode: currentUrlMode(),
      public_tunnel_status: (el("public-tunnel-status") || {}).textContent || "PUBLIC_TUNNEL_NOT_RUNNING",
      camera_status: "CAMERA_READY",
      base_gps: state.baseGpsPosition,
      current_gps: state.currentGpsPosition,
      gps_samples: state.gpsSamples,
      base_gps_lock_status: state.baseGpsLockStatus,
      idempotency_key: state.startIdempotencyKey,
      ...visibilityPayload()
    };
  }

  function visibilityPayload() {
    return {
      visibility_state: state.visibility_state,
      foreground_recording_status: state.foreground_recording_status,
      hidden_started_at: state.hidden_started_at,
      hidden_duration_ms: state.hidden_duration_ms,
      frame_loop_paused_due_to_hidden: state.frame_loop_paused_due_to_hidden,
      browser_throttle_warning: state.browser_throttle_warning
    };
  }

  function handleVisibilityChange() {
    state.visibility_state = document.visibilityState || (document.hidden ? "hidden" : "visible");
    if (document.hidden) {
      state.hidden_started_at = new Date().toISOString();
      state.foreground_recording_status = "PAGE_HIDDEN_BROWSER_MAY_THROTTLE";
      state.browser_throttle_warning = "Halaman tidak aktif. Browser dapat membatasi kamera/timer/GPS. Buka kembali halaman untuk recording stabil.";
      state.frame_loop_paused_due_to_hidden = true;
      state.frame_process_interval_ms = 3000;
      if (state.frameTimer) startFrameLoop();
    } else {
      if (state.hidden_started_at) {
        const started = Date.parse(state.hidden_started_at);
        if (Number.isFinite(started)) state.hidden_duration_ms += Math.max(0, Date.now() - started);
      }
      state.hidden_started_at = "";
      state.visibility_state = "visible";
      state.foreground_recording_status = "FOREGROUND_RECORDING_ACTIVE";
      state.browser_throttle_warning = "";
      state.frame_loop_paused_due_to_hidden = false;
      if (state.frame_process_interval_ms >= 3000) state.frame_process_interval_ms = 1000;
      if (state.frameTimer) startFrameLoop();
    }
    renderStatus();
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.status || response.statusText);
    return data;
  }

  function bind(id, fn) {
    const node = el(id);
    if (node) node.addEventListener("click", fn);
  }

  function openSessionMap() {
    press3D(el("open-map-report"));
    safeVibrate(12);
    if (!state.shutterDone || !state.mapUrl) {
      showToast("Jepret dulu untuk membuat evidence map");
      return;
    }
    window.location.assign(state.mapUrl);
  }

  function openSessionSpreadsheet() {
    press3D(el("session-result"));
    safeVibrate(12);
    if (!state.shutterDone || !state.spreadsheetUrl) {
      showToast("Jepret dulu untuk membuat spreadsheet evidence");
      return;
    }
    window.location.assign(state.spreadsheetUrl);
  }

  function openManualInput() {
    press3D(el("session-manual-input"));
    safeVibrate(12);
    const target = state.session_id ? `/field-manual-input?session_id=${encodeURIComponent(state.session_id)}` : "/field-manual-input";
    window.location.assign(target);
  }

  function safeVibrate(ms) {
    if (navigator.vibrate) {
      try {
        navigator.vibrate(ms);
      } catch (error) {
        // Haptic feedback is optional.
      }
    }
  }

  function press3D(button) {
    if (!button || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    button.classList.remove("press-3d-active");
    window.requestAnimationFrame(function () {
      button.classList.add("press-3d-active");
      window.setTimeout(function () {
        button.classList.remove("press-3d-active");
      }, 180);
    });
  }

  function shutterPulse() {
    const button = el("shutter-capture");
    if (!button || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    button.classList.remove("shutter-pulse-active");
    window.requestAnimationFrame(function () {
      button.classList.add("shutter-pulse-active");
      window.setTimeout(function () {
        button.classList.remove("shutter-pulse-active");
      }, 420);
    });
  }

  window.FieldSession = {
    state,
    startSession,
    stopSession,
    homeFromCamera,
    requestHighAccuracyGps,
    startGpsWatch,
    stopGpsWatch,
    startCamera,
    stopCamera,
    startFrameLoop,
    stopFrameLoop,
    updateGpsQuality,
    computeHaversineMeters,
    sendGpsUpdate,
    sendFrame,
    shutterCapture,
    renderStatus,
    renderOverlay,
    handleError,
    handleVisibilityChange,
    openSessionMap,
    openSessionSpreadsheet,
    openManualInput,
    safeVibrate,
    press3D
  };

  bind("session-start", startSession);
  bind("session-stop", stopSession);
  bind("session-home", homeFromCamera);
  bind("shutter-capture", shutterCapture);
  bind("open-map-report", openSessionMap);
  bind("session-result", openSessionSpreadsheet);
  bind("session-manual-input", openManualInput);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  setEvidenceButtonsEnabled(false);
  renderStatus();
})();
