# Progress 6.4 Live HP Acceptance Execution

Progress 6.4 adalah tahap eksekusi live dan bugfix-only untuk membuktikan workflow HP fisik. Tahap ini tidak mengulang Progress 5.4, 6.1, 6.2, atau 6.3.

Arsitektur tetap:

HP browser field client -> public HTTPS tunnel Ngrok/Cloudflare -> Flask backend di laptop -> runtime/report/map.

Target sebelum HP submit:

`PROGRESS_6_4_LIVE_HP_ACCEPTANCE_READY_WAITING_FOR_USER_TEST`

Target setelah evidence lengkap dari HP:

`PROGRESS_6_4_LIVE_HP_ACCEPTANCE_PASS`

Jika GPS aktif tetapi akurasi rendah, status yang benar:

`PROGRESS_6_4_LIVE_HP_ACCEPTANCE_PASS_WITH_GPS_LIMITATION`

Acceptance bukan klaim akurasi model. Acceptance hanya membuktikan public HTTPS, kamera, GPS browser, shutter, report/result, map status, dan no fake detection hidup dari HP fisik.

`MODEL_NOT_READY` bukan blocker acceptance. `REAL_MODEL` hanya boleh muncul jika `best.pt` valid dan class order sudah sesuai.
