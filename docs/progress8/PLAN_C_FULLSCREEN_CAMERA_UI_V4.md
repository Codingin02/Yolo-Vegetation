# Plan C Fullscreen Camera UI V4

Patch V4 membersihkan capture page agar kamera menjadi full satu halaman dan tidak lagi bercampur dengan script/operator UI lama.

## Perubahan utama

1. `plan_c_capture.html` dioverwrite menjadi template bersih.
2. Tidak memuat:
   - `plan_c_capture.js`
   - `plan_c_operator_final.js`
   - `plan_c_operator_ui_accuracy_final.js`
   - CSS lama yang menyebabkan kamera mengecil.
3. Kamera memakai viewport penuh.
4. Tombol visible hanya:
   - Shutter merah di dalam kamera.
   - Bottom nav satu deret: Home, Kamera, Map, Result.
5. Tidak ada status chip Camera/GPS/Server pada operator page.
6. Tidak ada manual input pada operator page.
7. GPS tetap dicoba otomatis dengan:
   - `enableHighAccuracy: true`
   - `maximumAge: 0`
   - `timeout: 20000`
8. Result page diberi bottom nav yang sama.
9. File backend, dataset, model, label, dan runtime lama tidak disentuh.

## Catatan GPS

Laptop dapat tetap gagal memberi koordinat jika device/browser/Windows tidak menyediakan lokasi presisi. Test final GPS paling tepat dilakukan dari HP melalui URL HTTPS ngrok.
