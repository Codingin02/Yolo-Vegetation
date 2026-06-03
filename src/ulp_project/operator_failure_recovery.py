"""Operator failure-recovery decision tree for HP/ngrok field trials."""

from __future__ import annotations

from typing import Any


def build_failure_recovery(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the most useful next operator action for a field-trial failure."""

    url_attempted = _text(payload.get("url_attempted") or payload.get("public_url") or payload.get("opened_url"))
    hp_can_open_url = _bool_or_none(payload.get("hp_can_open_url"))
    tunnel_status = _text(payload.get("tunnel_status"), "UNKNOWN")
    server_status = _text(payload.get("server_status"), "UNKNOWN")
    camera_status = _text(payload.get("camera_status"), "UNKNOWN")
    gps_status = _text(payload.get("gps_status"), "UNKNOWN")
    websocket_status = _text(payload.get("websocket_status"), "UNKNOWN")
    report_status = _text(payload.get("report_status"), "UNKNOWN")
    map_status = _text(payload.get("map_status"), "UNKNOWN")
    model_status = _text(payload.get("model_status"), "MODEL_NOT_READY")
    calibration_status = _text(payload.get("calibration_status"), "CALIBRATION_NOT_READY")

    if "localhost" in url_attempted.lower() or "127.0.0.1" in url_attempted:
        return _decision(
            "HIGH",
            "HP menggunakan localhost, padahal localhost di HP berarti HP sendiri.",
            "Gunakan public ngrok HTTPS URL atau LAN IP laptop.",
            "ngrok http 5000",
            "Buka https://<ngrok-public-url>/field-capture dari HP.",
        )
    if hp_can_open_url is False and tunnel_status in {"NGROK_NOT_RUNNING", "PUBLIC_TUNNEL_NOT_RUNNING", "NGROK_CLI_FOUND_BUT_TUNNEL_NOT_RUNNING"}:
        return _decision(
            "HIGH",
            "Public tunnel belum berjalan atau sudah expired.",
            "Jalankan ulang ngrok lalu buka URL HTTPS baru dari HP.",
            "ngrok http 5000",
            "Jangan menyimpan token atau URL runtime tunnel ke Git.",
        )
    if hp_can_open_url is False and "LAN" in url_attempted.upper():
        return _decision(
            "HIGH",
            "HP dan laptop kemungkinan beda jaringan atau Windows Firewall memblokir port.",
            "Pakai ngrok HTTPS untuk paket data, atau izinkan Python di Windows Firewall Private Network.",
            ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --ngrok-probe",
            "Script tidak mengubah firewall otomatis.",
        )
    if hp_can_open_url is False or server_status in {"LOCAL_SERVER_HEALTH_NOT_REACHABLE", "SERVER_DOWN", "NOT_RUNNING"}:
        return _decision(
            "HIGH",
            "Server Flask field-trial belum berjalan atau port salah.",
            "Jalankan server field-trial pada host 0.0.0.0 dan port 5000.",
            ".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000",
            "Ini tetap field-trial/dev server, bukan production deployment permanen.",
        )
    if camera_status in {"CAMERA_API_UNAVAILABLE_IN_THIS_CONTEXT", "CAMERA_PERMISSION_DENIED", "CAMERA_NOT_READY"}:
        return _decision(
            "MEDIUM",
            "Kamera diblokir oleh insecure context atau permission browser.",
            "Buka HTTPS ngrok URL, beri izin kamera, lalu reload halaman.",
            "ngrok http 5000",
            "Fallback aman tetap tersedia: upload image manual tanpa fake detection.",
        )
    if gps_status in {"GPS_PERMISSION_DENIED", "GPS_TIMEOUT", "GPS_API_UNAVAILABLE_IN_THIS_CONTEXT", "GPS_NOT_READY"}:
        return _decision(
            "MEDIUM",
            "GPS browser belum diizinkan atau timeout.",
            "Aktifkan Location permission di browser/Android dan ulangi Ambil GPS.",
            "Buka Settings browser > Site settings > Location > Allow",
            "Jika lat/lon diisi manual, status harus GPS_SOURCE_MANUAL; tanpa GPS map marker tidak dibuat.",
        )
    if websocket_status in {"WEBSOCKET_ERROR_HTTP_FALLBACK", "WEBSOCKET_UNAVAILABLE_HTTP_FALLBACK", "WEBSOCKET_FAILED"}:
        return _decision(
            "LOW",
            "Tunnel/proxy tidak mendukung WebSocket atau koneksi tidak stabil.",
            "Gunakan fallback HTTP 1 FPS dan lanjutkan snapshot manual/provisional.",
            "Tidak perlu command tambahan; UI otomatis fallback HTTP.",
            "Jangan menulis report setiap frame.",
        )
    if report_status in {"REPORT_NOT_WRITTEN", "SNAPSHOT_REPORT_FAILED", "NOT_WRITABLE"}:
        return _decision(
            "HIGH",
            "Folder output tidak writable atau snapshot payload invalid.",
            "Jalankan diagnose dan report smoke untuk melihat error spesifik.",
            ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --actual-runtime-smoke",
            "Report resmi hanya ditulis saat snapshot submit.",
        )
    if map_status in {"MAP_NOT_WRITTEN", "NO_GPS_NO_MARKER"}:
        return _decision(
            "LOW",
            "Map marker tidak dibuat karena GPS belum valid.",
            "Ambil GPS HP atau isi lat/lon manual dengan status GPS_SOURCE_MANUAL.",
            "Buka /field-trial-checklist dan catat status GPS.",
            "Jangan membuat koordinat palsu.",
        )
    if model_status == "MODEL_NOT_READY":
        return _decision(
            "INFO",
            "best.pt custom belum tersedia atau belum valid.",
            "Lanjut manual/provisional mode; jangan klaim real model.",
            ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --check-model",
            "detections tetap [] sampai model custom valid.",
        )
    if calibration_status.startswith("CALIBRATION_NOT"):
        return _decision(
            "INFO",
            "Profil kalibrasi lapangan belum dibuat.",
            "Hasil tetap provisional; lakukan kalibrasi setelah field marker/reference tersedia.",
            ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --check-calibration",
            "Kalibrasi wajib sebelum klaim hasil final.",
        )
    return _decision(
        "INFO",
        "Tidak ada kegagalan prioritas tinggi dari input diagnostic.",
        "Lanjutkan checklist field trial dan evidence pack.",
        ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --evidence-pack",
        "HP physical test tetap perlu konfirmasi operator.",
    )


def _decision(severity: str, likely_cause: str, next_action: str, exact_command: str, operator_note: str) -> dict[str, str]:
    return {
        "status": "FAILURE_RECOVERY_DECISION_READY",
        "severity": severity,
        "likely_cause": likely_cause,
        "next_action": next_action,
        "exact_command": exact_command,
        "operator_note": operator_note,
    }


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return None
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "ya", "ok"}:
        return True
    if lowered in {"false", "0", "no", "tidak"}:
        return False
    return None


def _text(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value)
