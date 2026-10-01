(() => {
  const page = document.body.dataset.page;
  const byId = (id) => document.getElementById(id);

  if (page === "home") {
    byId("start-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const status = byId("form-status");
      status.textContent = "Membuat sesi...";
      try {
        const response = await fetch("/api/vegetation/session/start", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget)))
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || payload.status);
        location.assign(payload.capture_url);
      } catch (error) {
        status.textContent = `Sesi gagal dibuat: ${error.message}`;
      }
    });
  }

  if (page === "capture") setupCapture();
  if (page === "processing") pollResult();
  if (page === "result") setupFeedback();

  async function setupCapture() {
    const sessionId = document.body.dataset.sessionId;
    const video = byId("camera");
    const stage = document.querySelector(".video-stage");
    const overlay = byId("detection-overlay");
    const overlayContext = overlay.getContext("2d");
    const canvas = byId("snapshot-canvas");
    const message = byId("camera-message");
    const status = byId("capture-status");
    const startButton = byId("capture-button");
    const lightingButton = byId("lighting-button");
    const flashButton = byId("flash-button");
    const stopButton = byId("retry-button");
    const saveButton = byId("submit-button");
    const galleryInput = byId("gallery-input");
    let running = false;
    let inferenceBusy = false;
    let inferenceAnimation = null;
    let requestId = 0;
    let latestRenderedRequest = 0;
    let lastFrame = null;
    let stream = null;
    let flashEnabled = false;
    let lightingIndex = 0;
    let normalExposure = null;
    let lastExposureTarget = null;
    let lastExposureAt = 0;
    let exposureApplying = false;
    const lightingModes = [
      {value: "auto", label: "Auto"},
      {value: "normal", label: "Normal"},
      {value: "backlight", label: "Backlight"},
      {value: "low_light", label: "Low Light"}
    ];
    startButton.disabled = true;

    try {
      stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: {ideal: "environment"}}, audio: false});
      video.srcObject = stream;
      await video.play();
      message.hidden = true;
      startButton.disabled = false;
      lightingButton.disabled = false;
      flashButton.disabled = false;
      const exposure = stream.getVideoTracks()[0]?.getSettings?.().exposureCompensation;
      if (Number.isFinite(exposure)) {
        normalExposure = exposure;
        lastExposureTarget = exposure;
      }
    } catch (_) {
      message.textContent = "Kamera tidak tersedia. Pilih foto dari galeri.";
    }

    startButton.addEventListener("click", () => {
      if (running || !video.videoWidth) return;
      running = true;
      startButton.hidden = true;
      stopButton.hidden = false;
      status.textContent = "Menghubungkan deteksi...";
      scheduleInference();
    });
    lightingButton.addEventListener("click", cycleLighting);
    flashButton.addEventListener("click", toggleFlash);
    stopButton.addEventListener("click", stopRealtime);
    saveButton.addEventListener("click", async () => submitSnapshot(await cameraFrame(), "camera"));
    galleryInput.addEventListener("change", () => submitSnapshot(galleryInput.files[0], "gallery"));
    window.addEventListener("pagehide", () => {
      stopInference();
      stream?.getTracks().forEach((track) => track.stop());
    });

    async function inferenceLoop() {
      inferenceAnimation = null;
      if (!running) return;
      if (inferenceBusy || document.hidden) {
        scheduleInference();
        return;
      }
      inferenceBusy = true;
      const currentRequest = ++requestId;
      try {
        const frame = await cameraFrame();
        if (!frame) {
          status.textContent = "Frame kamera belum tersedia.";
          return;
        }
        lastFrame = frame;
        const form = new FormData();
        form.append("session_id", sessionId);
        form.append("lighting_mode", lightingModes[lightingIndex].value);
        form.append("frame", frame, "frame.jpg");
        const response = await fetch("/api/vegetation/realtime/frame", {method: "POST", body: form});
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || payload.status);
        if (!running || currentRequest < latestRenderedRequest) return;
        latestRenderedRequest = currentRequest;
        applyLightingFeedback(payload.lighting);
        drawDetections(payload);
        saveButton.hidden = false;
        status.textContent = runtimeStatus(payload);
      } catch (error) {
        if (running && currentRequest >= latestRenderedRequest) {
          status.textContent = `Koneksi deteksi bermasalah: ${error.message}`;
        }
      } finally {
        inferenceBusy = false;
        scheduleInference();
      }
    }

    function scheduleInference() {
      if (running && inferenceAnimation === null) {
        inferenceAnimation = window.requestAnimationFrame(inferenceLoop);
      }
    }

    function stopRealtime() {
      stopInference();
      startButton.hidden = false;
      stopButton.hidden = true;
      status.textContent = lastFrame ? "Deteksi dihentikan. Hasil terakhir tetap terlihat." : "Deteksi dihentikan.";
    }

    async function toggleFlash() {
      flashEnabled = !flashEnabled;
      flashButton.disabled = true;
      flashButton.textContent = flashEnabled ? "Flash Nyala" : "Flash Mati";
      flashButton.setAttribute("aria-pressed", String(flashEnabled));
      stage.classList.toggle("screen-flash", flashEnabled);
      let torchApplied = false;
      try {
        const track = stream?.getVideoTracks()[0];
        if (track?.getCapabilities?.().torch) {
          await track.applyConstraints({advanced: [{torch: flashEnabled}]});
          torchApplied = true;
        }
      } catch (_) {
        torchApplied = false;
      }
      if (torchApplied) stage.classList.remove("screen-flash");
      status.textContent = flashEnabled
        ? (torchApplied ? "Flash kamera aktif." : "Flash layar aktif.")
        : "Flash dimatikan.";
      flashButton.disabled = false;
    }

    function cycleLighting() {
      lightingIndex = (lightingIndex + 1) % lightingModes.length;
      const mode = lightingModes[lightingIndex];
      lightingButton.textContent = `Cahaya: ${mode.label}`;
      video.style.filter = "none";
      if (mode.value === "normal") void applyHardwareExposure(0, true);
      status.textContent = `Cahaya ${mode.label.toLowerCase()} aktif.`;
    }

    function applyLightingFeedback(lighting) {
      const mode = lightingModes[lightingIndex].value;
      if (!lighting || lighting.mode !== mode) return;
      const brightness = Math.max(1, Math.min(1.65, Number(lighting.preview_brightness) || 1));
      const contrast = Math.max(1, Math.min(1.20, Number(lighting.preview_contrast) || 1));
      video.style.filter = mode === "normal" ? "none" : `brightness(${brightness}) contrast(${contrast})`;
      if (mode !== "normal") {
        void applyHardwareExposure(Number(lighting.exposure_ratio) || 0);
      } else {
        void applyHardwareExposure(0);
      }
    }

    async function applyHardwareExposure(ratio, force = false) {
      if (exposureApplying) return;
      const track = stream?.getVideoTracks()[0];
      const capability = track?.getCapabilities?.().exposureCompensation;
      const current = track?.getSettings?.().exposureCompensation;
      if (!capability || !Number.isFinite(capability.min) || !Number.isFinite(capability.max)) return;
      if (normalExposure === null && Number.isFinite(current)) normalExposure = current;
      if (normalExposure === null) return;
      const boundedRatio = Math.max(0, Math.min(0.7, ratio));
      const target = Math.max(
        capability.min,
        Math.min(capability.max, normalExposure + (capability.max - normalExposure) * boundedRatio)
      );
      const threshold = Math.max(Number(capability.step) || 0, (capability.max - capability.min) * 0.05);
      const now = Date.now();
      if (!force && (
        now - lastExposureAt < 650
        || (Number.isFinite(lastExposureTarget) && Math.abs(target - lastExposureTarget) < threshold)
      )) return;
      exposureApplying = true;
      lastExposureAt = now;
      try {
        await track.applyConstraints({advanced: [{exposureCompensation: target}]});
        lastExposureTarget = target;
      } catch (_) {
        // Hardware exposure is optional; software adaptation remains active.
      } finally {
        exposureApplying = false;
      }
    }

    async function submitSnapshot(blob, source) {
      if (!blob) return;
      stopInference();
      startButton.disabled = true;
      stopButton.hidden = true;
      saveButton.disabled = true;
      status.textContent = "Menyimpan dan memproses hasil...";
      const form = new FormData();
      form.append("session_id", sessionId);
      form.append("lighting_mode", lightingModes[lightingIndex].value);
      form.append("snapshot", blob, "capture.jpg");
      form.append("capture_source", source);
      try {
        const response = await fetch("/api/vegetation/session/snapshot", {method: "POST", body: form});
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || payload.status);
        location.assign(payload.result_url);
      } catch (error) {
        status.textContent = `Hasil gagal disimpan: ${error.message}`;
        startButton.disabled = false;
        saveButton.disabled = false;
      }
    }

    function cameraFrame() {
      if (!video.videoWidth || !video.videoHeight) return Promise.resolve(null);
      const scale = Math.min(1, 768 / Math.max(video.videoWidth, video.videoHeight));
      canvas.width = Math.round(video.videoWidth * scale);
      canvas.height = Math.round(video.videoHeight * scale);
      const context = canvas.getContext("2d");
      context.filter = "none";
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      context.filter = "none";
      return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.75));
    }

    function drawDetections(payload) {
      const width = overlay.clientWidth;
      const height = overlay.clientHeight;
      if (!width || !height) return;
      overlay.width = Math.round(width);
      overlay.height = Math.round(height);
      overlayContext.clearRect(0, 0, overlay.width, overlay.height);
      const sourceWidth = Number(payload.frame?.width);
      const sourceHeight = Number(payload.frame?.height);
      if (!(sourceWidth > 0 && sourceHeight > 0)) return;
      const rect = containedVideoRect(overlay.width, overlay.height);
      const scaleX = rect.width / sourceWidth;
      const scaleY = rect.height / sourceHeight;
      overlayContext.font = "600 14px Arial";
      overlayContext.lineWidth = 2;
      overlayContext.textBaseline = "top";

      if (payload.geometry?.thresholds?.ready && Array.isArray(payload.geometry.risk_bands)) {
        for (const band of payload.geometry.risk_bands) {
          const status = String(band.status || "").toUpperCase();
          const fill = status === "TEBANG"
            ? "rgba(220, 38, 38, .24)"
            : status === "PANTAU" ? "rgba(245, 158, 11, .22)" : null;
          const polygon = Array.isArray(band.polygon_xyn)
            ? band.polygon_xyn.map((point) => Array.isArray(point) ? point.map(Number) : [])
            : [];
          if (!fill || polygon.length < 3 || !polygon.every((point) => point.length === 2 && point.every(Number.isFinite))) continue;
          overlayContext.beginPath();
          polygon.forEach((point, index) => {
            const x = rect.left + Math.max(0, Math.min(1, point[0])) * rect.width;
            const y = rect.top + Math.max(0, Math.min(1, point[1])) * rect.height;
            if (index === 0) overlayContext.moveTo(x, y);
            else overlayContext.lineTo(x, y);
          });
          overlayContext.closePath();
          overlayContext.fillStyle = fill;
          overlayContext.fill();
        }
      }

      const geometryTrees = Array.isArray(payload.geometry?.trees) ? payload.geometry.trees : [];
      for (const [detectionIndex, detection] of (payload.detections || []).entries()) {
        if (!Array.isArray(detection.bbox_xyxy) || detection.bbox_xyxy.length !== 4) continue;
        const bbox = detection.bbox_xyxy.map(Number);
        if (!bbox.every(Number.isFinite)) continue;
        const x1 = Math.max(rect.left, Math.min(rect.left + bbox[0] * scaleX, rect.left + rect.width));
        const y1 = Math.max(rect.top, Math.min(rect.top + bbox[1] * scaleY, rect.top + rect.height));
        const x2 = Math.max(rect.left, Math.min(rect.left + bbox[2] * scaleX, rect.left + rect.width));
        const y2 = Math.max(rect.top, Math.min(rect.top + bbox[3] * scaleY, rect.top + rect.height));
        if (x2 <= x1 || y2 <= y1) continue;

        const rawClassName = String(detection.class_name || detection.class || "");
        const isAngsana = rawClassName.toLowerCase() === "angsana";
        const treeGeometry = isAngsana ? geometryTrees.find((tree) => (
          tree.track_id != null && detection.track_id != null
            ? String(tree.track_id) === String(detection.track_id)
            : Number(tree.detection_index) === detectionIndex
        )) : null;
        const prediction = isAngsana ? detection.prediction : null;
        const rawRiskStatus = isAngsana ? String(
          prediction ? (prediction.operational_status || prediction.prediction_status || "") : (treeGeometry?.risk_status || "")
        ) : "";
        const operationalStatus = isAngsana && ["AMAN", "PANTAU", "TEBANG"].includes(rawRiskStatus.toUpperCase())
          ? rawRiskStatus.toUpperCase()
          : null;
        const technicalStatus = isAngsana ? {
          threshold_not_configured: "Ambang risiko belum dikonfigurasi",
          uncalibrated_device: "Perangkat belum dikalibrasi",
          capture_protocol_required: "Protokol pengambilan belum terpenuhi",
          conductor_not_detected: "Konduktor tidak terdeteksi",
          insufficient_data: "Data belum cukup",
          geometry_unreliable: "Geometri belum cukup andal",
          threshold_incompatible: "Jenis ambang tidak cocok"
        }[rawRiskStatus] : null;
        const statusStyle = isAngsana ? {
          AMAN: {stroke: "#4aa316", label: "rgba(23, 98, 55, .9)"},
          PANTAU: {stroke: "#f59e0b", label: "rgba(146, 88, 0, .92)"},
          TEBANG: {stroke: "#dc2626", label: "rgba(153, 27, 27, .92)"}
        }[operationalStatus] : null;
        const color = statusStyle?.stroke || (rawClassName === "konduktor" ? "#f59e0b" : "#4aa316");
        const polygon = Array.isArray(detection.mask_polygon_xyn)
          ? detection.mask_polygon_xyn.map((point) => Array.isArray(point) ? point.map(Number) : [])
          : [];
        if (polygon.length >= 3 && polygon.every((point) => point.length === 2 && point.every(Number.isFinite))) {
          overlayContext.beginPath();
          polygon.forEach((point, index) => {
            const x = rect.left + Math.max(0, Math.min(1, point[0])) * rect.width;
            const y = rect.top + Math.max(0, Math.min(1, point[1])) * rect.height;
            if (index === 0) overlayContext.moveTo(x, y);
            else overlayContext.lineTo(x, y);
          });
          overlayContext.closePath();
          overlayContext.strokeStyle = color;
          overlayContext.stroke();
        }
        overlayContext.strokeStyle = color;
        overlayContext.strokeRect(x1, y1, x2 - x1, y2 - y1);
        const name = String(detection.display_name || detection.class_name || detection.class || "Objek");
        const confidence = Math.round((Number(detection.confidence) || 0) * 100);
        const track = detection.track_id == null ? "" : ` #${detection.track_id}`;
        const lines = [`${name} ${confidence}%${track}`];
        if (isAngsana) {
          const days = prediction?.days_to_prune == null ? null : Number(prediction.days_to_prune);
          const statusParts = [];
          if (operationalStatus) statusParts.push(operationalStatus);
          if (Number.isFinite(days) && days >= 0) statusParts.push(`${days > 0 ? "~" : ""}${Math.round(days)} HARI`);
          if (statusParts.length) lines[0] += ` | ${statusParts.join(" | ")}`;
          if (!statusParts.length && prediction?.prediction_status === "insufficient_growth_reference") {
            lines[0] += " | DATA PERTUMBUHAN KURANG";
          }
          if (!operationalStatus && technicalStatus) lines.push(technicalStatus);
          else if (!statusParts.length && prediction?.display_status) lines.push(String(prediction.display_status));
        }
        const lineHeight = 18;
        const labelWidth = Math.min(rect.width, Math.max(...lines.map((line) => overlayContext.measureText(line).width)) + 12);
        const labelHeight = lineHeight * lines.length + 4;
        const labelX = Math.max(rect.left, Math.min(x1, rect.left + rect.width - labelWidth));
        const labelY = Math.max(rect.top, y1 - labelHeight);
        overlayContext.fillStyle = statusStyle?.label || "rgba(23, 98, 55, .9)";
        overlayContext.fillRect(labelX, labelY, labelWidth, labelHeight);
        overlayContext.fillStyle = "#fff";
        lines.forEach((line, index) => overlayContext.fillText(line, labelX + 6, labelY + 3 + index * lineHeight));
      }
    }

    function containedVideoRect(width, height) {
      const videoRatio = video.videoWidth / video.videoHeight;
      if (width / height > videoRatio) {
        const renderedWidth = height * videoRatio;
        return {left: (width - renderedWidth) / 2, top: 0, width: renderedWidth, height};
      }
      const renderedHeight = width / videoRatio;
      return {left: 0, top: (height - renderedHeight) / 2, width, height: renderedHeight};
    }

    function stopInference() {
      running = false;
      if (inferenceAnimation !== null) window.cancelAnimationFrame(inferenceAnimation);
      inferenceAnimation = null;
      latestRenderedRequest = ++requestId;
    }

    function runtimeStatus(payload) {
      if (payload.detector_status === "model_not_ready") return "Model detector belum tersedia; kamera tetap aktif.";
      if (payload.detector_status === "inference_error") return `Inference gagal: ${payload.detector_error || "error tidak diketahui"}`;
      const detector = payload.production_detector_ready ? "Detector pohon aktif" : "Inference dasar aktif; model pohon produksi belum tersedia";
      const tracking = payload.tracking_status === "active" ? "pelacakan aktif" : "pelacakan tidak tersedia";
      return `${detector} · ${tracking} · ${payload.detection_count} objek`;
    }
  }

  async function pollResult() {
    const sessionId = document.body.dataset.sessionId;
    const status = byId("processing-status");
    for (let attempt = 0; attempt < 60; attempt += 1) {
      try {
        const response = await fetch(`/api/vegetation/session/${sessionId}/status`, {cache: "no-store"});
        const payload = await response.json();
        if (payload.result_ready) return location.replace(payload.result_url);
        const statusLabels = {
          waiting_for_capture: "Menunggu frame...",
          processing: "Sedang memproses...",
          ready: "Hasil siap."
        };
        status.textContent = statusLabels[payload.status] || "Menunggu hasil...";
      } catch (_) {
        status.textContent = "Menunggu koneksi...";
      }
      await wait(1000);
    }
    status.textContent = "Pemrosesan belum selesai. Muat ulang halaman untuk mencoba lagi.";
  }

  function setupFeedback() {
    document.querySelectorAll("[data-decision]").forEach((button) => {
      button.addEventListener("click", async () => {
        const response = await fetch("/api/vegetation/operator-feedback", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({session_id: document.body.dataset.sessionId, decision: button.dataset.decision})
        });
        const payload = await response.json();
        byId("review-status").textContent = response.ok ? "Pemeriksaan tersimpan." : `Pemeriksaan gagal: ${payload.status}`;
      });
    });
  }

  function wait(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
  }
})();
