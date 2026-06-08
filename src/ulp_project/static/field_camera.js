(function () {
  function readCameraSessionId() {
    const params = new URLSearchParams(location.search);
    const urlHasSessionParam = params.has("session_id");
    const fromUrl = new URLSearchParams(location.search).get("session_id");
    if (urlHasSessionParam && (!String(fromUrl || "").trim() || String(fromUrl || "").trim().startsWith("FS_DEGRADED"))) {
      return "";
    }
    const fromBody = (document.body && document.body.dataset && document.body.dataset.sessionId) || "";
    const root = document.querySelector("[data-session-id]");
    const fromRoot = (root && root.dataset && root.dataset.sessionId) || "";
    const hidden = document.getElementById("camera-session-id");
    const fromHidden = (hidden && hidden.dataset && hidden.dataset.sessionId) || "";
    const fromSessionStorage = window.sessionStorage.getItem("ulp_active_field_session_id") || "";
    const fromLocalStorage = window.localStorage.getItem("field_session_id") || "";
    const candidates = [fromUrl, fromBody, fromRoot, fromHidden, fromSessionStorage, fromLocalStorage].map(function (value) {
      return String(value || "").trim();
    });
    return candidates.find(function (value) {
      return value && !value.startsWith("FS_DEGRADED");
    }) || "";
  }

  function setFatalSessionError(visible, status) {
    const error = document.getElementById("camera-session-error");
    if (error) error.hidden = !visible;
    document.body.classList.toggle("camera-session-error", Boolean(visible));
    if (visible && window.FieldSession) {
      window.FieldSession.handleError(status || "FIELD_SESSION_ID_REQUIRED", "Session ID kosong. Kembali ke Home lalu tekan Start ulang.");
    }
  }

  function initCameraPage() {
    const sessionId = readCameraSessionId();
    if (!sessionId) {
      setFatalSessionError(true, "FIELD_SESSION_ID_REQUIRED");
      return;
    }
    setFatalSessionError(false, "");
    window.localStorage.setItem("field_session_id", sessionId);
    window.sessionStorage.setItem("ulp_active_field_session_id", sessionId);
    if (window.FieldSession && window.FieldSession.state) {
      window.FieldSession.state.session_id = sessionId;
      window.FieldSession.state.session_status = "RECORDING_ACTIVE";
    }
    document.body.classList.add("camera-mode-active");
    if (!window.FieldSession) return;
    const session = window.FieldSession;
    session.renderStatus();
    Promise.resolve()
      .then(function () {
        return session.startCamera();
      })
      .then(function () {
        session.startGpsWatch();
        session.startFrameLoop();
        session.renderOverlay({ model_status: "TREE_MODEL_READY_CANDIDATE", detections: [] });
        session.renderStatus();
      })
      .catch(function (error) {
        session.handleError("FIELD_CAMERA_START_FAILED", String(error));
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCameraPage);
  } else {
    initCameraPage();
  }
})();
