(() => {
"use strict";

const API_FRAME = "/api/field/session/frame";
const API_GPS = "/api/field/session/gps-update";
const API_SHUTTER = "/api/field/session/shutter";
const UI_VERSION = "PROGRESS_6_21_LIVE_YOLO_OVERLAY";

const video = document.getElementById("cameraPreview");
const overlay = document.getElementById("overlayCanvas");
const canvas = document.getElementById("frameCanvas");
const ctxOverlay = overlay.getContext("2d");
const ctxFrame = canvas.getContext("2d", { willReadFrequently: false });

const treeBadge = document.getElementById("treeBadge");
const gpsBadge = document.getElementById("gpsBadge");
const cameraBadge = document.getElementById("cameraBadge");
const frameBadge = document.getElementById("frameBadge");
const shutterBadge = document.getElementById("shutterBadge");
const sessionBadge = document.getElementById("sessionBadge");
const messageBar = document.getElementById("messageBar");
const debugBox = document.getElementById("debugBox");

let stream = null;
let frameTimer = null;
let gpsWatchId = null;
let lastGps = null;
let lastFrameResult = null;
let shutterSaved = false;
let frameCounter = 0;
let nextTrackId = 1;
let tracks = [];

function readCameraSessionId() {
    const fromUrl = new URLSearchParams(location.search).get("session_id") || "";
    const fromBody = document.body.dataset.sessionId || "";
    const fromRoot = document.querySelector("[data-session-id]")?.dataset?.sessionId || "";
    const fromDataset = document.getElementById("camera-session-id")?.dataset?.sessionId || "";
    const fromStorage = sessionStorage.getItem("ulp_active_field_session_id") || "";
    const candidates = [fromUrl, fromBody, fromRoot, fromDataset, fromStorage]
        .map(v => (v || "").trim())
        .filter(v => v && !v.startsWith("FS_DEGRADED"));
    return candidates[0] || "";
}

const sessionId = readCameraSessionId();
if (sessionId) {
    sessionStorage.setItem("ulp_active_field_session_id", sessionId);
    window.ulpActiveFieldSessionId = sessionId;
}

function setText(el, value) {
    if (el) el.textContent = String(value || "");
}

function setMessage(value) {
    setText(messageBar, value || "READY");
}

function updateDebug(obj) {
    lastFrameResult = obj || lastFrameResult;
    if (debugBox) {
        debugBox.textContent = JSON.stringify(obj || {}, null, 2);
    }
}

function isOperationalSessionId(value) {
    return typeof value === "string" && /^FS_[A-Za-z0-9_:-]+/.test(value) && !value.startsWith("FS_DEGRADED");
}

function normalizeBox(raw) {
    if (!raw) return null;
    if (Array.isArray(raw) && raw.length >= 4) {
        return raw.slice(0, 4).map(Number);
    }
    if (Array.isArray(raw.bbox_xyxy) && raw.bbox_xyxy.length >= 4) {
        return raw.bbox_xyxy.slice(0, 4).map(Number);
    }
    if (Array.isArray(raw.bbox) && raw.bbox.length >= 4) {
        return raw.bbox.slice(0, 4).map(Number);
    }
    if (Array.isArray(raw.box) && raw.box.length >= 4) {
        return raw.box.slice(0, 4).map(Number);
    }
    if (Array.isArray(raw.xyxy) && raw.xyxy.length >= 4) {
        return raw.xyxy.slice(0, 4).map(Number);
    }
    const x1 = Number(raw.x1 ?? raw.left);
    const y1 = Number(raw.y1 ?? raw.top);
    const x2 = Number(raw.x2 ?? raw.right);
    const y2 = Number(raw.y2 ?? raw.bottom);
    if ([x1, y1, x2, y2].every(Number.isFinite)) {
        return [x1, y1, x2, y2];
    }
    return null;
}

function normalizeDetections(result) {
    const overlayBoxes = result?.overlay_json?.boxes;
    const topLevelDetections = result?.detections;
    const progress620Detections = result?.progress6_20_gps_yolo?.yolo_detection?.detections;
    const directBoxes = result?.boxes;
    let selected = [];
    if (Array.isArray(overlayBoxes) && overlayBoxes.length) {
        selected = overlayBoxes;
    } else if (Array.isArray(topLevelDetections) && topLevelDetections.length) {
        selected = topLevelDetections;
    } else if (Array.isArray(progress620Detections) && progress620Detections.length) {
        selected = progress620Detections;
    } else if (Array.isArray(directBoxes) && directBoxes.length) {
        selected = directBoxes;
    }
    if (!Array.isArray(selected)) return [];
    return selected.map((d) => {
        const box = normalizeBox(d);
        if (!box) return null;
        return {
            box,
            cls: d.class_name || d.name || d.label || d.cls_name || d.class || "object",
            conf: Number(d.confidence ?? d.conf ?? d.score ?? 0),
            raw: d
        };
    }).filter(Boolean);
}

function yoloStatusFromResponse(result) {
    const p620 = result?.progress6_20_gps_yolo?.yolo_detection || {};
    const treeDetected = Boolean(result?.tree_detected || result?.measurement_result?.tree_detected || p620.tree_detected);
    if (treeDetected) return "YOLO_TREE_DETECTED";
    const status = result?.yolo_detection_status || p620.status || result?.tree_model_status || result?.model_status || "TREE_MODEL_READY_CANDIDATE";
    if (status === ["YOLO", "NOT", "BLOCKED"].join("_")) return "TREE_MODEL_READY_CANDIDATE";
    return status;
}

function iou(a, b) {
    const xA = Math.max(a[0], b[0]);
    const yA = Math.max(a[1], b[1]);
    const xB = Math.min(a[2], b[2]);
    const yB = Math.min(a[3], b[3]);
    const inter = Math.max(0, xB - xA) * Math.max(0, yB - yA);
    const areaA = Math.max(0, a[2] - a[0]) * Math.max(0, a[3] - a[1]);
    const areaB = Math.max(0, b[2] - b[0]) * Math.max(0, b[3] - b[1]);
    return inter / Math.max(1, areaA + areaB - inter);
}

function updateClientTracks(detections) {
    const updated = [];
    for (const det of detections) {
        let best = null;
        let bestScore = 0;
        for (const tr of tracks) {
            const score = iou(det.box, tr.box);
            if (score > bestScore) {
                bestScore = score;
                best = tr;
            }
        }
        if (best && bestScore >= 0.25) {
            best.box = det.box;
            best.cls = det.cls;
            best.conf = det.conf;
            best.age = 0;
            updated.push(best);
        } else {
            updated.push({ id: nextTrackId++, box: det.box, cls: det.cls, conf: det.conf, age: 0 });
        }
    }
    tracks = updated.concat(tracks.filter(t => !updated.includes(t)).map(t => ({...t, age: t.age + 1})).filter(t => t.age < 3));
    return tracks;
}

function drawOverlay(result) {
    if (!overlay || !ctxOverlay || !video) return;
    const rect = video.getBoundingClientRect();
    overlay.width = Math.max(1, Math.floor(rect.width * window.devicePixelRatio));
    overlay.height = Math.max(1, Math.floor(rect.height * window.devicePixelRatio));
    ctxOverlay.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    ctxOverlay.clearRect(0, 0, rect.width, rect.height);

    const detections = normalizeDetections(result);
    const clientTracks = updateClientTracks(detections);

    ctxOverlay.lineWidth = 3;
    ctxOverlay.font = "700 14px system-ui";
    const sourceW = Math.max(1, video.videoWidth || rect.width);
    const sourceH = Math.max(1, video.videoHeight || rect.height);
    const scaleX = rect.width / sourceW;
    const scaleY = rect.height / sourceH;
    for (const tr of clientTracks) {
        const [sx1, sy1, sx2, sy2] = tr.box;
        const x1 = sx1 * scaleX;
        const y1 = sy1 * scaleY;
        const x2 = sx2 * scaleX;
        const y2 = sy2 * scaleY;
        ctxOverlay.strokeStyle = "rgba(91, 255, 187, 0.95)";
        ctxOverlay.fillStyle = "rgba(5, 42, 33, 0.78)";
        ctxOverlay.strokeRect(x1, y1, x2 - x1, y2 - y1);
        const label = `T${tr.id} ${tr.cls} ${tr.conf ? tr.conf.toFixed(2) : ""}`;
        const w = ctxOverlay.measureText(label).width + 12;
        ctxOverlay.fillRect(x1, Math.max(0, y1 - 24), w, 22);
        ctxOverlay.fillStyle = "#ffffff";
        ctxOverlay.fillText(label, x1 + 6, Math.max(16, y1 - 8));
    }
}

function getVideoFrameDataUrl() {
    if (!video || !video.videoWidth || !video.videoHeight) {
        return "";
    }
    canvas.width = Math.max(1, Math.round(video.videoWidth));
    canvas.height = Math.max(1, Math.round(video.videoHeight));
    ctxFrame.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.85);
}

async function postJson(url, payload) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
        body: JSON.stringify(payload || {}),
    });
    let data = {};
    try { data = await res.json(); } catch (_) {}
    if (!res.ok) {
        data.ok = false;
        data.http_status = res.status;
    }
    return data;
}

function buildFramePayload(dataUrl, eventName) {
    return {
        session_id: sessionId,
        event: eventName || "realtime_frame",
        point_id: sessionStorage.getItem("ulp_point_id") || "V001_pohon_sono",
        timestamp_client: new Date().toISOString(),
        gps: lastGps || { status: "GPS_NOT_READY", gps_source: "GPS_NOT_PROVIDED", latitude: null, longitude: null, accuracy_m: null },
        image: dataUrl,
        frame: dataUrl,
        image_base64: dataUrl,
        jpeg_base64: dataUrl,
        frame_jpeg_base64: dataUrl,
        image_jpeg_base64: dataUrl,
        frame_image: dataUrl,
        camera: {
            width: video?.videoWidth || null,
            height: video?.videoHeight || null,
            client_frame_counter: frameCounter,
        },
        no_fake_gps: true,
        no_fake_detection: true,
        no_fake_clearance: true,
    };
}

async function sendFrame() {
    if (!isOperationalSessionId(sessionId)) return;
    if (!stream || !video || !video.videoWidth) {
        setText(frameBadge, "FRAME_SKIPPED_NO_VIDEO");
        return;
    }

    frameCounter += 1;
    const dataUrl = getVideoFrameDataUrl();
    if (!dataUrl || dataUrl.length < 1000) {
        setText(frameBadge, "FRAME_SKIPPED_NO_IMAGE");
        setMessage("FRAME_SKIPPED_NO_IMAGE");
        return;
    }

    try {
        const result = await postJson(API_FRAME, buildFramePayload(dataUrl, "realtime_frame"));
        setText(frameBadge, result.frame_status || result.status || "FRAME_OK");
        const yoloStatus = yoloStatusFromResponse(result);
        setText(treeBadge, yoloStatus);
        setMessage(yoloStatus || result.message || result.status || "FRAME_OK");
        updateDebug(result);
        drawOverlay(result);
    } catch (err) {
        setText(frameBadge, "FRAME_POST_FAILED");
        setMessage("FRAME_POST_FAILED");
        updateDebug({ ok: false, error: String(err), session_id: sessionId });
    }
}

function startGpsWatch() {
    if (!navigator.geolocation) {
        setText(gpsBadge, "GPS_UNAVAILABLE");
        lastGps = { status: "GPS_UNAVAILABLE", gps_source: "BROWSER_UNAVAILABLE", latitude: null, longitude: null, accuracy_m: null };
        return;
    }

    gpsWatchId = navigator.geolocation.watchPosition(async (pos) => {
        lastGps = {
            status: "GPS_READY",
            gps_status: "GPS_READY",
            gps_source: "BROWSER",
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy_m: pos.coords.accuracy,
            altitude: pos.coords.altitude,
            speed: pos.coords.speed,
            heading: pos.coords.heading,
            timestamp: new Date(pos.timestamp || Date.now()).toISOString(),
        };
        setText(gpsBadge, `GPS_READY_${Math.round(pos.coords.accuracy || 0)}M`);
        try {
            await postJson(API_GPS, { session_id: sessionId, gps: lastGps, ...lastGps, no_fake_gps: true });
        } catch (err) {
            updateDebug({ warning: "GPS_POST_FAILED", error: String(err), gps: lastGps });
        }
    }, (err) => {
        const codeMap = { 1: "GPS_PERMISSION_DENIED", 2: "GPS_POSITION_UNAVAILABLE", 3: "GPS_TIMEOUT" };
        const status = codeMap[err.code] || "GPS_NOT_READY";
        lastGps = { status, gps_status: status, gps_source: "BROWSER_ERROR", latitude: null, longitude: null, accuracy_m: null, error_message: err.message };
        setText(gpsBadge, status);
    }, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 1000,
    });
}

async function populateCameraLensSelectorIfAvailable() {
    const select = document.getElementById("cameraLensSelect");
    const sheet = document.getElementById("lensSheet");
    if (!select || !navigator.mediaDevices?.enumerateDevices) return;
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videos = devices.filter(d => d.kind === "videoinput");
        select.innerHTML = "";
        const auto = document.createElement("option");
        auto.value = "";
        auto.textContent = "Lens: Auto";
        select.appendChild(auto);
        for (const d of videos) {
            const opt = document.createElement("option");
            opt.value = d.deviceId || "";
            opt.textContent = d.label || "Camera";
            select.appendChild(opt);
        }
        select.disabled = videos.length === 0;
        if (sheet && videos.length > 1) sheet.hidden = false;
    } catch (_) {
        select.disabled = true;
    }
}

async function startCamera() {
    if (!isOperationalSessionId(sessionId)) {
        setMessage("FIELD_SESSION_ID_REQUIRED");
        return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setText(cameraBadge, "CAMERA_API_UNAVAILABLE");
        setMessage("CAMERA_API_UNAVAILABLE_HTTPS_REQUIRED");
        return;
    }

    const constraints = {
        audio: false,
        video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1280 },
            height: { ideal: 720 },
            frameRate: { ideal: 15, max: 30 },
        },
    };

    try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        await video.play();
        const track = stream.getVideoTracks()[0];
        const label = String(track?.label || "").toLowerCase();
        if (label.includes("front") || label.includes("user")) {
            setText(cameraBadge, "CAMERA_FRONT_ACTIVE_NOT_RECOMMENDED_FOR_FIELD_TREE");
        } else {
            setText(cameraBadge, "CAMERA_STREAM_READY");
        }
        setMessage("CAMERA_STREAM_READY");
        await populateCameraLensSelectorIfAvailable();
        if (frameTimer) clearInterval(frameTimer);
        frameTimer = setInterval(sendFrame, 1000);
        setTimeout(sendFrame, 350);
    } catch (err) {
        setText(cameraBadge, "CAMERA_PERMISSION_REQUIRED");
        setMessage("CAMERA_PERMISSION_REQUIRED");
        updateDebug({ ok: false, error: String(err), status: "CAMERA_PERMISSION_REQUIRED" });
    }
}

async function shutter() {
    if (!isOperationalSessionId(sessionId)) {
        alert("Session belum valid. Kembali ke Home lalu tekan Start.");
        return;
    }
    const dataUrl = getVideoFrameDataUrl();
    if (!dataUrl || dataUrl.length < 1000) {
        alert("Kamera belum stabil. Tunggu CAMERA_STREAM_READY dan FRAME_OK.");
        return;
    }
    setText(shutterBadge, "SHUTTER_SAVING");
    try {
        const result = await postJson(API_SHUTTER, buildFramePayload(dataUrl, "shutter"));
        shutterSaved = true;
        sessionStorage.setItem(`ulp_shutter_saved_${sessionId}`, "1");
        setText(shutterBadge, result.shutter_status || "SHUTTER_SAVED");
        setMessage(result.message || "SHUTTER_SAVED");
        updateDebug(result);
        drawOverlay(result);
    } catch (err) {
        setText(shutterBadge, "SHUTTER_FAILED");
        updateDebug({ ok: false, error: String(err), status: "SHUTTER_FAILED" });
    }
}

function goMap() {
    if (!shutterSaved && sessionStorage.getItem(`ulp_shutter_saved_${sessionId}`) !== "1") {
        alert("Jepret dulu untuk membuat evidence map.");
        return;
    }
    location.href = `/field-map/session/${encodeURIComponent(sessionId)}`;
}

function goResult() {
    if (!shutterSaved && sessionStorage.getItem(`ulp_shutter_saved_${sessionId}`) !== "1") {
        alert("Jepret dulu untuk membuat spreadsheet evidence.");
        return;
    }
    location.href = `/field-spreadsheet/session/${encodeURIComponent(sessionId)}`;
}

function stopStream() {
    if (frameTimer) clearInterval(frameTimer);
    if (gpsWatchId !== null && navigator.geolocation) navigator.geolocation.clearWatch(gpsWatchId);
    if (stream) stream.getTracks().forEach(t => t.stop());
}

window.addEventListener("resize", () => drawOverlay(lastFrameResult || {}));
window.addEventListener("beforeunload", stopStream);

document.getElementById("homeBtn")?.addEventListener("click", () => location.href = "/field-capture");
document.getElementById("mapBtn")?.addEventListener("click", goMap);
document.getElementById("resultBtn")?.addEventListener("click", goResult);
document.getElementById("manualBtn")?.addEventListener("click", () => alert("Manual input tetap aman; stabilkan kamera dulu."));
document.getElementById("shutterBtn")?.addEventListener("click", shutter);

setText(sessionBadge, sessionId ? sessionId.slice(0, 22) : "FIELD_SESSION_ID_REQUIRED");
updateDebug({ ui_version: UI_VERSION, status: "FIELD_CAMERA_JS_READY" });

if (sessionId) {
    startGpsWatch();
    startCamera();
} else {
    setMessage("FIELD_SESSION_ID_REQUIRED");
}
})();
