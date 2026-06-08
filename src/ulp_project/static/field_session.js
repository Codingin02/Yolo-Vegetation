(() => {
"use strict";

function getOperationalSessionIdFromStartResult(result) {
    return (
        result?.session_id ||
        result?.session?.session_id ||
        result?.data?.session_id ||
        ""
    ).trim();
}

function isOperationalSessionId(value) {
    return typeof value === "string" && /^FS_[A-Za-z0-9_:-]+/.test(value) && !value.startsWith("FS_DEGRADED");
}

function q(sel) {
    return document.querySelector(sel);
}

function getValue(selectors, fallback) {
    for (const sel of selectors) {
        const el = q(sel);
        if (el && typeof el.value === "string" && el.value.trim()) return el.value.trim();
    }
    return fallback || "";
}

async function requestCameraWarmup() {
    if (!navigator.mediaDevices?.getUserMedia) return "CAMERA_API_UNAVAILABLE";
    try {
        const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        s.getTracks().forEach(t => t.stop());
        return "CAMERA_READY";
    } catch (err) {
        return "CAMERA_PERMISSION_REQUIRED";
    }
}

function requestGpsWarmup() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve({ gps_status: "GPS_UNAVAILABLE", gps_source: "BROWSER_UNAVAILABLE" });
            return;
        }
        navigator.geolocation.getCurrentPosition((pos) => {
            resolve({
                gps_status: "GPS_READY",
                gps_source: "BROWSER",
                latitude: pos.coords.latitude,
                longitude: pos.coords.longitude,
                accuracy_m: pos.coords.accuracy,
                timestamp: new Date(pos.timestamp || Date.now()).toISOString(),
            });
        }, (err) => {
            const codeMap = { 1: "GPS_PERMISSION_DENIED", 2: "GPS_POSITION_UNAVAILABLE", 3: "GPS_TIMEOUT" };
            resolve({
                gps_status: codeMap[err.code] || "GPS_NOT_READY",
                gps_source: "BROWSER_ERROR",
                latitude: null,
                longitude: null,
                accuracy_m: null,
                error_message: err.message,
            });
        }, { enableHighAccuracy: true, timeout: 8000, maximumAge: 1000 });
    });
}

async function startFieldSession() {
    const statusEl = q("#status") || q("[data-status]") || q(".status");
    if (statusEl) statusEl.textContent = "Meminta izin kamera dan GPS...";

    const pointId = getValue(["#point_id", "#pointId", "input[name='point_id']", "input[name='pointId']"], "V001_pohon_sono");
    const operatorName = getValue(["#operator_name", "#operatorName", "input[name='operator_name']", "input[name='operatorName']"], "");
    const notes = getValue(["#notes", "textarea[name='notes']"], "");

    sessionStorage.setItem("ulp_point_id", pointId);

    const cameraStatus = await requestCameraWarmup();
    const gpsPayload = await requestGpsWarmup();

    const response = await fetch("/api/field/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
        body: JSON.stringify({
            point_id: pointId,
            operator_name: operatorName,
            notes,
            camera_status: cameraStatus,
            gps: gpsPayload,
            gpsPayload,
            no_fake_gps: true,
            no_fake_detection: true,
            no_fake_clearance: true,
        }),
    });

    const result = await response.json();
    const startedSessionId = getOperationalSessionIdFromStartResult(result);
    if (!isOperationalSessionId(startedSessionId)) {
        if (statusEl) statusEl.textContent = "SESSION_START_FAILED_NO_CAMERA_REDIRECT";
        alert("SESSION_START_FAILED_NO_CAMERA_REDIRECT");
        return;
    }

    sessionStorage.setItem("ulp_active_field_session_id", startedSessionId);
    window.ulpActiveFieldSessionId = startedSessionId;

    const cameraUrl = result.camera_url || `/field-camera?session_id=${encodeURIComponent(startedSessionId)}&nocache=${Date.now()}`;
    location.href = cameraUrl;
}

function bindStartButtons() {
    const explicit = q("#startBtn") || q("#startSessionBtn") || q("[data-start-session]");
    if (explicit) {
        explicit.addEventListener("click", (e) => {
            e.preventDefault();
            startFieldSession().catch(err => {
                alert(`SESSION_START_FAILED: ${err}`);
            });
        });
        return;
    }

    const buttons = Array.from(document.querySelectorAll("button, input[type='button'], input[type='submit']"));
    const startButton = buttons.find((b) => (b.textContent || b.value || "").trim().toLowerCase() === "start");
    if (startButton) {
        startButton.addEventListener("click", (e) => {
            e.preventDefault();
            startFieldSession().catch(err => {
                alert(`SESSION_START_FAILED: ${err}`);
            });
        });
    }
}

document.addEventListener("DOMContentLoaded", bindStartButtons);
window.startFieldSession = startFieldSession;
})();
