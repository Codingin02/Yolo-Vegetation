# System Finalization Plan

Tujuan branch `system-finalization-no-label-touch` adalah menyiapkan pipeline setelah labeling selesai tanpa mengganggu proses labeling aktif.

## Komponen

1. Import label YOLO hasil makesense.ai dengan default dry-run.
2. Validator label YOLO untuk class `0/1/2`.
3. Builder dataset `field_multiclass_v1` dengan split deterministic.
4. Generator `data.yaml`.
5. Training launcher YOLOv8 dengan mode aman.
6. Flask dashboard/API scaffold.
7. GPS/Folium map scaffold.
8. Export metadata CSV lokal.
9. Risk skeleton tanpa angka asumsi.
10. Tests minimal.

## Batas Aman

Pipeline sistem hanya membaca folder labeling sampai user menjalankan mode copy/build secara eksplisit setelah export selesai.

Tidak ada training final pada tahap ini.
