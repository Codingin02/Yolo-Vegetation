(function () {
  const output = document.getElementById("status-output");
  const video = document.getElementById("camera");
  const canvas = document.getElementById("frame");
  let capturedBlob = null;

  function setStatus(payload) {
    output.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  }

  document.getElementById("open-camera").addEventListener("click", async function () {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      video.srcObject = stream;
      setStatus("CAMERA_READY");
    } catch (error) {
      setStatus({ status: "CAMERA_NOT_READY", message: String(error) });
    }
  });

  document.getElementById("capture-frame").addEventListener("click", function () {
    if (!video.videoWidth) {
      setStatus("CAMERA_FRAME_NOT_READY");
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob(function (blob) {
      capturedBlob = blob;
      setStatus("FRAME_CAPTURED_READY_TO_UPLOAD");
    }, "image/jpeg", 0.82);
  });

  document.getElementById("gps-btn").addEventListener("click", function () {
    if (!navigator.geolocation) {
      setStatus("GPS_NOT_AVAILABLE_IN_BROWSER");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      function (position) {
        document.getElementById("lat").value = position.coords.latitude.toFixed(7);
        document.getElementById("lon").value = position.coords.longitude.toFixed(7);
        setStatus("GPS_READY");
      },
      function () {
        setStatus("GPS_PERMISSION_OR_SIGNAL_NOT_READY");
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  });

  document.getElementById("ping-btn").addEventListener("click", async function () {
    const response = await fetch("/api/field-capture/ping");
    setStatus(await response.json());
  });

  document.getElementById("upload-btn").addEventListener("click", async function () {
    const form = new FormData();
    form.append("point_id", document.getElementById("point_id").value);
    form.append("manual_object_type", document.getElementById("manual_object_type").value);
    form.append("lat", document.getElementById("lat").value);
    form.append("lon", document.getElementById("lon").value);
    form.append("timestamp", new Date().toISOString());
    form.append("operator_note", document.getElementById("operator_note").value);
    form.append("network_mode", navigator.onLine ? "same_lan_mode" : "offline_queue_mode");
    const selected = document.getElementById("image").files[0];
    if (capturedBlob) {
      form.append("image", capturedBlob, "field_capture_frame.jpg");
    } else if (selected) {
      form.append("image", selected);
    }
    try {
      const response = await fetch("/api/field-capture/upload", { method: "POST", body: form });
      setStatus(await response.json());
    } catch (error) {
      localStorage.setItem("field_capture_pending_upload", "true");
      setStatus({ status: "OFFLINE_QUEUE_PENDING", message: String(error) });
    }
  });
})();
