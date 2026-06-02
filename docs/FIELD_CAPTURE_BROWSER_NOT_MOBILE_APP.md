# Field Capture Browser, Not Mobile App

Tidak ada APK, tidak ada Flutter, tidak ada React Native, dan tidak ada monitoring app HP.

HP hanya:

- membuka `/field-capture`,
- mengirim foto/frame,
- mengirim GPS browser,
- mengirim metadata inspeksi,
- menerima hasil ringkas.

Laptop:

- menjalankan Flask,
- memproses image nanti dengan YOLO/OpenCV,
- menghitung tinggi, clearance, ETA,
- menulis spreadsheet,
- membuat peta risiko.

Route `/mobile` hanya alias kompatibilitas ke `/field-capture`.
