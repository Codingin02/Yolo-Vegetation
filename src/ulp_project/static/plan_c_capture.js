(function () {
  const shell = document.querySelector(".capture-shell");
  const sessionId = shell ? shell.dataset.sessionId : "";
  const video = document.getElementById("cameraPreview");
  const canvas = document.getElementById("snapshotCanvas");
  const shutterButton = document.getElementById("shutterButton");
  const retryButton = document.getElementById("retryButton");
  const anchorButton = document.getElementById("anchorButton");
  const overlay = document.getElementById("loadingOverlay");
  const statusEls = {
    camera: document.getElementById("cameraStatus"),
    gps: document.getElementById("gpsStatus"),
    snapshot: document.getElementById("snapshotStatus"),
    server: document.getElementById("serverStatus"),
  };
  let stream = null;
  let latestPosition = null;
  let latestGpsStatus = "GPS_NOT_READY";
  let uploadInFlight = false;

  function setStatus(name, text) {
    if (statusEls[name]) statusEls[name].textContent = text;
  }

  async function startCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("camera", "CAMERA_API_UNAVAILABLE");
      return;
    }
    stopCamera();
    const constraints = [
      { video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false },
      { video: { facingMode: "environment" }, audio: false },
      { video: true, audio: false },
    ];
    let lastError = null;
    for (const constraint of constraints) {
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraint);
        video.srcObject = stream;
        setStatus("camera", "Camera ready");
        return;
      } catch (error) {
        lastError = error;
      }
    }
    setStatus("camera", cameraErrorStatus(lastError));
  }

  function stopCamera() {
    if (!stream) return;
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }

  function cameraErrorStatus(error) {
    const name = error && error.name ? error.name : "";
    if (name === "NotAllowedError" || name === "SecurityError") return "CAMERA_PERMISSION_DENIED";
    if (name === "NotFoundError") return "CAMERA_NOT_FOUND";
    if (name === "NotReadableError") return "CAMERA_NOT_READABLE";
    return "CAMERA_NOT_READY";
  }

  function readGps() {
    if (!navigator.geolocation) {
      latestGpsStatus = "GPS_API_UNAVAILABLE";
      setStatus("gps", latestGpsStatus);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        latestPosition = position;
        latestGpsStatus = "GPS_READY";
        setStatus("gps", "GPS ready");
      },
      (error) => {
        latestPosition = null;
        latestGpsStatus = gpsErrorStatus(error);
        setStatus("gps", latestGpsStatus);
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 15000 }
    );
  }

  function gpsErrorStatus(error) {
    if (!error) return "GPS_NOT_READY";
    if (error.code === error.PERMISSION_DENIED) return "GPS_PERMISSION_DENIED";
    if (error.code === error.TIMEOUT) return "GPS_TIMEOUT";
    return "GPS_NOT_READY";
  }

  function gpsPayload() {
    if (!latestPosition) return { gps_status: latestGpsStatus };
    return {
      latitude: latestPosition.coords.latitude,
      longitude: latestPosition.coords.longitude,
      gps_accuracy_m: latestPosition.coords.accuracy,
      gps_status: "GPS_READY",
      gps_source: "GPS_SOURCE_BROWSER",
    };
  }

  async function saveAnchor() {
    setStatus("server", "Server...");
    const payload = { session_id: sessionId, ...gpsPayload() };
    const response = await fetch("/api/plan-c/session/tree-anchor", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    setStatus("server", data.status || "Server");
  }

  function setBusy(value) {
    shutterButton.disabled = value;
    retryButton.disabled = value;
    anchorButton.disabled = value;
    overlay.hidden = !value;
  }

  async function takeSnapshot() {
    if (uploadInFlight) return;
    if (!video.videoWidth || !video.videoHeight) {
      setStatus("snapshot", "Snapshot pending");
      return;
    }
    uploadInFlight = true;
    setBusy(true);
    setStatus("snapshot", "Snapshot...");
    const idempotencyKey = generateIdempotencyKey();
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(async (blob) => {
      if (!blob) {
        setStatus("snapshot", "Snapshot failed");
        uploadInFlight = false;
        setBusy(false);
        return;
      }
      const form = new FormData();
      form.append("session_id", sessionId);
      form.append("idempotency_key", idempotencyKey);
      form.append("point_id", "pohon_sono");
      form.append("snapshot", blob, "snapshot.jpg");
      Object.entries(gpsPayload()).forEach(([key, value]) => form.append(key, value));
      const manualClearance = document.getElementById("manualClearance").value;
      const manualTreeHeight = document.getElementById("manualTreeHeight").value;
      const manualDistance = document.getElementById("manualDistance").value;
      if (manualClearance) form.append("manual_clearance_m", manualClearance);
      if (manualTreeHeight) form.append("manual_tree_height_m", manualTreeHeight);
      if (manualDistance) form.append("manual_distance_m", manualDistance);
      try {
        setStatus("server", "Upload...");
        const response = await fetch("/api/plan-c/session/snapshot", { method: "POST", body: form });
        const data = await response.json();
        if (!response.ok) throw new Error(data.status || "UPLOAD_FAILED");
        setStatus("server", "Processing");
        window.location.href = `/plan-c/processing/${sessionId}`;
      } catch (error) {
        setStatus("server", error.message);
        uploadInFlight = false;
        setBusy(false);
      }
    }, "image/jpeg", 0.92);
  }

  retryButton.addEventListener("click", () => {
    setStatus("snapshot", "Snapshot");
    setStatus("server", "Server");
    if (!uploadInFlight) {
      startCamera();
      readGps();
    }
  });
  anchorButton.addEventListener("click", saveAnchor);
  shutterButton.addEventListener("click", takeSnapshot);
  startCamera();
  readGps();

  function generateIdempotencyKey() {
    if (window.crypto && window.crypto.randomUUID) {
      return `${sessionId}:${window.crypto.randomUUID()}`;
    }
    const random = Math.random().toString(36).slice(2);
    return `${sessionId}:${Date.now()}:${random}`;
  }
})();
