from pathlib import Path
from collections import defaultdict
import shutil


PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")

EXPORT_ROOT = PROJECT_ROOT / "data" / "exports" / "make_sense" / "V001_pohon_sono"
EXTRACT_DIR = EXPORT_ROOT / "extracted_latest"
PROJECT_ORDER_DIR = EXPORT_ROOT / "project_order_labels"

EXPECTED_PROJECT_CLASSES = {
    0: "struktur_penyangga",
    1: "konduktor",
    2: "pohon_sono",
}


def parse_label_file(path: Path):
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) != 5:
            raise ValueError(f"{path.name}:{line_no} format bukan 5 kolom: {line}")

        cls = int(parts[0])
        x, y, w, h = map(float, parts[1:])
        area = w * h
        rows.append((cls, x, y, w, h, area))

    return rows


def infer_mapping(label_files):
    area_by_class = defaultdict(list)

    for path in label_files:
        rows = parse_label_file(path)
        for cls, x, y, w, h, area in rows:
            area_by_class[cls].append(area)

    class_ids = sorted(area_by_class.keys())

    print("=== DETECTED MAKE SENSE CLASS IDS ===")
    for cls in class_ids:
        areas = area_by_class[cls]
        print(
            f"class {cls}: count={len(areas)}, "
            f"max_area={max(areas):.6f}, avg_area={sum(areas)/len(areas):.6f}"
        )

    if not class_ids:
        raise RuntimeError("Tidak ada baris label di export MakeSense.")

    # Jika MakeSense sudah memakai class project 0/1/2 dan ada class 2,
    # kita anggap tidak perlu remap.
    if 2 in class_ids:
        mapping = {cls: cls for cls in class_ids}
        print("\nMapping mode: ALREADY_PROJECT_ORDER")
        return mapping

    # Untuk V001, objek pohon_sono adalah box terbesar.
    # Jadi class dengan area rata-rata terbesar dipetakan ke class 2.
    pohon_cls = max(class_ids, key=lambda c: sum(area_by_class[c]) / len(area_by_class[c]))

    mapping = {}
    for cls in class_ids:
        if cls == pohon_cls:
            mapping[cls] = 2
        else:
            mapping[cls] = 1

    print("\nMapping mode: INFER_FROM_BOX_AREA")
    print(f"MakeSense class {pohon_cls} dianggap pohon_sono -> project class 2")
    for cls in class_ids:
        if cls != pohon_cls:
            print(f"MakeSense class {cls} dianggap konduktor -> project class 1")

    return mapping


def remap_files(label_files, mapping):
    if PROJECT_ORDER_DIR.exists():
        shutil.rmtree(PROJECT_ORDER_DIR)

    PROJECT_ORDER_DIR.mkdir(parents=True, exist_ok=True)

    for path in label_files:
        output_rows = []

        for cls, x, y, w, h, area in parse_label_file(path):
            if cls not in mapping:
                raise ValueError(f"Class {cls} tidak ada mapping untuk file {path.name}")

            new_cls = mapping[cls]

            if new_cls not in EXPECTED_PROJECT_CLASSES:
                raise ValueError(f"Mapping menghasilkan class tidak valid: {new_cls}")

            output_rows.append(f"{new_cls} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")

        out_path = PROJECT_ORDER_DIR / path.name
        out_path.write_text("\n".join(output_rows), encoding="utf-8")

    print("\n=== REMAP SUMMARY ===")
    print(f"Input dir  : {EXTRACT_DIR}")
    print(f"Output dir : {PROJECT_ORDER_DIR}")
    print(f"Files remapped: {len(label_files)}")
    print("Project class order:")
    print("0 struktur_penyangga")
    print("1 konduktor")
    print("2 pohon_sono")


def main():
    if not EXTRACT_DIR.exists():
        raise FileNotFoundError(f"Folder extracted_latest tidak ditemukan: {EXTRACT_DIR}")

    label_files = sorted(EXTRACT_DIR.glob("*.txt"))

    if not label_files:
        raise FileNotFoundError(f"Tidak ada .txt label di: {EXTRACT_DIR}")

    mapping = infer_mapping(label_files)
    remap_files(label_files, mapping)


if __name__ == "__main__":
    main()
