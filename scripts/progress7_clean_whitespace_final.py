from pathlib import Path

ROOT = Path(r"E:\Projects\ULP_Project")

files = [
    "scripts/final_live_yolo_frame_ui_smoke.py",
    "scripts/progress7_start_contract_no_gps_test.py",
    "scripts/progress7_force_no_gps_camera_start_fix.py",
    "src/ulp_project/field_capture_routes.py",
    "src/ulp_project/field_session_runtime.py",
    "src/ulp_project/runtime_yolo_status.py",
    "src/ulp_project/static/field_camera.js",
    "src/ulp_project/static/final_live_force_yolo_frame.js",
    "src/ulp_project/static/progress6_27_yolo_first_lock.js",
    "src/ulp_project/templates/field_camera.html",
]

changed = []

for rel in files:
    path = ROOT / rel
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")

    while lines and lines[-1].strip() == "":
        lines.pop()

    lines = [line.rstrip() for line in lines]

    fixed = "\n".join(lines) + "\n"

    if fixed != text:
        path.write_text(fixed, encoding="utf-8", newline="\n")
        changed.append(rel)

print("WHITESPACE_CLEAN_DONE")
for item in changed:
    print("-", item)
