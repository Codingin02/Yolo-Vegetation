
(function () {
  "use strict";

  const sessionMatch = location.pathname.match(/\/plan-c\/capture\/([^/?#]+)/);
  const sessionId = sessionMatch ? decodeURIComponent(sessionMatch[1]) : "";

  let stream = null;
  let gps = null;
  let shotLocked = false;
  let gpsWatchId = null;

  const video = document.getElementById("pcv4-video");
  const canvas = document.getElementById("pcv4-canvas");
  const shutter = document.getElementById("pcv4-shutter");
  const processing = document.getElementById("pcv4-processing");
  const cameraNav = document.getElementById("pcv4-camera-nav");
  const mapNav = document.getElementById("pcv4-map-nav");
  const resultNav = document.getElementById("pcv4-result-nav");

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

  async function stopCamera() {
    if (!stream) return;
    try {
      stream.getTracks().forEach(track => track.stop());
    } catch (_) {}
    stream = null;
  }

  async function startCamera() {
    await stopCamera();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert("Kamera tidak tersedia. Pastikan browser membuka URL HTTPS ngrok dan izin kamera aktif.");
      return;
    }

    const constraintsList = [
      {
        audio: false,
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      },
      {
        audio: false,
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      },
      {
        audio: false,
        video: {
          facingMode: "environment"
        }
      },
      {
        audio: false,
        video: true
      }
    ];

    let lastError = null;

    for (const constraints of constraintsList) {
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        video.muted = true;
        video.playsInline = true;
        video.setAttribute("playsinline", "");
        video.setAttribute("webkit-playsinline", "");
        await video.play();

        const track = stream.getVideoTracks()[0];
        const settings = track && track.getSettings ? track.getSettings() : {};
        logDev("CAMERA", {
          status: "CAMERA_READY",
          width: settings.width || null,
          height: settings.height || null,
          facingMode: settings.facingMode || null
        });
        return;
      } catch (err) {
        lastError = err;
      }
    }

    logDev("CAMERA", {
      status: "CAMERA_FAILED",
      error: lastError ? String(lastError.name + ": " + lastError.message) : "UNKNOWN"
    });

    alert("Kamera gagal dibuka. Cek permission kamera di browser, lalu tekan tombol Kamera di bawah.");
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
      gps_source: "browser_geolocation_fresh"
    };
  }

  function startGps() {
    if (!navigator.geolocation) {
      gps = null;
      logDev("GPS", { status: "GEOLOCATION_NOT_SUPPORTED" });
      return;
    }

    const opts = {
      enableHighAccuracy: true,
      maximumAge: 0,
      timeout: 20000
    };

    function ok(pos) {
      gps = normalizePosition(pos);
      logDev("GPS", gps);
    }

    function fail(err) {
      logDev("GPS", {
        status: "GPS_NOT_READY",
        code: err && err.code ? err.code : null,
        message: err && err.message ? err.message : ""
      });
    }

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

  function waitForGps(ms) {
    return new Promise(resolve => {
      if (gps && Number.isFinite(gps.latitude) && Number.isFinite(gps.longitude)) {
        resolve(gps);
        return;
      }

      let done = false;
      const timer = setTimeout(() => {
        if (!done) {
          done = true;
          resolve(gps);
        }
      }, ms);

      try {
        navigator.geolocation.getCurrentPosition(
          pos => {
            if (done) return;
            done = true;
            clearTimeout(timer);
            gps = normalizePosition(pos);
            logDev("GPS", gps);
            resolve(gps);
          },
          () => {
            if (done) return;
            done = true;
            clearTimeout(timer);
            resolve(gps);
          },
          { enableHighAccuracy: true, maximumAge: 0, timeout: ms }
        );
      } catch (_) {}
    });
  }

  function canvasToBlob(targetCanvas) {
    return new Promise(resolve => {
      targetCanvas.toBlob(blob => resolve(blob), "image/jpeg", 0.92);
    });
  }

  async function takeSnapshot() {
    if (shotLocked) return;
    shotLocked = true;

    try {
      if (!video.videoWidth || !video.videoHeight) {
        throw new Error("CAMERA_FRAME_NOT_READY");
      }

      showProcessing(true);
      shutter.disabled = true;

      await waitForGps(7000);

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const blob = await canvasToBlob(canvas);
      if (!blob) throw new Error("SNAPSHOT_BLOB_EMPTY");

      const form = new FormData();
      const filename = sessionId + ".jpg";

      form.append("session_id", sessionId);
      form.append("point_id", "pohon_sono");
      form.append("operator_note", "");
      form.append("note", "");
      form.append("idempotency_key", "pcv4_" + sessionId + "_" + Date.now());

      form.append("snapshot", blob, filename);
      form.append("image", blob, filename);
      form.append("file", blob, filename);

      if (gps && Number.isFinite(gps.latitude) && Number.isFinite(gps.longitude)) {
        const lat = String(gps.latitude);
        const lon = String(gps.longitude);
        const acc = String(gps.accuracy_m);

        form.append("latitude", lat);
        form.append("longitude", lon);
        form.append("lat", lat);
        form.append("lng", lon);
        form.append("gps_latitude", lat);
        form.append("gps_longitude", lon);
        form.append("accuracy_m", acc);
        form.append("gps_accuracy_m", acc);
        form.append("gps_timestamp_ms", String(gps.timestamp_ms));
        form.append("gps_status", gps.gps_status);
        form.append("gps_source", gps.gps_source);
        form.append("altitude", gps.altitude || "");
        form.append("heading", gps.heading || "");
        form.append("speed", gps.speed || "");
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

      const resultUrl =
        data.result_url ||
        data.redirect_url ||
        data.url ||
        ("/plan-c/processing/" + encodeURIComponent(sessionId));

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
      showProcessing(false);
      alert("Snapshot gagal: " + (err && err.message ? err.message : err));
    }
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

  shutter.addEventListener("click", takeSnapshot);

  if (cameraNav) {
    cameraNav.addEventListener("click", function () {
      startCamera();
      startGps();
    });
  }

  if (mapNav) {
    mapNav.classList.add("disabled");
  }

  if (resultNav) {
    resultNav.classList.add("disabled");
  }

  startCamera();
  startGps();

  window.addEventListener("beforeunload", function () {
    try {
      if (gpsWatchId !== null) navigator.geolocation.clearWatch(gpsWatchId);
    } catch (_) {}
    try {
      if (stream) stream.getTracks().forEach(track => track.stop());
    } catch (_) {}
  });
})();
