(function () {
  function initCameraPage() {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session_id") || window.localStorage.getItem("field_session_id") || "";
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
        session.renderOverlay({ model_status: "MODEL_NOT_READY", detections: [] });
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
