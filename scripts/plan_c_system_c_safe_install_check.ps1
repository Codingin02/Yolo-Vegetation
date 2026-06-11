Set-StrictMode -Off
$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\Projects\ULP_Project"
$DocsTarget = Join-Path $ProjectRoot "docs\progress8\system_c_final"
$SharedDownloads = "D:\Users\All Users\Downloads"
$UserDownloads = Join-Path $env:USERPROFILE "Downloads"
$DatasetDownloadRoot = Join-Path $SharedDownloads "ULP_Project_PlanC_Dataset_Downloads"
$DatasetFinalRoot = Join-Path $ProjectRoot "data\dataset_yolo\plan_c_final_v1"

Write-Host "=== PLAN C SYSTEM C SAFE INSTALL CHECK ===" -ForegroundColor Cyan
Write-Host "ProjectRoot         : $ProjectRoot"
Write-Host "DocsTarget          : $DocsTarget"
Write-Host "SharedDownloads     : $SharedDownloads"
Write-Host "UserDownloads       : $UserDownloads (optional)"
Write-Host "DatasetDownloadRoot : $DatasetDownloadRoot"
Write-Host "DatasetFinalRoot    : $DatasetFinalRoot"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "PROJECT_ROOT_NOT_FOUND: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $SharedDownloads)) {
    New-Item -ItemType Directory -Force -Path $SharedDownloads | Out-Null
}
if (-not (Test-Path -LiteralPath $UserDownloads)) {
    Write-Host "USER_DOWNLOADS_OPTIONAL_MISSING" -ForegroundColor Yellow
}

New-Item -ItemType Directory -Force -Path $DocsTarget | Out-Null
New-Item -ItemType Directory -Force -Path $DatasetDownloadRoot | Out-Null
New-Item -ItemType Directory -Force -Path $DatasetFinalRoot | Out-Null

$required = @(
    "00_README_SYSTEM_C_FINAL.md",
    "01_SYSTEM_C_ARCHITECTURE_FINAL.md",
    "02_DATASET_FINAL_TARGET_AND_FOLDER_POLICY.md",
    "03_SOURCE_REGISTRY_25_PLUS.md",
    "04_LEGAL_LICENSE_AND_DOWNLOAD_POLICY.md",
    "05_AUTOLABEL_AND_BOUNDING_POLICY.md",
    "06_ROBOFLOW_REVIEW_PACKAGE_WORKFLOW.md",
    "07_YOLOV8_TRAINING_GATE_AND_TRAINING_PLAN.md",
    "08_MODEL_REGISTRY_AND_RUNTIME_INTEGRATION.md",
    "09_RUNTIME_PLAN_C_FINAL_ACCEPTANCE.md",
    "10_FIELD_TEST_HP_NGROK_FINAL_RUNBOOK.md",
    "11_FINAL_REPORT_WORDING_AND_CLAIM_POLICY.md",
    "12_CODEX_MASTER_PROMPT_SYSTEM_C_FINAL.md",
    "13_POWERSHELL_INSTALL_AND_RUNBOOK.md",
    "14_FAILURE_RECOVERY_AND_ANTI_REPEAT.md",
    "LOCAL_PATHS_SYSTEM_C_FINAL.md",
    "MANIFEST_SYSTEM_C_FINAL.json"
)

$missing = @()
foreach ($name in $required) {
    $path = Join-Path $DocsTarget $name
    if (-not (Test-Path -LiteralPath $path)) {
        $missing += $name
    }
}

Write-Host "MISSING_EXPECTED_COUNT = $($missing.Count)" -ForegroundColor Cyan
foreach ($name in $missing) {
    Write-Host "MISSING: $name" -ForegroundColor Yellow
}

Write-Host "INSTALL_SYSTEM_C_FINAL_DOCS_COMPLETE" -ForegroundColor Green
