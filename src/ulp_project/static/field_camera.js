(function () {
  function initCameraPage() {
    const params = new URLSearchParams(window.location.search);
    const urlHasSessionParam = params.has("session_id");
    const sessionId = urlHasSessionParam ? (params.get("session_id") || "") : (window.localStorage.getItem("field_session_id") || "");
    if (!sessionId || String(sessionId).startsWith("FS_DEGRADED")) {
      document.body.classList.add("camera-session-error");
      const error = document.getElementById("camera-session-error");
      if (error) error.hidden = false;
      if (window.FieldSession) {
        window.FieldSession.handleError("SESSION_INVALID_OR_EXPIRED", "Session ID kosong/degraded. Kembali ke Home lalu tekan Start ulang.");
      }
      return;
    }
    if (sessionId) {
      window.localStorage.setItem("field_session_id", sessionId);
      if (window.FieldSession && window.FieldSession.state) {
        window.FieldSession.state.session_id = sessionId;
        window.FieldSession.state.session_status = "RECORDING_ACTIVE";
      }
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
