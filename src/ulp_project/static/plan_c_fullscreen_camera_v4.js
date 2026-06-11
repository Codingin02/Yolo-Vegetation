(function () {
  "use strict";

  const sessionMatch = location.pathname.match(/\/plan-c\/capture\/([^/?#]+)/);
  const sessionId = sessionMatch ? decodeURIComponent(sessionMatch[1]) : "";

  let stream = null;
  let shotLocked = false;
  let gpsWatchId = null;
  let treeAnchorGps = null;
  let lastGps = null;
  let gpsTrack = [];
  let rearDevices = [];
  let rearDeviceIndex = 0;
  let treeAnchorSaved = false;

  const video = document.getElementById("pcv4-video");
  const canvas = document.getElementById("pcv4-canvas");
  const shutter = document.getElementById("pcv4-shutter");
  const processing = document.getElementById("pcv4-processing");
  const cameraNav = document.getElementById("pcv4-camera-nav");
  const mapNav = document.getElementById("pcv4-map-nav");
  const resultNav = document.getElementById("pcv4-result-nav");
  const anchorModal = document.getElementById("pcv4-anchor-modal");
  const anchorYes = document.getElementById("pcv4-anchor-yes");
  const anchorNo = document.getElementById("pcv4-anchor-no");
  const galleryButton = document.getElementById("pcv4-gallery");
  const galleryInput = document.getElementById("pcv4-gallery-input");
  const lensButton = document.getElementById("pcv4-lens");

  if (!sessionId || !video || !canvas || !shutter) return;

  sessionStorage.setItem("PLAN_C_LAST_SESSION_ID", sessionId);

  function logDev(name, data) {
    try {
      sessionStorage.setItem("PLAN_C_DEV_" + name, JSON.stringify(data || {}));
    } catch (_) {}
  }

  function showProcessing(show) {
    if (!processing) return;
    processing.classList.toggle("hidden", !show);
  }

  function stopCamera() {
    if (!stream) return;
    try {
      stream.getTracks().forEach(track => track.stop());
    } catch (_) {}
    stream = null;
  }

  function cameraBaseConstraints(deviceId) {
    if (deviceId) {
      return {
        audio: false,
        video: {
          deviceId: { exact: deviceId },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      };
    }
    return {
      audio: false,
      video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      }
    };
  }

  async function requestCamera(constraints) {
    const media = await navigator.mediaDevices.getUserMedia(constraints);
    stream = media;
    video.srcObject = stream;
    video.muted = true;
    video.playsInline = true;
    video.setAttribute("playsinline", "");
    video.setAttribute("webkit-playsinline", "");
    await video.play();
    const track = stream.getVideoTracks()[0];
    const settings = track && track.getSettings ? track.getSettings() : {};
    logDev("CAMERA", {
      status: "CAMERA_STREAM_OPEN",
      width: settings.width || null,
      height: settings.height || null,
      facingMode: settings.facingMode || null,
      deviceId: settings.deviceId || null
    });
  }

  function isNormalRearCamera(device) {
    const label = String(device.label || "").toLowerCase();
    if (!label) return false;
    const looksRear = /(back|rear|environment|belakang|kamera belakang)/.test(label);
    const looksUltra = /(ultra|ultrawide|wide angle|0\.5x|0,5x)/.test(label);
    return looksRear && !looksUltra;
  }

  async function refreshRearDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      rearDevices = devices.filter(item => item.kind === "videoinput" && isNormalRearCamera(item));
      logDev("CAMERA_DEVICES", {
        normal_rear_count: rearDevices.length,
        labels: devices
          .filter(item => item.kind === "videoinput")
          .map(item => ({ label: item.label || "", selected_normal_rear: isNormalRearCamera(item) }))
      });
    } catch (err) {
      rearDevices = [];
      logDev("CAMERA_DEVICES", { status: "ENUMERATE_FAILED", error: String(err && err.message ? err.message : err) });
    }
  }

  async function startCamera(deviceId) {
    stopCamera();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      logDev("CAMERA", { status: "CAMERA_API_UNAVAILABLE" });
      alert("Kamera tidak tersedia. Pastikan memakai browser modern lewat HTTPS.");
      return;
    }

    const constraintsList = [
      cameraBaseConstraints(deviceId),
      {
        audio: false,
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      },
      { audio: false, video: { facingMode: "environment" } },
      { audio: false, video: true }
    ];

    let lastError = null;
    for (const constraints of constraintsList) {
      try {
        await requestCamera(constraints);
        await refreshRearDevices();
        return;
      } catch (err) {
        lastError = err;
        stopCamera();
      }
    }

    logDev("CAMERA", {
      status: lastError && lastError.name === "NotAllowedError" ? "CAMERA_PERMISSION_DENIED" : "CAMERA_FAILED",
      error: lastError ? String(lastError.name + ": " + lastError.message) : "UNKNOWN"
    });
    alert("Kamera gagal dibuka. Cek izin kamera pada browser, lalu tekan Kamera.");
  }

  async function switchLens() {
    if (!rearDevices.length) {
      await refreshRearDevices();
    }
    if (rearDevices.length) {
      rearDeviceIndex = (rearDeviceIndex + 1) % rearDevices.length;
      await startCamera(rearDevices[rearDeviceIndex].deviceId);
      return;
    }
    await startCamera("");
  }

  function normalizePosition(pos) {
    return {
      latitude: Number(pos.coords.latitude),
      longitude: Number(pos.coords.longitude),
      accuracy_m: Number(pos.coords.accuracy || 9999),
      altitude: pos.coords.altitude == null ? "" : String(pos.coords.altitude),
      heading: pos.coords.heading == null ? "" : String(pos.coords.heading),
      speed: pos.coords.speed == null ? "" : String(pos.coords.speed),
      timestamp_ms: Date.now(),
      gps_status: "GPS_FRESH_BROWSER",
      gps_source: "GPS_SOURCE_BROWSER"
    };
  }

  function haversineMeters(a, b) {
    if (!a || !b) return null;
    if (!Number.isFinite(a.latitude) || !Number.isFinite(a.longitude) || !Number.isFinite(b.latitude) || !Number.isFinite(b.longitude)) return null;
    const radius = 6371000;
    const toRad = value => value * Math.PI / 180;
    const dLat = toRad(b.latitude - a.latitude);
    const dLon = toRad(b.longitude - a.longitude);
    const lat1 = toRad(a.latitude);
    const lat2 = toRad(b.latitude);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
    return 2 * radius * Math.asin(Math.sqrt(h));
  }

  function addGpsPoint(point) {
    lastGps = point;
    gpsTrack.push(point);
    if (gpsTrack.length > 120) gpsTrack = gpsTrack.slice(-120);
    if (!treeAnchorGps && Number.isFinite(point.latitude) && Number.isFinite(point.longitude)) {
      treeAnchorGps = point;
      saveTreeAnchor(point);
    }
    logDev("GPS", buildGpsSummary());
  }

  function bestRecentGps() {
    const usable = gpsTrack.filter(item => Number.isFinite(item.latitude) && Number.isFinite(item.longitude));
    if (!usable.length) return lastGps;
    return usable.slice(-12).sort((a, b) => Number(a.accuracy_m || 9999) - Number(b.accuracy_m || 9999))[0];
  }

  function buildGpsSummary(shutterGps) {
    const best = shutterGps || bestRecentGps();
    const distance = treeAnchorGps && best ? haversineMeters(treeAnchorGps, best) : null;
    const accuracy = best && Number.isFinite(best.accuracy_m) ? Number(best.accuracy_m) : null;
    const status = accuracy === null
      ? "GPS_NOT_READY"
      : accuracy > 10
        ? "GPS_DISTANCE_LOW_CONFIDENCE"
        : "GPS_DISTANCE_ACCEPTED";
    return {
      track_point_count: gpsTrack.length,
      first_timestamp_ms: gpsTrack.length ? gpsTrack[0].timestamp_ms : null,
      last_timestamp_ms: gpsTrack.length ? gpsTrack[gpsTrack.length - 1].timestamp_ms : null,
      gps_accuracy_m: accuracy,
      gps_distance_from_anchor_m: distance === null ? null : Number(distance.toFixed(2)),
      estimated_steps_from_anchor: distance === null ? null : Number((distance / 0.75).toFixed(1)),
      gps_distance_status: status,
      gps_source: best && best.gps_source ? best.gps_source : "GPS_SOURCE_UNAVAILABLE"
    };
  }

  function startGpsWatch() {
    if (!navigator.geolocation) {
      logDev("GPS", { status: "GEOLOCATION_NOT_SUPPORTED" });
      return;
    }

    const opts = { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 };
    const ok = pos => addGpsPoint(normalizePosition(pos));
    const fail = err => {
      logDev("GPS", {
        status: err && err.code === 1 ? "GPS_PERMISSION_DENIED" : "GPS_NOT_READY",
        code: err && err.code ? err.code : null,
        message: err && err.message ? err.message : ""
      });
    };

    try {
      navigator.geolocation.getCurrentPosition(ok, fail, opts);
    } catch (err) {
      fail(err);
    }

    try {
      if (gpsWatchId !== null) navigator.geolocation.clearWatch(gpsWatchId);
      gpsWatchId = navigator.geolocation.watchPosition(ok, fail, opts);
    } catch (err) {
      fail(err);
    }
  }

  async function saveTreeAnchor(point) {
    if (treeAnchorSaved || !point) return;
    treeAnchorSaved = true;
    try {
      await fetch("/api/plan-c/session/tree-anchor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({
          session_id: sessionId,
          latitude: point.latitude,
          longitude: point.longitude,
          gps_accuracy_m: point.accuracy_m,
          gps_source: point.gps_source,
          tree_anchor_gps: point
        })
      });
    } catch (err) {
      treeAnchorSaved = false;
      logDev("TREE_ANCHOR", { status: "TREE_ANCHOR_SAVE_FAILED", error: String(err && err.message ? err.message : err) });
    }
  }

  function waitForGps(ms) {
    return new Promise(resolve => {
      const existing = bestRecentGps();
      if (existing && Number.isFinite(existing.latitude) && Number.isFinite(existing.longitude)) {
        resolve(existing);
        return;
      }

      if (!navigator.geolocation) {
        resolve(null);
        return;
      }

      let done = false;
      const timer = setTimeout(() => {
        if (!done) {
          done = true;
          resolve(bestRecentGps());
        }
      }, ms);

      try {
        navigator.geolocation.getCurrentPosition(
          pos => {
            if (done) return;
            done = true;
            clearTimeout(timer);
            const point = normalizePosition(pos);
            addGpsPoint(point);
            resolve(point);
          },
          () => {
            if (done) return;
            done = true;
            clearTimeout(timer);
            resolve(bestRecentGps());
          },
          { enableHighAccuracy: true, maximumAge: 0, timeout: ms }
        );
      } catch (_) {
        clearTimeout(timer);
        resolve(bestRecentGps());
      }
    });
  }

  function canvasToBlob(targetCanvas) {
    return new Promise(resolve => {
      targetCanvas.toBlob(blob => resolve(blob), "image/jpeg", 0.92);
    });
  }

  async function blobFromCamera() {
    if (!video.videoWidth || !video.videoHeight) {
      throw new Error("CAMERA_FRAME_NOT_READY");
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await canvasToBlob(canvas);
    if (!blob) throw new Error("SNAPSHOT_BLOB_EMPTY");
    return blob;
  }

  function appendJson(form, key, value) {
    form.append(key, JSON.stringify(value || {}));
  }

  async function submitSnapshot(blob, source) {
    if (shotLocked) return;
    shotLocked = true;
    showProcessing(true);
    shutter.disabled = true;
    if (galleryButton) galleryButton.disabled = true;
    if (lensButton) lensButton.disabled = true;

    try {
      const shutterGps = await waitForGps(5000);
      const summary = buildGpsSummary(shutterGps);
      const form = new FormData();
      const filename = sessionId + "_" + source + ".jpg";

      form.append("session_id", sessionId);
      form.append("point_id", "pohon_sono");
      form.append("operator_note", "");
      form.append("note", "");
      form.append("capture_source", source);
      form.append("idempotency_key", "pcv5_" + sessionId + "_" + source + "_" + Date.now());
      form.append("snapshot", blob, filename);
      form.append("image", blob, filename);
      form.append("file", blob, filename);

      appendJson(form, "tree_anchor_gps", treeAnchorGps);
      appendJson(form, "shutter_gps", shutterGps);
      appendJson(form, "gps_track_summary", summary);
      appendJson(form, "gps_track_points", gpsTrack.slice(-24));
      form.append("gps_accuracy_m", summary.gps_accuracy_m == null ? "" : String(summary.gps_accuracy_m));
      form.append("gps_distance_from_anchor_m", summary.gps_distance_from_anchor_m == null ? "" : String(summary.gps_distance_from_anchor_m));
      form.append("estimated_steps_from_anchor", summary.estimated_steps_from_anchor == null ? "" : String(summary.estimated_steps_from_anchor));
      form.append("gps_source", summary.gps_source);
      form.append("gps_distance_status", summary.gps_distance_status);

      if (shutterGps && Number.isFinite(shutterGps.latitude) && Number.isFinite(shutterGps.longitude)) {
        form.append("latitude", String(shutterGps.latitude));
        form.append("longitude", String(shutterGps.longitude));
        form.append("lat", String(shutterGps.latitude));
        form.append("lng", String(shutterGps.longitude));
        form.append("accuracy_m", String(shutterGps.accuracy_m));
        form.append("gps_status", shutterGps.gps_status);
      } else {
        form.append("gps_status", "GPS_NOT_READY");
        form.append("gps_source", "GPS_SOURCE_UNAVAILABLE");
      }

      const resp = await fetch("/api/plan-c/session/snapshot", {
        method: "POST",
        body: form,
        cache: "no-store"
      });
      const text = await resp.text();
      let data = {};
      try { data = JSON.parse(text); } catch (_) {}

      if (!resp.ok) {
        throw new Error(data.status || data.error || ("HTTP_" + resp.status));
      }

      const resultUrl = data.result_url || data.redirect_url || data.url || ("/plan-c/processing/" + encodeURIComponent(sessionId));
      const finalResultUrl = "/plan-c/result/" + encodeURIComponent(sessionId);
      sessionStorage.setItem("PLAN_C_LAST_RESULT_URL", finalResultUrl);
      if (resultNav) {
        resultNav.classList.remove("disabled");
        resultNav.outerHTML = '<a class="pcv4-nav-item active" href="' + finalResultUrl + '">Result</a>';
      }
      window.location.href = resultUrl;
    } catch (err) {
      shotLocked = false;
      shutter.disabled = false;
      if (galleryButton) galleryButton.disabled = false;
      if (lensButton) lensButton.disabled = false;
      showProcessing(false);
      alert("Snapshot gagal: " + (err && err.message ? err.message : err));
    }
  }

  async function takeSnapshot() {
    const blob = await blobFromCamera();
    await submitSnapshot(blob, "camera");
  }

  async function startNewCameraSession() {
    try {
      const resp = await fetch("/api/plan-c/session/start", { method: "POST", cache: "no-store" });
      const data = await resp.json();
      const sid = data.session_id || data.session || (data.result && data.result.session_id);
      if (sid) {
        window.location.href = "/plan-c/capture/" + encodeURIComponent(sid);
        return;
      }
    } catch (_) {}
    window.location.href = "/plan-c";
  }

  async function bootAfterAnchorConfirm() {
    if (anchorModal) anchorModal.classList.add("hidden");
    startGpsWatch();
    await startCamera("");
  }

  shutter.addEventListener("click", takeSnapshot);

  if (galleryButton && galleryInput) {
    galleryButton.addEventListener("click", () => galleryInput.click());
    galleryInput.addEventListener("change", async () => {
      const file = galleryInput.files && galleryInput.files[0];
      if (!file) return;
      await submitSnapshot(file, "gallery");
    });
  }

  if (lensButton) {
    lensButton.addEventListener("click", switchLens);
  }

  if (anchorNo) {
    anchorNo.addEventListener("click", () => { window.location.href = "/plan-c"; });
  }

  if (anchorYes) {
    anchorYes.addEventListener("click", bootAfterAnchorConfirm);
  }

  if (cameraNav) {
    cameraNav.addEventListener("click", startNewCameraSession);
  }

  if (mapNav) mapNav.classList.add("disabled");
  if (resultNav) resultNav.classList.add("disabled");

  window.addEventListener("beforeunload", function () {
    try {
      if (gpsWatchId !== null) navigator.geolocation.clearWatch(gpsWatchId);
    } catch (_) {}
    stopCamera();
  });
})();
