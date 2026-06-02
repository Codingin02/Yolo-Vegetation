# Codex Next Prompt After makesense Done

Gunakan prompt ini setelah export YOLO makesense.ai selesai.

```text
Anda bekerja di E:\Projects\ULP_Project pada branch system-finalization-no-label-touch.

Mulai dengan audit:
git branch --show-current
git rev-parse --short HEAD
git status --short --untracked-files=all

Labeling V001_pohon_sono sudah selesai dan export YOLO makesense.ai sudah diletakkan di:
data\exports\make_sense\V001_pohon_sono

Kerjakan aman:
1. Jalankan phase3_readiness_gate dan phase4_integration_gate.
2. Jalankan import makesense dry-run.
3. Jika jumlah label export cocok jumlah gambar dan tidak ada orphan/invalid, jalankan import mode copy.
4. Jalankan validate_yolo_labels.
5. Jika validator VALID, jalankan build dataset dry-run.
6. Jika dry-run aman, jalankan build dataset mode build.
7. Generate data.yaml.
8. Jalankan train launcher dry-run.
9. Jangan training actual sebelum user memberi izin eksplisit.
10. Laporkan semua status tanpa klaim akurasi, mAP, precision, recall, atau performa model.

Jangan menggunakan dataset_botol sebagai dataset utama.
Jangan membuat label palsu, model palsu, atau akurasi palsu.
```
