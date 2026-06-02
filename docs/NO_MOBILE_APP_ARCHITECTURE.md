# No Mobile App Architecture

Project ini tidak membuat APK, Flutter, React Native, Android app, iOS app, dashboard mobile app, atau monitoring app.

## Peran HP

HP hanya field input browser, bukan aplikasi monitoring utama.

- Membuka halaman web ringan dari server Flask laptop.
- Mengirim foto atau frame.
- Mengirim GPS browser.
- Mengirim metadata inspeksi.
- Menerima hasil ringkas real-time.

## Peran Laptop

- Menjalankan Flask.
- Menjalankan YOLO/OpenCV nanti setelah model tersedia.
- Menghitung jarak pohon ke kabel, span, trafo, atau tiang.
- Menghitung ETA risiko.
- Menulis CSV/Google Sheets.
- Membuat peta risiko.

## Route Utama

- `/field-capture`
- `/api/field-capture/upload`
- `/api/field-capture/job/<job_id>`
- `/api/field-capture/result/<job_id>`
- `/api/field-capture/ping`

`/mobile` hanya alias kompatibilitas ke `/field-capture`.
