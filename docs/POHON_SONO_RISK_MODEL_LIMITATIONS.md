# Pohon Sono Risk Model Limitations

Risk model Phase 6 bersifat rule-based dan data-driven skeleton. Model ini dibuat untuk membantu prioritas operator, bukan klaim ilmiah final.

## Faktor yang Dipakai

- Jarak vegetasi ke konduktor jika tersedia dari vision/calibration.
- Curah hujan 7 hari dan 30 hari.
- Kelembapan dan suhu.
- Hari kering beruntun.
- Angin dan gust.
- pH serta tekstur tanah jika tersedia.
- Ketidakpastian lokasi urban padat/perkerasan bila data langsung belum ada.

## Output

- `growth_pressure_score`
- `trimming_urgency_score`
- `electrical_clearance_risk`
- `environmental_growth_index`
- `confidence_level`
- `missing_sources`
- `top_factors`
- `not_accuracy_claim: true`

## Batasan

- Tidak memprediksi akurasi final.
- Tidak mengganti inspeksi manusia.
- Tidak memakai angka pH/curah hujan Surabaya tanpa sumber data nyata.
- Tidak boleh dipakai sebagai dasar klaim performa sebelum validasi ground truth.
