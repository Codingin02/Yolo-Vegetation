# Auto Label Review Result

## Prinsip

Pre-label System C bersifat review-only.

Tidak ada label yang dianggap ground truth sebelum review manual. Negative sample boleh tanpa file `.txt` jika tidak memiliki objek kelas target.

## Format Label

Format YOLO detection:

```text
class x_center y_center width height
```

Koordinat harus normalized `0..1`, class id hanya `0`, `1`, `2`, atau `3`.

## Class Order

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono
```

## Status

Jika engine pre-label tidak tersedia, status yang benar adalah review manual, bukan membuat bbox palsu.
