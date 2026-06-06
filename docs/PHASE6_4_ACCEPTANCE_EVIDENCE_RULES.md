# Phase 6.4 Acceptance Evidence Rules

Acceptance PASS hanya boleh jika evidence minimal lengkap:

- acceptance sudah disubmit dari HP.
- halaman dibuka melalui public HTTPS.
- secure context OK.
- kamera siap atau aktif.
- GPS siap atau aktif, termasuk GPS_ACCURACY_LOW dengan catatan limitasi.
- nilai GPS accuracy tercatat.
- start session PASS.
- stop record PASS.
- shutter PASS.
- report page PASS.
- result page PASS.
- map status jelas: MAP_HTML_READY, MAP_BASIC_FALLBACK, FOLIUM_READY, atau NO_GPS_NO_MARKER.
- model status jujur: MODEL_NOT_READY atau REAL_MODEL.
- no fake detection PASS.
- operator_name atau device_name diisi.

Status gagal utama:

- PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST: belum ada submit evidence HP.
- PHYSICAL_HP_ACCEPTANCE_FAIL_NO_PUBLIC_HTTPS: bukan public HTTPS atau secure context belum OK.
- PHYSICAL_HP_ACCEPTANCE_FAIL_CAMERA_NOT_READY: kamera belum siap.
- PHYSICAL_HP_ACCEPTANCE_FAIL_GPS_NOT_READY: GPS atau accuracy belum tercatat.
- PHYSICAL_HP_ACCEPTANCE_FAIL_SHUTTER_NOT_RECORDED: shutter belum ada.
- PHYSICAL_HP_ACCEPTANCE_FAIL_REPORT_RESULT_NOT_OPENED: report/result belum dibuka.

GPS_ACCURACY_LOW tidak menggagalkan acceptance workflow, tetapi status harus menjadi PASS_WITH_GPS_LIMITATION bila bukti lain lengkap. Ini bukan bukti jarak presisi.
