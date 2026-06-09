from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
js_path = ROOT / "src" / "ulp_project" / "static" / "progress6_24_realtime_vision_switch.js"

text = js_path.read_text(encoding="utf-8", errors="replace")
original = text

patches = []

def replace_once(old, new, label):
    global text
    if old in text:
        text = text.replace(old, new, 1)
        patches.append(label)
    elif new in text:
        patches.append(label + "_ALREADY")
    else:
        raise RuntimeError(f"PATCH_PATTERN_NOT_FOUND: {label}")

replace_once(
    "const REQUEST_TIMEOUT_MS = 4500;",
    "const REQUEST_TIMEOUT_MS = 18000;\n  const CLOUD_MIN_INTERVAL_MS = 5000;",
    "increase_timeout_and_add_cloud_min_interval",
)

replace_once(
    'if (elapsed < LOOP_INTERVAL_MS - 50) return;',
    'if (elapsed < CLOUD_MIN_INTERVAL_MS - 50) return;',
    "use_cloud_min_interval_for_api_request",
)

replace_once(
    'try { controller.abort(); } catch (_) {}',
    'try { controller.abort("P625_VISION_CLOUD_TIMEOUT_AFTER_18S"); } catch (_) {}',
    "add_abort_reason",
)

replace_once(
    'setPrediction("busy", "◈", "AI membaca frame realtime... tick " + state.tickCount);',
    'setPrediction("busy", "◈", "AI membaca frame realtime... tick " + state.tickCount + " | cloud latest-only");',
    "clarify_latest_only_status",
)

replace_once(
    'state.lastError = err && err.message ? err.message : String(err);',
    '''
      const rawError = err && err.message ? err.message : String(err);
      if (rawError === "signal is aborted without reason" || rawError.includes("aborted without reason")) {
        state.lastError = "VISION_TIMEOUT_CLIENT_ABORT_PREVENTED_BY_P625_RELOAD_REQUIRED";
      } else if (rawError.includes("P625_VISION_CLOUD_TIMEOUT_AFTER_18S")) {
        state.lastError = "VISION_CLOUD_TIMEOUT_AFTER_18S";
      } else {
        state.lastError = rawError;
      }
'''.rstrip(),
    "normalize_abort_error_message",
)

# Tambahkan cache result ke localStorage supaya Shutter bisa ikut evidence terbaru bila backend membaca field tambahan.
cache_anchor = 'window.PROGRESS_6_24_LAST_REALTIME_VISION_RESULT = result;'
cache_insert = '''
      window.PROGRESS_6_24_LAST_REALTIME_VISION_RESULT = result;
      try {
        window.localStorage.setItem("P625_LAST_VISION_RESULT", JSON.stringify({
          saved_at: new Date().toISOString(),
          session_id: getSessionId(),
          point_id: getPointId(),
          result: result
        }));
      } catch (_) {}
'''.rstrip()

if cache_anchor in text and "P625_LAST_VISION_RESULT" not in text:
    text = text.replace(cache_anchor, cache_insert, 1)
    patches.append("cache_last_vision_result")
elif "P625_LAST_VISION_RESULT" in text:
    patches.append("cache_last_vision_result_ALREADY")
else:
    raise RuntimeError("PATCH_PATTERN_NOT_FOUND: cache_last_vision_result")

# Patch fetch guard agar body shutter membawa snapshot vision terakhir sebagai metadata tambahan.
fetch_return_anchor = "return state.nativeFetch(input, init);"
fetch_guard_insert = r'''
      if (url.includes("/api/field/session/shutter") && init && typeof init.body === "string") {
        try {
          const lastRaw = window.localStorage.getItem("P625_LAST_VISION_RESULT");
          if (lastRaw) {
            const bodyObj = JSON.parse(init.body);
            bodyObj.vision_result_cache = JSON.parse(lastRaw);
            bodyObj.vision_result_cache_status = "P625_ATTACHED_FRONTEND_CACHE";
            const nextInit = Object.assign({}, init, { body: JSON.stringify(bodyObj) });
            return state.nativeFetch(input, nextInit);
          }
        } catch (_) {}
      }

      return state.nativeFetch(input, init);
'''.rstrip()

if fetch_return_anchor in text and "vision_result_cache_status" not in text:
    text = text.replace(fetch_return_anchor, fetch_guard_insert, 1)
    patches.append("attach_last_vision_result_to_shutter")
elif "vision_result_cache_status" in text:
    patches.append("attach_last_vision_result_to_shutter_ALREADY")
else:
    raise RuntimeError("PATCH_PATTERN_NOT_FOUND: attach_last_vision_result_to_shutter")

# Tambahkan status object supaya bisa dicek dari console.
status_anchor = 'request_timeout_ms: REQUEST_TIMEOUT_MS,'
status_insert = 'request_timeout_ms: REQUEST_TIMEOUT_MS,\n      cloud_min_interval_ms: CLOUD_MIN_INTERVAL_MS,\n      patch_6_25: "ABORT_FIX_CLOUD_SAFE",'
if status_anchor in text and "patch_6_25" not in text:
    text = text.replace(status_anchor, status_insert, 1)
    patches.append("expose_625_status")
elif "patch_6_25" in text:
    patches.append("expose_625_status_ALREADY")
else:
    raise RuntimeError("PATCH_PATTERN_NOT_FOUND: expose_625_status")

js_path.write_text(text, encoding="utf-8")

print("PATCHED:", js_path.relative_to(ROOT))
for p in patches:
    print(" -", p)

if text == original:
    print("NO_TEXT_CHANGE_BUT_PATTERNS_ALREADY_OK")

print("PROGRESS_6_25_JS_ABORT_FIX_PATCH_PASS")
