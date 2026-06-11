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

  function setStatus(name, text) {
    if (statusEls[name]) statusEls[name].textContent = text;
  }

  async function startCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      video.srcObject = stream;
      setStatus("camera", "Camera ready");
    } catch (error) {
      setStatus("camera", "Camera blocked");
    }
  }

  function readGps() {
    if (!navigator.geolocation) {
      setStatus("gps", "GPS unavailable");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        latestPosition = position;
        setStatus("gps", "GPS ready");
      },
      () => {
        setStatus("gps", "GPS pending");
      },
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 8000 }
    );
  }

  function gpsPayload() {
    if (!latestPosition) return {};
    return {
      latitude: latestPosition.coords.latitude,
      longitude: latestPosition.coords.longitude,
      gps_accuracy_m: latestPosition.coords.accuracy,
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
    if (!video.videoWidth || !video.videoHeight) {
      setStatus("snapshot", "Snapshot pending");
      return;
    }
    setBusy(true);
    setStatus("snapshot", "Snapshot...");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(async (blob) => {
      if (!blob) {
        setStatus("snapshot", "Snapshot failed");
        setBusy(false);
        return;
      }
      const form = new FormData();
      form.append("session_id", sessionId);
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
        setBusy(false);
      }
    }, "image/jpeg", 0.92);
  }

  retryButton.addEventListener("click", () => {
    setStatus("snapshot", "Snapshot");
    setStatus("server", "Server");
  });
  anchorButton.addEventListener("click", saveAnchor);
  shutterButton.addEventListener("click", takeSnapshot);
  startCamera();
  readGps();
})();
