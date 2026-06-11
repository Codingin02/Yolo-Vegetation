# SYSTEM C FINAL — Wording Laporan Akhir dan Batas Klaim

## Judul aman

```text
Pengembangan Sistem Monitoring Pohon Sono pada Jaringan Distribusi 20 kV Berbasis YOLOv8, Monocular Scaling, dan Regresi Linear untuk Prediksi Waktu Pemangkasan
```

## Narasi sistem

Sistem yang dikembangkan merupakan prototipe monitoring vegetasi berbasis snapshot capture dari perangkat HP, pemrosesan backend pada laptop, deteksi objek menggunakan YOLOv8, estimasi geometri menggunakan Python geometry, serta prediksi risiko pertumbuhan menggunakan data pertumbuhan pohon sono/angsana berbasis proxy dan/atau data lapangan yang tersedia.

## Klaim yang boleh

```text
- Sistem prototipe field trial.
- YOLOv8 digunakan untuk deteksi objek setelah snapshot.
- Output YOLO berupa bounding box, class, dan confidence.
- Python geometry digunakan untuk estimasi clearance dan zona.
- Growth model digunakan untuk prediction window.
- AI vision, jika ada, hanya validator tambahan.
- Data growth proxy belum menggantikan observasi lokal.
```

## Klaim yang tidak boleh

```text
- Sistem produksi PLN.
- Akurasi final PLN.
- Clearance final untuk semua kondisi.
- Model biologis final pertumbuhan pohon.
- Dataset sudah lengkap jika belum gate.
- AI menggantikan YOLO.
- AI menghitung clearance final.
```

## Penyesuaian dari proposal

Proposal awal mengarah ke YOLOv8 single-class untuk pohon sono, monocular scaling, dan regresi linear. Dalam implementasi Plan C, sistem tetap memakai YOLOv8 sebagai pendeteksi utama setelah snapshot. Pengembangan menambahkan class pendukung konduktor dan struktur penyangga untuk kebutuhan geometri, tetapi laporan harus menjelaskan bahwa fokus utama riset tetap pohon sono pada jaringan distribusi 20 kV.

## Dataset growth

Data growth pohon sono/angsana harus ditulis sebagai proxy jika belum ada observasi lapangan ULP Perak. Pakai istilah:

```text
proxy reference
field-trial prior
perlu validasi lapangan
bukan observasi biologis final
```

## Zona risiko

Tulis zona sebagai:

```text
ZONA_TEBANG: area 0–3 meter di bawah konduktor.
ZONA_PANTAU: area 3–6 meter di bawah konduktor.
ZONA_AMAN: area di bawah batas pantau hingga ground reference.
```

Jangan tulis zona aman sebagai bagian bawah foto secara visual. Zona aman harus berbasis ground reference.

## Kesimpulan aman

Kesimpulan akhir harus jujur:

```text
Sistem berhasil membangun alur monitoring berbasis snapshot dan pipeline deteksi-prediksi, tetapi akurasi model dan estimasi clearance tetap perlu diperkuat melalui penambahan dataset lapangan, validasi bounding box, dan uji lapangan berulang.
```
