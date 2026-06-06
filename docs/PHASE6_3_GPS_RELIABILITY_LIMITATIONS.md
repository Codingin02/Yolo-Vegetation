# Phase 6.3 GPS Reliability Limitations

Browser GPS memakai Native Geolocation API:

- `navigator.geolocation.getCurrentPosition()`
- `navigator.geolocation.watchPosition()`
- `enableHighAccuracy: true`

Batas yang wajib dipahami:

- Browser tidak memberi akses langsung ke jumlah satelit.
- Browser GPS bukan RTK/survey-grade.
- Browser hanya meminta high accuracy; OS/browser menentukan sumber lokasi.
- Web recording tidak dijamin berjalan penuh saat tab hidden, layar mati, atau browser diminimize.
- GPS adalah evidence lokasi, spatial grouping, dan estimasi jarak mundur operator.
- GPS bukan pengganti kalibrasi kamera dan tidak memperbaiki pixel-to-meter geometry.

Policy akurasi:

- `GPS_ACCURACY_GOOD`: accuracy <= 5 m.
- `GPS_ACCURACY_MEDIUM`: 5 m < accuracy <= 10 m.
- `GPS_ACCURACY_LOW`: accuracy > 10 m.
- `GPS_ACCURACY_UNKNOWN`: browser belum memberi nilai accuracy.

Distance reliability:

- Jika accuracy lebih besar dari jarak mundur, status:
  `GPS_ACCURACY_GREATER_THAN_DISTANCE`
- Jika jarak < 1 m:
  `DISTANCE_TOO_SMALL_FOR_GPS_RELIABILITY`
- Jika jarak >= 2x max accuracy:
  `DISTANCE_REASONABLY_RELIABLE_FOR_FIELD_EVIDENCE`

Jika GPS low, report tetap boleh disimpan sebagai evidence lokasi, tetapi tidak boleh dipakai untuk klaim jarak presisi.
