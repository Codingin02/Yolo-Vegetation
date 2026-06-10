# 02 — Plan C Route Contract

## Page Routes

GET /plan-c  
Home Plan C.

GET /plan-c/capture/<session_id>  
Halaman kamera bersih.

GET /plan-c/processing/<session_id>  
Halaman tunggu processing.

GET /plan-c/result/<session_id>  
Halaman hasil.

GET /plan-c/map  
Peta marker hasil inspeksi.

GET /plan-c/developer/<session_id>  
Halaman debug developer.

## API Routes

POST /api/plan-c/session/start  
Membuat session baru.

POST /api/plan-c/session/tree-anchor  
Menyimpan GPS tree anchor. GPS tidak boleh memblokir kamera.

POST /api/plan-c/session/snapshot  
Upload foto snapshot dan metadata.

GET /api/plan-c/session/<session_id>/status  
Mengecek status processing.

GET /api/plan-c/session/<session_id>/result  
Mengambil result JSON.

## Status Wajib

PLAN_C_SESSION_STARTED  
TREE_ANCHOR_SAVED  
TREE_ANCHOR_PENDING  
PLAN_C_SNAPSHOT_ACCEPTED  
PLAN_C_PROCESSING  
PLAN_C_RESULT_READY  
YOLO_MODEL_NOT_READY  
AI_VALIDATOR_DISABLED  
DATA_TIDAK_CUKUP
