"""GPS/Folium scaffold that reports partial readiness instead of inventing coordinates."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from .paths import GPS_FIELD_POINTS_DIR, RESULTS_MAP_DIR


@dataclass(frozen=True)
class FieldPoint:
    name: str
    latitude: float
    longitude: float
    source: Path


def _parse_float_pair(text: str) -> tuple[float, float] | None:
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*[,;\s]\s*(-?\d+(?:\.\d+)?)", text)
    if not match:
        return None
    first = float(match.group(1))
    second = float(match.group(2))
    if -90 <= first <= 90 and -180 <= second <= 180:
        return first, second
    if -90 <= second <= 90 and -180 <= first <= 180:
        return second, first
    return None


def _parse_txt(path: Path) -> list[FieldPoint]:
    pair = _parse_float_pair(path.read_text(encoding="utf-8", errors="ignore"))
    if not pair:
        return []
    return [FieldPoint(path.stem, pair[0], pair[1], path)]


def _parse_csv(path: Path) -> list[FieldPoint]:
    points: list[FieldPoint] = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lat = row.get("latitude") or row.get("lat")
            lon = row.get("longitude") or row.get("lon") or row.get("lng")
            if not lat or not lon:
                continue
            try:
                latitude = float(lat)
                longitude = float(lon)
            except ValueError:
                continue
            name = row.get("point_name") or row.get("point_id") or path.stem
            points.append(FieldPoint(name, latitude, longitude, path))
    return points


def _parse_kml(path: Path) -> list[FieldPoint]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    points: list[FieldPoint] = []
    for index, match in enumerate(re.finditer(r"<coordinates>\s*([^<]+)\s*</coordinates>", text), start=1):
        raw = match.group(1).strip().split()[0].split(",")
        if len(raw) < 2:
            continue
        try:
            longitude = float(raw[0])
            latitude = float(raw[1])
        except ValueError:
            continue
        points.append(FieldPoint(f"{path.stem}_{index}", latitude, longitude, path))
    return points


def _parse_gpx(path: Path) -> list[FieldPoint]:
    try:
        import gpxpy
    except ImportError:
        return []
    with path.open(encoding="utf-8", errors="ignore") as handle:
        gpx = gpxpy.parse(handle)
    points: list[FieldPoint] = []
    for index, waypoint in enumerate(gpx.waypoints, start=1):
        points.append(FieldPoint(waypoint.name or f"{path.stem}_{index}", waypoint.latitude, waypoint.longitude, path))
    return points


def read_field_points(gps_dir: Path = GPS_FIELD_POINTS_DIR) -> list[FieldPoint]:
    if not gps_dir.exists():
        return []
    points: list[FieldPoint] = []
    for path in sorted(item for item in gps_dir.rglob("*") if item.is_file()):
        suffix = path.suffix.lower()
        if suffix == ".txt":
            points.extend(_parse_txt(path))
        elif suffix == ".csv":
            points.extend(_parse_csv(path))
        elif suffix == ".kml":
            points.extend(_parse_kml(path))
        elif suffix == ".gpx":
            points.extend(_parse_gpx(path))
    return points


def build_map(points: list[FieldPoint], output: Path) -> str:
    if not points:
        return "GPS_DATA_NOT_READY"
    try:
        import folium
    except ImportError:
        return "DEPENDENCY_MISSING_FOLIUM"
    center = [sum(point.latitude for point in points) / len(points), sum(point.longitude for point in points) / len(points)]
    fmap = folium.Map(location=center, zoom_start=16, tiles="CartoDB Positron")
    for point in points:
        folium.Marker([point.latitude, point.longitude], popup=point.name, tooltip=point.name).add_to(fmap)
    output.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output))
    return "READY"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Folium field map from real GPS files only.")
    parser.add_argument("--gps-dir", type=Path, default=GPS_FIELD_POINTS_DIR)
    parser.add_argument("--output", type=Path, default=RESULTS_MAP_DIR / "field_points_map.html")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    points = read_field_points(args.gps_dir)
    if args.mode == "dry-run":
        print(f"status: {'READY' if points else 'GPS_DATA_NOT_READY'}")
        print(f"points_found: {len(points)}")
        print(f"output: {args.output}")
        print("written: False")
        return 0
    status = build_map(points, args.output)
    print(f"status: {status}")
    print(f"points_found: {len(points)}")
    if status == "READY":
        print(f"output: {args.output}")
    return 0 if status in {"READY", "GPS_DATA_NOT_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
