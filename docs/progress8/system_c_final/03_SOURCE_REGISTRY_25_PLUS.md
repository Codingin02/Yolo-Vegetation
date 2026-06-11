# SYSTEM C FINAL — Source Registry 25+ untuk Scraping Legal

Codex wajib mencari dari banyak sumber. Jangan hanya Wikimedia. Setiap sumber harus dicatat legalitas dan attribution-nya.

## Query utama pohon_sono

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

## Source registry

| priority | source_name | target | status policy |
|---:|---|---|---|
| 1 | Wikimedia Commons | pohon_sono | download jika license jelas |
| 2 | GBIF occurrence media | pohon_sono | download jika media license jelas |
| 3 | iNaturalist observations | pohon_sono | CC jelas boleh; CC-BY-NC restricted |
| 4 | Flickr Creative Commons | pohon_sono | download jika license masih aktif |
| 5 | Openverse | pohon_sono | pakai original source URL dan license |
| 6 | Encyclopedia of Life media | pohon_sono | download jika license jelas |
| 7 | PlantNet / Pl@ntNet | pohon_sono | reference-only jika terms tidak jelas |
| 8 | India Biodiversity Portal | pohon_sono | download jika license/author jelas |
| 9 | Atlas of Living Australia | pohon_sono | download jika media license jelas |
| 10 | Kew / Plants of the World Online | pohon_sono | taxonomy/reference-only |
| 11 | NParks Flora Fauna Web | pohon_sono | morphology/reference-only |
| 12 | Useful Tropical Plants | pohon_sono | reference-only kecuali license jelas |
| 13 | Tropical Plants Database | pohon_sono | reference-only jika copyright unclear |
| 14 | Forestry/agroforestry species PDFs | growth/reference | citation only, not dataset image |
| 15 | Roboflow Universe | conductor/structure/vegetation | pakai hanya dataset dengan license jelas |
| 16 | Open Images | negative/conductor-like/object | object detection source |
| 17 | MS COCO | negative sample | person/vehicle/indoor object |
| 18 | LVIS | negative/object variety | object variety |
| 19 | Mapillary / Mapillary Vistas | conductor/structure context | street-level scene, check terms |
| 20 | ADE20K | negative indoor/wall/building | negative scene |
| 21 | LabelMe | negative object/scene | annotation reference |
| 22 | Kaggle dataset search | conductor/tree/pole | only if license clear |
| 23 | Zenodo datasets | power line/vegetation | use DOI/license if clear |
| 24 | IEEE DataPort metadata | reference only unless accessible/legal |
| 25 | Mendeley Data | vegetation/powerline | use if license clear |
| 26 | Figshare | vegetation/powerline | use if license clear |
| 27 | Government/open utility image portals | utility pole | use if license clear |
| 28 | Own field photos | all classes | highest priority if available |
| 29 | Existing local accepted feedback | all classes | use only if operator accepted |
| 30 | Manual photo package from HP | all classes | use after source marked own-field |

## Accept rules

Pohon sono diterima jika metadata menyebut:

```text
Pterocarpus indicus
angsana
sonokembang
narra
Burmese rosewood
Malay padauk
```

Reject jika hanya:

```text
tree
plant
wood
timber
furniture
generic vegetation
```

Konduktor diterima jika visual dan metadata jelas menunjukkan overhead power line / distribution conductor / electric line.

Struktur penyangga diterima jika visual dan metadata jelas menunjukkan utility pole / power pole / distribution pole / crossarm.

Negative sample diterima jika memang bukan target, seperti manusia, kendaraan, tembok, indoor object, atap, lampu, dan pohon non-sono.

## HTTP 429 policy

Jika Wikimedia atau sumber lain mengembalikan HTTP 429:

1. catat `SOURCE_RATE_LIMITED`,
2. tidur sesuai backoff,
3. jangan retry tanpa batas,
4. pindah ke sumber lain,
5. lanjutkan manifest,
6. jangan membuat kandidat palsu.
