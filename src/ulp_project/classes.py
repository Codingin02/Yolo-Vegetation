"""Locked YOLO class order for the ULP field dataset."""

CLASS_ORDER = {
    0: "struktur_penyangga",
    1: "konduktor",
    2: "pohon_sono",
}

CLASS_NAMES = [CLASS_ORDER[index] for index in sorted(CLASS_ORDER)]


def validate_class_id(class_id: int) -> bool:
    return class_id in CLASS_ORDER


def data_yaml_names_block() -> dict[int, str]:
    return dict(CLASS_ORDER)
