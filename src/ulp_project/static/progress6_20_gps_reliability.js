(function () {
  "use strict";

  const VERSION = "progress6_20_gps_reliability_js";
  let lastGoodPosition = null;
  let watchId = null;
  let retryCount = 0;

  function getSessionId() {
    try {
      const url = new URL(window.location.href);
      const q = url.searchParams.get("session_id") || url.searchParams.get("sessionId");
      if (q && q.startsWith("FS_")) return q;

      const m = window.location.pathname.match(/FS_\d{8}_\d{6}_[A-Za-z0-9]+/);
      if (m) return m[0];
    } catch (e) {}
    return "";
  }

  function badge(text) {
    try {
      let el = document.getElementById("progress6-20-gps-badge");
      if (!el) {
        el = document.createElement("div");
        el.id = "progress6-20-gps-badge";
        el.style.position = "fixed";
        el.style.left = "12px";
        el.style.bottom = "76px";
        el.style.zIndex = "99999";
        el.style.padding = "8px 12px";
        el.style.borderRadius = "999px";
        el.style.background = "rgba(0, 65, 42, 0.88)";
        el.style.color = "white";
        el.style.fontSize = "12px";
        el.style.fontWeight = "700";
        el.style.boxShadow = "0 8px 24px rgba(0,0,0,.25)";
        document.body.appendChild(el);
      }
      el.textContent = text;
    } catch (e) {}
  }

  async function sendPosition(position, source) {
    const sessionId = getSessionId();
    if (!sessionId || !position || !position.coords) return;

    const payload = {
      session_id: sessionId,
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
      gps_accuracy_m: position.coords.accuracy,
      gps_status: "GPS_READY_BROWSER_PROGRESS_6_20",
      gps_source: source || "BROWSER_GEOLOCATION",
      source: source || "BROWSER_GEOLOCATION",
      progress6_20_version: VERSION,
      gps: {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        gps_accuracy_m: position.coords.accuracy,
        source: source || "BROWSER_GEOLOCATION"
      },
      coords: {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy
      }
    };

    lastGoodPosition = position;

    try {
      await fetch("/api/field/session/gps-update", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-store"
        },
        body: JSON.stringify(payload),
        keepalive: true
      });

      const acc = Math.round(position.coords.accuracy || 0);
      badge("GPS_READY_" + acc + "M / GPS_EVIDENCE_ONLY");
    } catch (e) {
      badge("GPS_SEND_RETRYING / GPS_EVIDENCE_ONLY");
    }
  }

  function onGpsError(err) {
    const code = err && typeof err.code !== "undefined" ? err.code : "UNKNOWN";
    const label = code === 1 ? "GPS_PERMISSION_DENIED" :
      code === 2 ? "GPS_POSITION_UNAVAILABLE" :
      code === 3 ? "GPS_TIMEOUT" :
      "GPS_ERROR";

    badge(label + " + YOLO_STILL_RUNNING");

    retryCount += 1;
    const delay = Math.min(30000, 2500 + retryCount * 2500);

    window.setTimeout(function () {
      requestOneShot(false);
      requestOneShot(true);
    }, delay);
  }

  function requestOneShot(highAccuracy) {
    if (!navigator.geolocation) {
      badge("GPS_API_NOT_AVAILABLE + YOLO_STILL_RUNNING");
      return;
    }

    const opts = {
      enableHighAccuracy: !!highAccuracy,
      timeout: highAccuracy ? 20000 : 8000,
      maximumAge: highAccuracy ? 15000 : 90000
    };

    navigator.geolocation.getCurrentPosition(
      function (pos) { sendPosition(pos, highAccuracy ? "BROWSER_GPS_HIGH_ACCURACY_RETRY" : "BROWSER_GPS_CACHED_FAST_RETRY"); },
      onGpsError,
      opts
    );
  }

  function startWatch() {
    if (!navigator.geolocation) {
      badge("GPS_API_NOT_AVAILABLE + YOLO_STILL_RUNNING");
      return;
    }

    try {
      if (watchId !== null) navigator.geolocation.clearWatch(watchId);
    } catch (e) {}

    watchId = navigator.geolocation.watchPosition(
      function (pos) { sendPosition(pos, "BROWSER_GPS_WATCH_PROGRESS_6_20"); },
      onGpsError,
      {
        enableHighAccuracy: true,
        timeout: 25000,
        maximumAge: 30000
      }
    );

    badge("GPS_WATCHING + YOLO_STILL_RUNNING");
  }

  function boot() {
    const sessionId = getSessionId();
    if (!sessionId) return;

    requestOneShot(false);
    window.setTimeout(function () { requestOneShot(true); }, 1500);
    window.setTimeout(startWatch, 2500);

    window.setInterval(function () {
      if (!lastGoodPosition) {
        requestOneShot(false);
        requestOneShot(true);
      } else {
        sendPosition(lastGoodPosition, "BROWSER_LAST_GOOD_GPS_CACHE_RESEND");
      }
    }, 15000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
