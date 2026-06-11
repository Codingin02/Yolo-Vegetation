# SYSTEM C FINAL — Legal License and Download Policy

## Prinsip

Gambar internet hanya boleh dipakai jika sumber, author, license, dan attribution jelas. Gambar dari Google Images langsung tidak boleh dipakai karena Google Images hanya mesin pencari, bukan sumber lisensi.

## Kategori license

Aman untuk dataset riset jika attribution dicatat:

```text
CC0
Public Domain
CC BY
CC BY-SA
```

Restricted/reference-only:

```text
CC BY-NC
CC BY-NC-SA
research-only unclear
educational-only
```

Tolak:

```text
all rights reserved
license missing
unknown copyright
no author
no source URL
watermark commercial
```

## Download rules

Downloader harus:

```text
- memakai User-Agent jelas
- rate limit per source
- retry terbatas
- exponential backoff untuk HTTP 429
- timeout per request
- checksum SHA256
- simpan manifest walau download gagal
- tidak menulis langsung ke data/raw
- tidak menulis langsung ke runs/weights/models
```

## Path download awal

```text
D:\Users\All Users\Downloads\ULP_Project_PlanC_Dataset_Downloads
```

Subfolder:

```text
pohon_sono_positive_reference
pohon_non_sono_negative_reference
conductor_structure_reference
non_target_negative_reference
restricted_reference_only
rejected_license_unclear
```

## Path dataset final

```text
E:\Projects\ULP_Project\data\dataset_yolo\plan_c_final_v1
```

Hanya gambar yang lolos policy dan manifest yang boleh masuk.

## Manifest source

`source_manifest.csv` wajib memuat source_site, page_url, direct_image_url, author, license, target_class, dan sha256.

## Manifest license

`license_manifest.csv` wajib memuat license, license_url, attribution, accepted/restricted/rejected status.

## Manifest review

`review_manifest.csv` wajib memuat review_status:

```text
needs_manual_check
accepted_pseudo_label
rejected_pseudo_label
accepted_manual_label
```

## Output status

Jika sumber gagal:

```text
SOURCE_UNAVAILABLE_OR_RATE_LIMITED
```

Jika license tidak jelas:

```text
REJECT_LICENSE_UNCLEAR
```

Jika spesies tidak spesifik:

```text
REJECT_NOT_SPECIES_SPECIFIC
```

Jika cukup untuk review tetapi belum final:

```text
REVIEW_PACKAGE_READY_NOT_FINAL_TRAINING
```
