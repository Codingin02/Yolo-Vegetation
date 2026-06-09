/* PROGRESS_6_23_IOS_GLASS_3D_INTERACTIVE_UI */
/* UI-only layer: 3D push, ripple, haptic, icons. Does not change detection result. */

(function () {
  "use strict";

  const VERSION = "PROGRESS_6_23_IOS_GLASS_3D_INTERACTIVE_UI";

  const ICONS = {
    home: "⌂",
    map: "⌖",
    result: "▤",
    manual: "✎",
    shutter: "●",
    vision: "◈",
    gps: "⌁",
    default: "◆"
  };

  const state = {
    toast: null,
    lastToast: 0
  };

  function qsa(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function textOf(el) {
    return ((el && (el.innerText || el.textContent || el.value || el.getAttribute("aria-label") || "")) || "").trim();
  }

  function haystack(el) {
    if (!el) return "";
    return [
      el.id || "",
      el.className || "",
      el.getAttribute("aria-label") || "",
      el.getAttribute("title") || "",
      el.getAttribute("data-action") || "",
      el.getAttribute("data-role") || "",
      textOf(el)
    ].join(" ").toLowerCase();
  }

  function isInteractive(el) {
    if (!el) return false;
    if (el.disabled) return false;
    const tag = (el.tagName || "").toLowerCase();
    const role = (el.getAttribute && el.getAttribute("role")) || "";
    const hay = haystack(el);

    return (
      tag === "button" ||
      tag === "a" ||
      role === "button" ||
      tag === "input" ||
      hay.includes("shutter") ||
      hay.includes("jepret") ||
      hay.includes("capture") ||
      hay.includes("map") ||
      hay.includes("result") ||
      hay.includes("manual") ||
      hay.includes("home") ||
      hay.includes("vision")
    );
  }

  function classify(el) {
    const h = haystack(el);
    if (h.includes("home") || h.includes("kembali")) return "home";
    if (h.includes("map") || h.includes("peta")) return "map";
    if (h.includes("result") || h.includes("spreadsheet") || h.includes("hasil")) return "result";
    if (h.includes("manual")) return "manual";
    if (h.includes("shutter") || h.includes("jepret") || h.includes("capture") || h.includes("snapshot")) return "shutter";
    if (h.includes("vision") || h.includes("analyze") || h.includes("analisis")) return "vision";
    if (h.includes("gps")) return "gps";
    return "default";
  }

  function vibrate(pattern) {
    try {
      if (navigator && typeof navigator.vibrate === "function") {
        navigator.vibrate(pattern);
      }
    } catch (_) {}
  }

  function ensureToast() {
    if (state.toast) return state.toast;

    const toast = document.createElement("div");
    toast.className = "p623-ui-toast";
    toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);
    state.toast = toast;
    return toast;
  }

  function showToast(message) {
    const now = Date.now();
    if (now - state.lastToast < 240) return;
    state.lastToast = now;

    const toast = ensureToast();
    toast.textContent = message;
    toast.classList.add("p623-show");

    window.clearTimeout(toast._p623Timer);
    toast._p623Timer = window.setTimeout(function () {
      toast.classList.remove("p623-show");
    }, 1350);
  }

  function addIcon(el) {
    if (!el || el.dataset.p623IconAdded === "1") return;

    const kind = classify(el);

    if (kind === "default") {
      el.dataset.p623IconAdded = "1";
      return;
    }

    if (kind === "shutter") {
      el.classList.add("p623-shutter-3d");
      el.dataset.p623IconAdded = "1";
      return;
    }

    const existing = el.querySelector && el.querySelector(".p623-icon");
    if (existing) {
      el.dataset.p623IconAdded = "1";
      return;
    }

    const icon = document.createElement("span");
    icon.className = "p623-icon";
    icon.textContent = ICONS[kind] || ICONS.default;
    icon.setAttribute("aria-hidden", "true");

    try {
      el.insertBefore(icon, el.firstChild);
    } catch (_) {}

    el.dataset.p623IconAdded = "1";
  }

  function installBaseClass(el) {
    if (!el || el.dataset.p623PressInstalled === "1") return;
    if (!isInteractive(el)) return;

    el.classList.add("p623-pressable");
    addIcon(el);
    el.dataset.p623PressInstalled = "1";

    el.addEventListener("pointermove", function (ev) {
      const rect = el.getBoundingClientRect();
      if (!rect.width || !rect.height) return;

      const x = Math.max(0, Math.min(rect.width, ev.clientX - rect.left));
      const y = Math.max(0, Math.min(rect.height, ev.clientY - rect.top));

      const px = (x / rect.width) * 100;
      const py = (y / rect.height) * 100;

      const ry = ((x / rect.width) - 0.5) * 8;
      const rx = -(((y / rect.height) - 0.5) * 8);

      el.style.setProperty("--p623-x", px.toFixed(1) + "%");
      el.style.setProperty("--p623-y", py.toFixed(1) + "%");
      el.style.setProperty("--p623-rx", rx.toFixed(2) + "deg");
      el.style.setProperty("--p623-ry", ry.toFixed(2) + "deg");
      el.classList.add("p623-hover");
    }, {passive: true});

    el.addEventListener("pointerenter", function () {
      el.classList.add("p623-hover");
    }, {passive: true});

    el.addEventListener("pointerleave", function () {
      el.classList.remove("p623-hover", "p623-pressed");
      el.style.removeProperty("--p623-rx");
      el.style.removeProperty("--p623-ry");
    }, {passive: true});

    el.addEventListener("pointerdown", function (ev) {
      if (el.disabled) return;

      el.classList.add("p623-pressed", "p623-shine");

      const kind = classify(el);
      if (kind === "shutter") {
        vibrate([18, 26, 18]);
        showToast("Shutter ditekan: evidence + Vision API diproses");
      } else if (kind === "vision") {
        vibrate(18);
        showToast("Vision analyze berjalan");
      } else if (kind === "map") {
        vibrate(12);
        showToast("Membuka evidence map");
      } else if (kind === "result") {
        vibrate(12);
        showToast("Membuka result spreadsheet");
      } else {
        vibrate(8);
      }

      createRipple(el, ev);

      try {
        el.animate(
          [
            { transform: "translateY(0) scale(1)" },
            { transform: "translateY(5px) scale(.965)" },
            { transform: "translateY(2px) scale(.985)" }
          ],
          { duration: 230, easing: "cubic-bezier(.2,.9,.2,1.15)" }
        );
      } catch (_) {}

      window.setTimeout(function () {
        el.classList.remove("p623-shine");
      }, 760);
    }, {passive: true});

    el.addEventListener("pointerup", function () {
      el.classList.remove("p623-pressed");
      try {
        el.animate(
          [
            { transform: "translateY(4px) scale(.97)" },
            { transform: "translateY(-2px) scale(1.018)" },
            { transform: "translateY(0) scale(1)" }
          ],
          { duration: 240, easing: "cubic-bezier(.2,.9,.2,1.2)" }
        );
      } catch (_) {}
    }, {passive: true});

    el.addEventListener("pointercancel", function () {
      el.classList.remove("p623-pressed");
    }, {passive: true});
  }

  function createRipple(el, ev) {
    const rect = el.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const ripple = document.createElement("span");
    ripple.className = "p623-ripple";

    const x = ev.clientX - rect.left;
    const y = ev.clientY - rect.top;

    ripple.style.left = x + "px";
    ripple.style.top = y + "px";

    const size = Math.max(rect.width, rect.height) * 2.25;
    ripple.style.width = size + "px";
    ripple.style.height = size + "px";

    el.appendChild(ripple);

    try {
      ripple.animate(
        [
          { transform: "translate(-50%, -50%) scale(.05)", opacity: .94 },
          { transform: "translate(-50%, -50%) scale(.66)", opacity: .40 },
          { transform: "translate(-50%, -50%) scale(1)", opacity: 0 }
        ],
        { duration: 520, easing: "cubic-bezier(.18,.84,.32,1)" }
      ).onfinish = function () {
        ripple.remove();
      };
    } catch (_) {
      window.setTimeout(function () { ripple.remove(); }, 560);
    }
  }

  function beautifyVisionFab() {
    const fab = document.getElementById("p622VisionFab");
    if (!fab) return;

    if (!fab.querySelector(".p623-icon")) {
      fab.innerHTML = '<span class="p623-icon" aria-hidden="true">◈</span>';
    }
    fab.setAttribute("aria-label", "Vision Analyze");
    fab.title = "Vision Analyze";
    installBaseClass(fab);
  }

  function beautifyBars() {
    const candidates = qsa("div,nav,section").filter(function (el) {
      const h = haystack(el);
      const r = el.getBoundingClientRect();
      return r.width > 180 && r.height >= 44 && r.height <= 150 && (
        h.includes("bottom") ||
        h.includes("toolbar") ||
        h.includes("camera") ||
        h.includes("nav")
      );
    });

    candidates.forEach(function (el) {
      el.classList.add("p623-bottom-glass");
    });
  }

  function installAll() {
    document.documentElement.setAttribute("data-progress6-23-ios-glass-3d", "ready");
    document.body.classList.add("p623-ios-glass-3d-mode");

    qsa("button,a,[role='button'],input[type='button'],input[type='submit'],.camera-action,.nav-button,.action-button").forEach(installBaseClass);
    beautifyVisionFab();
    beautifyBars();

    qsa("details").forEach(function (d) {
      if (!d.dataset.p623Collapsed) {
        d.open = false;
        d.dataset.p623Collapsed = "1";
      }
    });

    window.PROGRESS_6_23_IOS_GLASS_3D_UI = {
      version: VERSION,
      status: "READY",
      note: "UI interaction layer only; detection backend unchanged."
    };
  }

  function observeDom() {
    const observer = new MutationObserver(function () {
      window.requestAnimationFrame(installAll);
    });

    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: false
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      installAll();
      observeDom();
    });
  } else {
    installAll();
    observeDom();
  }
})();
