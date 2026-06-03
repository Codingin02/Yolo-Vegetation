from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data" / "templates" / "environmental_manual_template.csv"
HEADER = "timestamp,location_name,latitude,longitude,season,rainfall_mm_day,rainfall_mm_7d,temperature_c,relative_humidity_percent,soil_ph,soil_moisture,solar_radiation,wind_speed,source_name,source_url,operator_notes\n"


def main() -> int:
    TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE.exists() or "location_name" not in TEMPLATE.read_text(encoding="utf-8").splitlines()[0]:
        TEMPLATE.write_text(HEADER, encoding="utf-8")
    print(f"ENVIRONMENTAL_TEMPLATE_READY: {TEMPLATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
