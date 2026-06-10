# AGENTS.md — Progress 8 Plan C

Project: ULP_Project  
Branch: progress8-plan-c-snapshot-processing  
Final system for laporan akhir magang riset: Plan C Snapshot Processing.

## Decision Lock

Plan A = YOLO-only realtime. Simpan sebagai history riset. Jangan dihapus.  
Plan B = YOLO + AI realtime. Simpan sebagai history riset. Jangan dihapus.  
Plan C = snapshot/manual capture + backend processing. Ini jalur utama final.

## Plan C Definition

Plan C tidak realtime. HP hanya menjadi kamera, GPS client, dan uploader foto. Laptop memproses foto setelah shutter.

Flow:
Home -> Get Started -> GPS/camera permission -> tree anchor GPS -> capture snapshot -> upload -> backend processing -> YOLO -> AI validator optional -> geometry -> growth prediction -> result -> spreadsheet append-only -> map marker append-only.

## Must Not Do

- Jangan menambal /field-camera lama.
- Jangan memakai YOLO-FIRST.
- Jangan memakai AI realtime switch.
- Jangan realtime detection loop.
- Jangan menghapus Plan A/B.
- Jangan edit data/raw, dataset, labels, runs, weights, models.
- Jangan membuat fake detection.
- Jangan membuat fake GPS.
- Jangan membuat fake prediction.
- Jangan git add .
- Jangan commit API key.
- Jangan klaim akurasi final PLN.

## Technology Roles

YOLO:
- post-capture object detection,
- bounding box,
- class confidence,
- annotated image.

AI vision:
- visual validation,
- second opinion,
- narrative summary,
- capture quality suggestion.

Python geometry:
- distance,
- height estimation,
- clearance,
- risk status,
- quarterly prediction.

AI tidak boleh menggantikan Python geometry.

## Target Objects

- pohon_sono
- konduktor
- struktur_penyangga

Objek lain seperti orang, mobil, ruangan, keyboard, dompet, meja, dan laptop boleh diabaikan.

## UI Rule

Capture page harus bersih:
- camera preview,
- instruction,
- shutter,
- retry,
- processing.

Tidak boleh ada:
- YOLO-FIRST,
- AI realtime switch,
- lens selector custom,
- debug chips,
- MODEL_STATUS_UNKNOWN,
- realtime bounding overlay.

Developer page boleh menampilkan debug.
