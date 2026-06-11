# Progress 8.4 Plan C Final Zone Geometry + UI Integration

Baseline: `2a9793c Implement Progress 8.3 Plan C detection zone engine`.

## Masalah Sebelum 8.4

- Zona pada annotated image masih berisiko memakai bagian bawah gambar sebagai tanah otomatis.
- Result UI sudah menampilkan detection dan prediction, tetapi belum menonjolkan `ground_reference_status`, batas zona, dan status presisi zona.
- Patch Capture UI V4 masih berada di worktree sebagai perubahan lokal dan perlu diintegrasikan sebagai file final.
- Training YOLO belum memiliki gate aman yang terpisah dari runtime web.

## Koreksi Geometri Zona

Screenshot target hanya referensi tampilan, bukan bukti geometri. Progress 8.4 mengunci aturan fisik berikut:

- `ZONA_TEBANG` adalah area 0-3 m di bawah `conductor_y`.
- `ZONA_PANTAU` adalah area lebih dari 3 m sampai 6 m di bawah `conductor_y`.
- `ZONA_AMAN` hanya dibuat dari batas 6 m sampai `ground_reference_y`.
- `ground_reference_y` berasal dari dasar vegetasi/bbox pohon yang terlihat atau input manual, bukan dari bawah foto secara buta.
- Jika konduktor tidak tervalidasi, sistem tidak menggambar zona presisi dan menampilkan `DATA TIDAK CUKUP - KONDUKTOR TIDAK TERVALIDASI`.
- Jika ground reference tidak cukup untuk zona aman, sistem menandai `GROUND_REFERENCE_NOT_ENOUGH_FOR_SAFE_ZONE`.

Field hasil yang ditambahkan atau dipertegas:

- `conductor_y`
- `ground_reference_y`
- `ground_reference_status`
- `meter_per_pixel`
- `meter_per_pixel_source`
- `zone_tebang_y1`, `zone_tebang_y2`
- `zone_pantau_y1`, `zone_pantau_y2`
- `zone_aman_y1`, `zone_aman_y2`
- `zone_status`
- `zone_precision`

## UI Final

Capture UI V4 masuk integrasi final:

- kamera fullscreen,
- shutter di dalam frame,
- bottom nav V4,
- tidak memakai `plan_c_capture.js` lama,
- tidak menampilkan status chip dan manual input lama.

Result UI menampilkan kartu:

- Field trial,
- Prediction,
- Detection,
- Detection + Zone,
- GPS,
- Growth,
- Review.

Operator UI tidak menampilkan nama provider, secret, raw JSON panjang, base64, atau path absolut Windows.

## Dataset dan Training Gate

Training YOLO tidak dijalankan di runtime `/plan-c`. Gate terpisah dibuat melalui:

- `scripts/plan_c_yolo_dataset_gate.py`
- `docs/progress8/PLAN_C_YOLO_DATASET_TRAINING_GATE.md`
- `docs/progress8/PLAN_C_POHON_SONO_DATASET_ACQUISITION_TODO.md`

Gate hanya:

- membaca kandidat dataset lokal,
- membuat manifest review-only dari feedback accepted,
- memvalidasi class order,
- menolak training jika data tidak cukup,
- tidak mengunduh dataset internet,
- tidak membuat model,
- tidak menyalin raw image baru ke Git.

## Validasi

Validasi yang wajib dijalankan sebelum commit:

```powershell
.\venv\Scripts\python.exe -m py_compile src\ulp_project\plan_c_detection_prompt_rules.py src\ulp_project\plan_c_free_vision_schema.py src\ulp_project\plan_c_free_vision_consensus.py src\ulp_project\plan_c_quality_layer.py src\ulp_project\plan_c_zone_overlay.py src\ulp_project\plan_c_yolo_compatible_renderer.py src\ulp_project\plan_c_geometry.py src\ulp_project\plan_c_processor.py src\ulp_project\plan_c_routes.py src\ulp_project\plan_c_feedback_learning.py src\ulp_project\plan_c_map.py scripts\plan_c_detection_zone_smoke.py scripts\plan_c_final_zone_geometry_smoke.py scripts\plan_c_yolo_dataset_gate.py
.\venv\Scripts\python.exe scripts\plan_c_final_zone_geometry_smoke.py
.\venv\Scripts\python.exe scripts\plan_c_detection_zone_smoke.py
.\venv\Scripts\python.exe scripts\plan_c_smoke.py
.\venv\Scripts\python.exe scripts\plan_c_field_trial_hardening_smoke.py
.\venv\Scripts\python.exe scripts\plan_c_free_vision_smoke.py
cmd /c "git diff --check"
```

## Batasan

- Hasil detection dan zona tetap untuk field trial dan review operator.
- Estimasi clearance dan prediction belum menggantikan pengukuran manual PLN.
- Growth untuk `pohon_non_sono` memakai `generic_vegetation_proxy`, bukan klaim final pohon sono.
- Akurasi YOLO tidak diklaim sebelum ada ground truth dan validasi lapangan.

## File yang Sengaja Tidak Disentuh

- `data/raw`
- `data/gps`
- `data/processed`
- `data/dataset_yolo`
- `dataset_botol`
- `runs`
- `weights`
- `models`
- file `.pt`, `.onnx`, `.engine`
- `.env`, token, credential, URL ngrok
- file media runtime
