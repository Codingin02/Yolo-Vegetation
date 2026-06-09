from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(r"E:\Projects\ULP_Project")

TARGETS = [
    ROOT / "src" / "ulp_project" / "field_capture_routes.py",
    ROOT / "src" / "ulp_project" / "field_session_runtime.py",
]

changed = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore").replace("\r\n", "\n").replace("\r", "\n")


def write(path: Path, text: str) -> None:
    # hilangkan trailing whitespace agar git diff --check tidak gagal
    lines = [line.rstrip() for line in text.split("\n")]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")


for path in TARGETS:
    if not path.exists():
        continue

    old = read(path)
    text = old

    # 1. Status GPS pending tidak boleh menjadi status start utama.
    text = text.replace(
        '"FIELD_SESSION_START_READY_GPS_PENDING"',
        '"FIELD_SESSION_STARTED"'
    )
    text = text.replace(
        "'FIELD_SESSION_START_READY_GPS_PENDING'",
        "'FIELD_SESSION_STARTED'"
    )

    # 2. Pesan jangan menyiratkan kamera harus menunggu GPS.
    text = text.replace(
        "Session ready but GPS coordinates not yet available; waiting for GPS fix",
        "Session started; GPS coordinates may arrive later through gps-update"
    )
    text = text.replace(
        "waiting for GPS fix",
        "GPS may arrive later through gps-update"
    )

    # 3. camera_url None/null pada response start harus diganti fallback camera URL.
    # Asumsi umum: variable session_id sudah ada karena response sudah mengembalikan session_id.
    text = re.sub(
        r'("camera_url"\s*:\s*)None',
        r'\1f"/field-camera?session_id={session_id}"',
        text
    )
    text = re.sub(
        r"('camera_url'\s*:\s*)None",
        r"\1f'/field-camera?session_id={session_id}'",
        text
    )
    text = re.sub(
        r'("camera_url"\s*:\s*)null',
        r'\1f"/field-camera?session_id={session_id}"',
        text
    )

    # 4. Kalau ada assignment camera_url = None pada jalur start, ubah jadi URL kamera.
    # Ini aman selama variable session_id ada. Jika tidak ada, compile/test akan menangkap.
    text = re.sub(
        r"(?m)^(\s*)camera_url\s*=\s*None\s*$",
        r'\1camera_url = f"/field-camera?session_id={session_id}"',
        text
    )

    # 5. recording_status tidak boleh STOPPED pada response start.
    # Dibuat targeted ke teks umum.
    text = text.replace(
        '"recording_status": "RECORDING_STOPPED"',
        '"recording_status": "RECORDING_ACTIVE"'
    )
    text = text.replace(
        "'recording_status': 'RECORDING_STOPPED'",
        "'recording_status': 'RECORDING_ACTIVE'"
    )

    # 6. Kalau gps_ready false, itu boleh, tapi bukan alasan blocking kamera.
    # Jangan ubah gps_ready. Biarkan jujur.

    if text != old:
        write(path, text)
        changed.append(str(path.relative_to(ROOT)).replace("\\", "/"))


if not changed:
    raise SystemExit("NO_FILE_CHANGED__GPS_PENDING_PATTERN_NOT_FOUND")

print("PROGRESS7_FORCE_NO_GPS_CAMERA_START_FIX_DONE")
for item in changed:
    print("-", item)
