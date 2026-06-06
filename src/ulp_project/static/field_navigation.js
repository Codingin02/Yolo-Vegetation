(function () {
  function currentSessionId() {
    const params = new URLSearchParams(window.location.search);
    return params.get("session_id") || window.localStorage.getItem("field_session_id") || "";
  }

  function preserveSessionUrl(path) {
    const sessionId = currentSessionId();
    if (!sessionId) return path;
    const url = new URL(path, window.location.origin);
    url.searchParams.set("session_id", sessionId);
    return url.pathname + url.search;
  }

  function go(path) {
    document.body.classList.add("page-transitioning");
    window.setTimeout(function () {
      window.location.href = preserveSessionUrl(path);
    }, 180);
  }

  function bind(id, path) {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("click", function () {
      go(path);
    });
  }

  window.FieldNavigation = {
    currentSessionId,
    preserveSessionUrl,
    go
  };

  bind("session-report", "/field-report");
  bind("session-result", "/field-result");
  bind("session-manual-input", "/field-manual-input");
})();
