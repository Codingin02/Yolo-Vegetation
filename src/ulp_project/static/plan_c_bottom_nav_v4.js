
(function () {
  "use strict";

  const isResult = location.pathname.includes("/plan-c/result/");
  if (!isResult) return;

  document.body.classList.add("pcv4-result-body");

  const sessionMatch = location.pathname.match(/\/plan-c\/result\/([^/?#]+)/);
  const sessionId = sessionMatch ? decodeURIComponent(sessionMatch[1]) : "";

  function hideOldOperatorButtons() {
    const nodes = Array.from(document.querySelectorAll("a,button"));
    nodes.forEach(node => {
      if (node.closest(".pcv4-result-bottom-nav")) return;
      const text = (node.textContent || "").trim().toLowerCase();
      if (text === "map" || text === "developer" || text === "new") {
        node.style.display = "none";
      }
    });
  }

  async function startNewCameraSession() {
    try {
      const resp = await fetch("/api/plan-c/session/start", { method: "POST", cache: "no-store" });
      const data = await resp.json();
      const sid = data.session_id || data.session || (data.result && data.result.session_id);
      if (sid) {
        window.location.href = "/plan-c/capture/" + encodeURIComponent(sid);
        return;
      }
    } catch (_) {}

    window.location.href = "/plan-c";
  }

  function addNav() {
    if (document.getElementById("pcv4-result-bottom-nav")) return;

    const nav = document.createElement("nav");
    nav.id = "pcv4-result-bottom-nav";
    nav.className = "pcv4-result-bottom-nav";
    nav.innerHTML = `
      <a class="pcv4-nav-item" href="/plan-c">Home</a>
      <button class="pcv4-nav-item" type="button" id="pcv4-result-camera">Kamera</button>
      <a class="pcv4-nav-item" href="/plan-c/map">Map</a>
      <a class="pcv4-nav-item active" href="${sessionId ? "/plan-c/result/" + encodeURIComponent(sessionId) : location.pathname}">Result</a>
    `;
    document.body.appendChild(nav);

    const cameraBtn = document.getElementById("pcv4-result-camera");
    if (cameraBtn) cameraBtn.addEventListener("click", startNewCameraSession);
  }

  function boot() {
    hideOldOperatorButtons();
    addNav();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
