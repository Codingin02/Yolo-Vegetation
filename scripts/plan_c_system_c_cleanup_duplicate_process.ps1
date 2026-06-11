param(
    [switch]$Kill
)

$ErrorActionPreference = "Stop"
$pattern = "plan_c_system_c_run_all_dataset_pipeline.py|plan_c_85b_direct_acquire_autolabel_package.py"
$matches = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match $pattern } |
    Select-Object ProcessId, CommandLine

if (-not $matches) {
    Write-Output "NO_DUPLICATE_SYSTEM_C_PIPELINE_PROCESS_FOUND"
    exit 0
}

if (-not $Kill) {
    $matches | ConvertTo-Json -Depth 3
    Write-Output "DUPLICATE_PROCESS_CHECK_ONLY_USE_-Kill_TO_TERMINATE"
    exit 0
}

foreach ($item in $matches) {
    Stop-Process -Id $item.ProcessId -Force
}

Write-Output "DUPLICATE_SYSTEM_C_PIPELINE_PROCESS_TERMINATED"
