# SYSTEM C FINAL — Auto-label dan Bounding Policy

## Tujuan

Auto-label dibuat untuk mempercepat review dataset, bukan untuk menggantikan label manual sepenuhnya. Semua hasil auto-label harus diberi status `needs_manual_check`.

## Format YOLO

Setiap file label `.txt` memakai format:

```text
class_id x_center y_center width height
```

Koordinat harus normalized 0–1.

Class ID:

```text
0 struktur_penyangga
1 konduktor
2 pohon_sono
3 pohon_non_sono
```

## Bounding pohon_sono

Label `pohon_sono` dipakai hanya jika objek adalah Pterocarpus indicus/angsana/sonokembang/narra yang metadata atau review visualnya kuat.

Bbox harus melingkupi bagian pohon yang terlihat. Jangan memasukkan langit, gedung, kendaraan, orang, atau background luas.

## Bounding konduktor

Konduktor adalah kabel listrik udara. Jika ada 3 kabel yang terpisah, buat 3 bbox. Jika ada lebih dari 3 kabel, bbox semua kabel yang terlihat. Jangan membuat satu bbox besar yang menutupi seluruh area kosong jika kabel terpisah jelas.

## Bounding struktur_penyangga

Struktur penyangga mencakup tiang listrik, crossarm, lengan penyangga, insulator support, atau komponen struktur yang mendukung konduktor.

Jangan label lampu jalan biasa, tiang reklame, dinding, lemari, atau objek vertikal non-listrik sebagai struktur_penyangga.

## Negative sample

Objek berikut tidak boleh diberi bbox target:

```text
person
face
head
chin
mouth
eye
body
car
motorcycle
truck
wall
indoor room
cabinet
lamp
roof
ceiling
floor
chair
table
phone
keyboard
monitor
```

Gambar negative boleh tidak memiliki label `.txt`. Dalam YOLO, gambar tanpa objek target boleh tanpa file label atau label kosong sesuai pipeline.

## Confidence pseudo-label

Auto-label harus punya confidence metadata. Threshold awal:

```text
pohon_sono confidence >= 0.45 untuk needs_manual_check
konduktor confidence >= 0.35 untuk needs_manual_check
struktur_penyangga confidence >= 0.35 untuk needs_manual_check
```

Jika confidence rendah, masukkan ke review folder, bukan train aktif.

## Review rule

File auto-label tidak boleh naik ke `accepted_manual_label` tanpa review manusia.

Status awal auto-label:

```text
needs_manual_check
```

Setelah review:

```text
accepted_pseudo_label
rejected_pseudo_label
accepted_manual_label
```

## Kesalahan yang harus dicegah

1. Tree umum menjadi pohon_sono.
2. Dagu/wajah/manusia menjadi pohon.
3. Kabel USB atau tali menjadi konduktor.
4. Lemari/dinding menjadi struktur penyangga.
5. Bbox terlalu besar.
6. Bbox keluar gambar.
7. Label class salah urutan.
8. File label kosong tetapi dianggap label target.
