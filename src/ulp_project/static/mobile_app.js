(function () {
  const statusOutput = document.getElementById("status-output");
  const gpsButton = document.getElementById("gps-btn");
  const uploadButton = document.getElementById("upload-btn");

  function setStatus(payload) {
    statusOutput.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
  }

  gpsButton.addEventListener("click", function () {
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

  uploadButton.addEventListener("click", async function () {
    const form = new FormData();
    form.append("point_id", document.getElementById("point_id").value);
    form.append("lat", document.getElementById("lat").value);
    form.append("lon", document.getElementById("lon").value);
    form.append("timestamp", new Date().toISOString());
    form.append("operator_note", document.getElementById("operator_note").value);
    form.append("network_mode", navigator.onLine ? "same_lan_mode" : "offline_queue_mode");
    const image = document.getElementById("image").files[0];
    if (image) {
      form.append("image", image);
    }
    try {
      const response = await fetch("/api/mobile/upload-inspection", { method: "POST", body: form });
      const payload = await response.json();
      setStatus(payload);
      if (!navigator.onLine) {
        localStorage.setItem("ulp_last_offline_payload", JSON.stringify({ point_id: form.get("point_id") }));
      }
    } catch (error) {
      setStatus({ status: "OFFLINE_QUEUE_PENDING", message: String(error) });
      localStorage.setItem("ulp_offline_queue_status", "PENDING_UPLOAD");
    }
  });
})();
