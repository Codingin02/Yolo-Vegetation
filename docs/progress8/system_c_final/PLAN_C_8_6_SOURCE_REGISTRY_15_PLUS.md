# PLAN C 8.6 — Source Registry 15+ untuk Dataset Pohon Sono dan Pendukung

## Prinsip sumber

Codex harus memakai banyak sumber. Jangan hanya Wikimedia. Prioritasnya adalah legalitas, metadata, dan relevansi visual. Jika sumber tidak menyediakan license atau attribution yang jelas, jangan masukkan ke folder dataset aktif.

## Query pohon_sono

```text
Pterocarpus indicus
angsana
pohon angsana
sonokembang
sono kembang
narra tree
Burmese rosewood
Malay padauk
Andaman redwood
Pterocarpus indicus leaves
Pterocarpus indicus bark
Pterocarpus indicus flowers
Pterocarpus indicus crown
```

## Source registry utama

| priority | source_name | target | use | accept policy |
|---:|---|---|---|---|
| 1 | Wikimedia Commons | pohon_sono | positive species reference | ACCEPT jika category/file metadata menyebut Pterocarpus indicus dan license CC/PD jelas |
| 2 | GBIF occurrence media | pohon_sono | positive occurrence reference | ACCEPT hanya jika media license jelas dan scientificName/taxonKey cocok |
| 3 | iNaturalist observations | pohon_sono | positive field variation | ACCEPT jika taxon Pterocarpus indicus dan photo license jelas; CC-BY-NC masuk restricted review |
| 4 | Flickr Creative Commons search | pohon_sono | positive additional variation | ACCEPT jika license CC jelas dan tags/title/description kuat |
| 5 | Openverse | pohon_sono | meta-search CC sources | ACCEPT jika original source dan license jelas |
| 6 | Encyclopedia of Life media | pohon_sono | reference candidate | ACCEPT jika license dan source_url tersedia |
| 7 | PlantNet / Pl@ntNet | pohon_sono | reference candidate | ACCEPT hanya jika license/API terms jelas; jika tidak, manifest-only |
| 8 | India Biodiversity Portal | pohon_sono | South/Southeast Asia visual reference | ACCEPT hanya jika license/author jelas |
| 9 | Atlas of Living Australia | pohon_sono | occurrence/media mirror | ACCEPT hanya jika media license jelas |
| 10 | Wikimedia linked media via multilingual pages | pohon_sono | additional Commons-linked files | ACCEPT hanya jika imageinfo license jelas |
| 11 | Kew / Plants of the World Online | pohon_sono | taxonomy/reference only | biasanya REFERENCE_ONLY, bukan download dataset, kecuali license image jelas |
| 12 | NParks Flora Fauna Web | pohon_sono | species morphology reference | biasanya REFERENCE_ONLY, bukan download dataset, kecuali license image jelas |
| 13 | Useful Tropical Plants / Agroforestry pages | pohon_sono | morphology/reference only | REFERENCE_ONLY jika copyright tidak mengizinkan dataset |
| 14 | Roboflow Universe | konduktor/struktur/vegetasi | dataset candidate | ACCEPT hanya per-project license jelas dan class cocok |
| 15 | Open Images | negative + conductor-like + utility scenes | bounding-box source | ACCEPT untuk negative sample dan objek umum dengan license/attribution jelas |
| 16 | MS COCO | negative sample | person, car, truck, motorcycle, indoor object | ACCEPT jika license/terms image dapat dicatat; jangan untuk pohon_sono |
| 17 | LVIS | negative/object segmentation | person/vehicle/object/plant broad classes | ACCEPT hanya sesuai license dataset |
| 18 | Mapillary / Mapillary Vistas | conductor/utility/street pole context | street-level utility context | ACCEPT hanya sesuai license/terms; cocok untuk pole/roadside negative |
| 19 | ADE20K | indoor/wall/building negative | indoor object, wall, building | ACCEPT hanya sesuai dataset license |
| 20 | LabelMe | negative object/scene | indoor/outdoor object scenes | ACCEPT hanya jika license valid dan source term jelas |
| 21 | Flickr/YFCC100M metadata | broad positive/negative search | CC photo discovery | ACCEPT jika original Flickr license masih tercatat dan attribution tersimpan |
| 22 | Foto lapangan sendiri | semua target | highest-value dataset | ACCEPT jika kualitas cukup dan label manual/pseudo-label direview |

## Query per class

### pohon_sono

```text
"Pterocarpus indicus" OR "angsana" OR "sonokembang" OR "narra tree" OR "Burmese rosewood" OR "Malay padauk"
```

Reject otomatis:

```text
generic tree
plant only
wood product
furniture
timber plank
bonsai unclear
low resolution
watermark heavy
license missing
```

### konduktor

```text
overhead power line
distribution conductor
medium voltage conductor
20 kV overhead line
utility power line
electric cable overhead
power cable above tree
```

### struktur_penyangga

```text
utility pole
electric pole
power pole
distribution pole
concrete electricity pole
crossarm power line
medium voltage pole
```

### negative non-target

```text
person
face
head
chin
mouth
eye
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
```

## Output manifest wajib

```text
data/dataset_yolo/plan_c_final_v1/source_manifest.csv
data/dataset_yolo/plan_c_final_v1/license_manifest.csv
data/dataset_yolo/plan_c_final_v1/review_manifest.csv
```

Kolom minimal:

```text
local_path,label_path,source_site,source_url,direct_image_url,scientific_name,common_name,target_class,license,license_url,author,attribution,country,width,height,sha256,downloaded_at,accept_status,review_status,risk_note
```

## Accept status

```text
ACCEPT_POSITIVE_REFERENCE
ACCEPT_NEGATIVE_REFERENCE
ACCEPT_CONDUCTOR_REFERENCE
ACCEPT_STRUCTURE_REFERENCE
RESTRICTED_REFERENCE_ONLY
REJECT_LICENSE_UNCLEAR
REJECT_NOT_SPECIES_SPECIFIC
REJECT_LOW_QUALITY
REJECT_NOT_TARGET_OBJECT
REJECT_DUPLICATE
```
