# Phase 5.2 Prediction Limitations and Safety

## Status Model

Jika custom YOLO `best.pt` belum tersedia atau belum valid:

```text
MODEL_NOT_READY
detections = []
```

Sistem tetap dapat dipakai untuk:

- kamera/browser field capture
- GPS/manual GPS
- prediksi manual/provisional
- snapshot CSV
- map jika GPS valid
- diagnostics dan operator smoke test

## Tidak Ada Fake Detection

Sistem tidak boleh membuat bounding box palsu sebagai hasil real. Demo mock hanya boleh aktif jika flag eksplisit `--demo-mock` dan harus berlabel:

```text
DEMO_MOCK_NOT_REAL_FIELD_RESULT
```

## ETA Prototype

Threshold prototype:

```text
clearance_threshold_m = 3.0
```

Jika `clearance_m > 3.0`:

```text
eta_days = (clearance_m - 3.0) / adjusted_growth_rate_m_per_day
```

Jika `clearance_m <= 3.0`:

```text
eta_days = 0
risk_status = ALREADY_WITHIN_UNSAFE_ZONE
action_priority = CRITICAL
```

Display meter memakai floor integer, tetapi raw value tetap disimpan.

Contoh:

```text
raw = 2.75
display = 2
eta_days = 0
```

## Confidence

Manual input menghasilkan:

```text
confidence_status = MANUAL_PROVISIONAL
```

Jika calibration belum siap, reason code tetap menyertakan:

```text
CALIBRATION_NOT_READY
```

## Batasan

Belum final tanpa:

- label makesense.ai selesai
- training YOLO custom
- validasi class order model
- kalibrasi lapangan
- ground truth field validation
- data lingkungan nyata/manual CSV terverifikasi

Jangan menulis klaim seperti akurasi final, pasti naik/turun, atau instruksi tindakan mutlak.
