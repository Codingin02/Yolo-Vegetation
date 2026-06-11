(function () {
  const image = document.getElementById("annotatedImage");
  if (image) {
    image.addEventListener("error", () => {
      const parent = image.parentElement;
      if (!parent) return;
      parent.innerHTML = '<div class="image-placeholder">ANNOTATED_IMAGE_NOT_AVAILABLE</div>';
    });
  }

  const match = window.location.pathname.match(/\/plan-c\/result\/([^/?#]+)/);
  const sessionId = match ? decodeURIComponent(match[1]) : "";
  if (!sessionId) return;

  function text(value, fallback) {
    if (value === null || value === undefined || value === "") return fallback || "-";
    return String(value);
  }

  function addOperatorPanel(result) {
    if (document.getElementById("plan-c-detection-zone-panel")) return;
    const panel = document.createElement("section");
    panel.id = "plan-c-detection-zone-panel";
    panel.className = "plan-c-feedback-box";
    panel.innerHTML = `
      <strong>Detection + Zone</strong>
      <dl class="metric-list">
        <dt>tree_species_status</dt><dd>${text(result.tree_species_status, "unknown")}</dd>
        <dt>conductor_status</dt><dd>${text(result.conductor_status, "tidak tervalidasi")}</dd>
        <dt>ground_reference_status</dt><dd>${text(result.ground_reference_status, "GROUND_REFERENCE_NOT_AVAILABLE")}</dd>
        <dt>zone_status</dt><dd>${text(result.zone_status, "unavailable")}</dd>
        <dt>zone_precision</dt><dd>${text(result.zone_precision, "unavailable")}</dd>
        <dt>Bounding box</dt><dd>${text(result.detection_count, "0")}</dd>
        <dt>conductor_group_count</dt><dd>${text(result.conductor_group_count, "0")}</dd>
        <dt>Prediction</dt><dd>${text(result.prediction_window, "data tidak cukup")}</dd>
        <dt>Review</dt><dd>${text(result.manual_review_required, true)}</dd>
      </dl>
    `;
    const target = document.querySelector(".summary-grid") || document.querySelector("main") || document.body;
    target.appendChild(panel);
  }

  function addFeedbackButtons() {
    if (document.getElementById("plan-c-feedback-box")) return;
    const box = document.createElement("section");
    box.id = "plan-c-feedback-box";
    box.className = "plan-c-feedback-box";
    box.innerHTML = `
      <strong>Operator Review</strong>
      <p>Gunakan tombol ini setelah hasil Detection, zona, dan Prediction diperiksa di lapangan.</p>
      <button id="plan-c-accept-result" class="plan-c-accept-btn" type="button">Benar, simpan referensi</button>
      <button id="plan-c-reject-result" class="plan-c-reject-btn" type="button">Salah, hapus hasil</button>
      <div id="plan-c-feedback-status" class="plan-c-feedback-status"></div>
    `;
    const target = document.querySelector("main") || document.body;
    target.appendChild(box);

    async function send(verdict) {
      const status = document.getElementById("plan-c-feedback-status");
      if (status) status.textContent = "Menyimpan review...";
      const response = await fetch("/api/plan-c/operator-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, verdict: verdict })
      });
      const data = await response.json().catch(() => ({}));
      if (status) status.textContent = data.status || ("HTTP_" + response.status);
      if (verdict === "rejected" && response.ok) {
        setTimeout(() => { window.location.href = "/plan-c/map"; }, 900);
      }
    }

    document.getElementById("plan-c-accept-result").addEventListener("click", () => send("accepted"));
    document.getElementById("plan-c-reject-result").addEventListener("click", () => send("rejected"));
  }

  fetch(`/api/plan-c/session/${encodeURIComponent(sessionId)}/result`, { cache: "no-store" })
    .then((response) => response.json())
    .then((data) => {
      const result = data.result_ready ? data : {};
      addOperatorPanel(result);
      addFeedbackButtons();
    })
    .catch(() => addFeedbackButtons());
})();
