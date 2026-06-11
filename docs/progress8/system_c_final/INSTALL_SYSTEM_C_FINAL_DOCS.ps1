Set-StrictMode -Off
$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\Projects\ULP_Project"
$SharedDownloads = "D:\Users\All Users\Downloads"
$UserDownloads = Join-Path $env:USERPROFILE "Downloads"
$ZipName = "plan_c_system_c_final_docs.zip"
$ZipPath = Join-Path $SharedDownloads $ZipName
$DocsTarget = Join-Path $ProjectRoot "docs\progress8\system_c_final"
$DatasetDownloadRoot = Join-Path $SharedDownloads "ULP_Project_PlanC_Dataset_Downloads"
$DatasetFinalRoot = Join-Path $ProjectRoot "data\dataset_yolo\plan_c_final_v1"

Write-Host ""
Write-Host "=== SYSTEM C FINAL DOCS INSTALLER ===" -ForegroundColor Cyan
Write-Host "ProjectRoot         : $ProjectRoot"
Write-Host "SharedDownloads     : $SharedDownloads"
Write-Host "UserDownloads       : $UserDownloads (optional)"
Write-Host "ZipPath             : $ZipPath"
Write-Host "DocsTarget          : $DocsTarget"
Write-Host "DatasetDownloadRoot : $DatasetDownloadRoot"
Write-Host "DatasetFinalRoot    : $DatasetFinalRoot"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "PROJECT_ROOT_NOT_FOUND: $ProjectRoot"
}

New-Item -ItemType Directory -Force -Path $SharedDownloads | Out-Null
New-Item -ItemType Directory -Force -Path $DocsTarget | Out-Null
New-Item -ItemType Directory -Force -Path $DatasetDownloadRoot | Out-Null
New-Item -ItemType Directory -Force -Path $DatasetFinalRoot | Out-Null

$zipCandidates = @()
$zipCandidates += $ZipPath
$zipCandidates += Join-Path (Get-Location) $ZipName
if (Test-Path -LiteralPath $UserDownloads) {
    $zipCandidates += Join-Path $UserDownloads $ZipName
} else {
    Write-Host "USER_DOWNLOADS_OPTIONAL_MISSING: $UserDownloads" -ForegroundColor Yellow
}

$FoundZip = $null
foreach ($candidate in $zipCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $FoundZip = $candidate
        break
    }
}

if ($FoundZip) {
    if ($FoundZip -ne $ZipPath) {
        Copy-Item -LiteralPath $FoundZip -Destination $ZipPath -Force
        Write-Host "ZIP_COPIED_TO_SHARED_DOWNLOADS: $ZipPath" -ForegroundColor Yellow
    }

    $TempExtract = Join-Path $env:TEMP ("plan_c_system_c_final_docs_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
    New-Item -ItemType Directory -Force -Path $TempExtract | Out-Null
    Write-Host "EXTRACT_ZIP: $ZipPath" -ForegroundColor Cyan
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $TempExtract -Force

    $MdFiles = Get-ChildItem -LiteralPath $TempExtract -Recurse -File -Filter "*.md"
    foreach ($file in $MdFiles) {
        Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $DocsTarget $file.Name) -Force
        Write-Host ("COPIED_DOC: " + $file.Name) -ForegroundColor Green
    }
} else {
    Write-Host "ZIP_NOT_FOUND_OPTIONAL_SKIP_DOC_COPY: $ZipName" -ForegroundColor Yellow
    Write-Host "Existing docs will be verified in place." -ForegroundColor Yellow
}

$folders = @(
    "$DatasetDownloadRoot\pohon_sono_positive_reference",
    "$DatasetDownloadRoot\pohon_non_sono_negative_reference",
    "$DatasetDownloadRoot\conductor_structure_reference",
    "$DatasetDownloadRoot\non_target_negative_reference",
    "$DatasetDownloadRoot\restricted_reference_only",
    "$DatasetDownloadRoot\rejected_license_unclear",
    "$DatasetFinalRoot\images\train",
    "$DatasetFinalRoot\images\val",
    "$DatasetFinalRoot\images\test",
    "$DatasetFinalRoot\labels\train",
    "$DatasetFinalRoot\labels\val",
    "$DatasetFinalRoot\labels\test",
    "$DatasetFinalRoot\rejected\license_unclear",
    "$DatasetFinalRoot\rejected\low_quality",
    "$DatasetFinalRoot\rejected\not_species_specific",
    "$DatasetFinalRoot\rejected\non_target",
    "$DatasetFinalRoot\review\needs_manual_check",
    "$DatasetFinalRoot\review\accepted_pseudo_label",
    "$DatasetFinalRoot\review\rejected_pseudo_label",
    "$DatasetFinalRoot\review\accepted_manual_label",
    "$DatasetFinalRoot\roboflow_package"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}

$ClassesPath = Join-Path $DatasetFinalRoot "classes.txt"
if (-not (Test-Path -LiteralPath $ClassesPath)) {
@"
struktur_penyangga
konduktor
pohon_sono
pohon_non_sono
"@ | Set-Content -Path $ClassesPath -Encoding UTF8
}

$YamlPath = Join-Path $DatasetFinalRoot "data.yaml"
if (-not (Test-Path -LiteralPath $YamlPath)) {
@"
path: E:/Projects/ULP_Project/data/dataset_yolo/plan_c_final_v1
train: images/train
val: images/val
test: images/test

names:
  0: struktur_penyangga
  1: konduktor
  2: pohon_sono
  3: pohon_non_sono
"@ | Set-Content -Path $YamlPath -Encoding UTF8
}

$PathPolicy = Join-Path $DocsTarget "LOCAL_PATHS_SYSTEM_C_FINAL.md"
@"
# LOCAL PATHS - SYSTEM C FINAL

Project root:
$ProjectRoot

Docs target:
$DocsTarget

Shared downloads:
$SharedDownloads

User downloads optional:
$UserDownloads

Dataset download staging:
$DatasetDownloadRoot

Dataset final:
$DatasetFinalRoot

Catatan:
UserDownloads bersifat optional. Script ini tidak git add, tidak commit, tidak reset, tidak download internet, dan tidak menghapus file.
"@ | Set-Content -Path $PathPolicy -Encoding UTF8

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

Write-Host ""
Write-Host "MISSING_EXPECTED_COUNT = $($missing.Count)" -ForegroundColor Cyan
foreach ($name in $missing) {
    Write-Host "MISSING: $name" -ForegroundColor Yellow
}

Write-Host "INSTALL_SYSTEM_C_FINAL_DOCS_COMPLETE" -ForegroundColor Green
