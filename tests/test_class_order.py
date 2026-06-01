from ulp_project.classes import CLASS_ORDER, CLASS_NAMES


def test_class_order_locked():
    assert CLASS_ORDER == {
        0: "struktur_penyangga",
        1: "konduktor",
        2: "pohon_sono",
    }
    assert CLASS_NAMES == ["struktur_penyangga", "konduktor", "pohon_sono"]
