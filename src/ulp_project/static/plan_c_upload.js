(function () {
  const form = document.getElementById("uploadForm");
  const gpsState = document.getElementById("gpsState");
  const processButton = document.getElementById("processButton");
  const processState = document.getElementById("processState");

  function setText(element, text) {
    if (element) {
      element.textContent = text;
    }
  }

  function readGps() {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        setText(gpsState, "GPS tidak tersedia");
        resolve(null);
        return;
      }
      setText(gpsState, "Mengambil GPS");
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords = position.coords || {};
          document.getElementById("latitude").value = coords.latitude || "";
          document.getElementById("longitude").value = coords.longitude || "";
          document.getElementById("accuracyM").value = coords.accuracy || "";
          setText(gpsState, `GPS siap (${Math.round(coords.accuracy || 0)} m)`);
          resolve(coords);
        },
        () => {
          setText(gpsState, "GPS_NOT_AVAILABLE");
          resolve(null);
        },
        { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
      );
    });
  }

  if (form) {
    readGps();
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector("button[type='submit']");
      if (button) button.disabled = true;
      setText(gpsState, "Mengupload foto");
      await readGps();
      const body = new FormData(form);
      try {
        const response = await fetch("/api/plan-c/upload/start", { method: "POST", body });
        const data = await response.json();
        if (!response.ok || !data.ok) {
          throw new Error(data.status || "UPLOAD_FAILED");
        }
        window.location.href = data.review_url;
      } catch (error) {
        setText(gpsState, `Upload gagal: ${error.message}`);
        if (button) button.disabled = false;
      }
    });
  }

  if (processButton) {
    processButton.addEventListener("click", async () => {
      const sessionId = processButton.dataset.sessionId;
      processButton.disabled = true;
      setText(processState, "Memproses foto");
      try {
        const response = await fetch(`/api/plan-c/upload/process/${sessionId}`, { method: "POST" });
        const data = await response.json();
        if (!response.ok || !data.ok) {
          throw new Error(data.status || "PROCESS_FAILED");
        }
        window.location.href = data.result_url || `/plan-c/upload/result/${sessionId}`;
      } catch (error) {
        setText(processState, `Proses gagal: ${error.message}`);
        processButton.disabled = false;
      }
    });
  }
})();
