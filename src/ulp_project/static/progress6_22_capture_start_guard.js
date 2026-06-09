/* PROGRESS_6_22_CAPTURE_START_JSON_GUARD */
(function () {
  "use strict";

  const VERSION = "PROGRESS_6_22_CAPTURE_START_JSON_GUARD";

  function textOf(el) {
    return ((el && (el.innerText || el.textContent || el.value || el.getAttribute("aria-label") || "")) || "").trim();
  }

  function idClassOf(el) {
    if (!el) return "";
    return [
      el.id || "",
      el.className || "",
      el.getAttribute("data-action") || "",
      el.getAttribute("data-role") || "",
      el.getAttribute("href") || ""
    ].join(" ").toLowerCase();
  }

  function isStartCameraControl(el) {
    if (!el) return false;
    const hay = (textOf(el) + " " + idClassOf(el)).toLowerCase();
    if (hay.includes("map") || hay.includes("result") || hay.includes("manual")) return false;
    return (
      hay.includes("start") ||
      hay.includes("mulai") ||
      hay.includes("camera") ||
      hay.includes("kamera") ||
      hay.includes("field-camera") ||
      hay.includes("buka kamera") ||
      hay.includes("open camera")
    );
  }

  function getInputValue(names, fallback) {
    for (const n of names) {
      const el = document.querySelector(n);
      if (el && el.value && String(el.value).trim()) return String(el.value).trim();
    }
    return fallback;
  }

  async function parseJsonOrThrow(resp) {
    const contentType = (resp.headers.get("content-type") || "").toLowerCase();
    const text = await resp.text();
    if (!contentType.includes("application/json")) {
      throw new Error("SESSION_START_RETURNED_NON_JSON_" + text.slice(0, 48).replace(/\s+/g, "_"));
    }
    try {
      return JSON.parse(text);
    } catch (err) {
      throw new Error("SESSION_START_JSON_PARSE_FAILED_" + String(err && err.message || err));
    }
  }

  async function startSession() {
    const pointId = getInputValue([
      'input[name="point_id"]',
      '#point_id',
      '#pointId',
      '[data-field="point_id"]'
    ], "V001_pohon_sono");

    const operator = getInputValue([
      'input[name="operator"]',
      '#operator',
      '#operatorName',
      '[data-field="operator"]'
    ], "operator");

    const payload = {
      point_id: pointId,
      operator: operator,
      source: VERSION,
      frontend_version: VERSION,
      no_fake_detection: true,
      no_fake_clearance: true
    };

    const resp = await fetch("/api/field/session/start", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
      cache: "no-store"
    });

    const data = await parseJsonOrThrow(resp);

    if (!resp.ok || data.ok === false) {
      throw new Error(data.error || data.status || ("SESSION_START_HTTP_" + resp.status));
    }

    const sessionId = data.session_id || data.id || "";
    let cameraUrl = data.camera_url || data.field_camera_url || "";

    if (!cameraUrl && sessionId) {
      cameraUrl = "/field-camera?session_id=" + encodeURIComponent(sessionId);
    }

    if (!cameraUrl) {
      throw new Error("SESSION_START_NO_CAMERA_URL");
    }

    const sep = cameraUrl.includes("?") ? "&" : "?";
    window.location.href = cameraUrl + sep + "v=progress6_22_frontend";
  }

  function install() {
    document.documentElement.setAttribute("data-progress6-22-capture-start-guard", "ready");

    document.addEventListener("click", function (ev) {
      const target = ev.target && ev.target.closest ? ev.target.closest("button,a,[role='button'],input[type='button'],input[type='submit']") : null;
      if (!isStartCameraControl(target)) return;

      ev.preventDefault();
      ev.stopPropagation();
      ev.stopImmediatePropagation();

      startSession().catch(function (err) {
        alert("SESSION_START_FAILED_6_22: " + (err && err.message ? err.message : String(err)));
        console.error("[P6.22] session start failed", err);
      });
    }, true);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }
})();
