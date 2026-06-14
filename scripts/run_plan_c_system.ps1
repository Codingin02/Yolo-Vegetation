param(
    [string]$HostAddress = "0.0.0.0",
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Python venv tidak ditemukan: $Python"
}

Write-Host "PLAN_C_SINGLE_CLASS_SYSTEM_START"
Write-Host "Working directory: $Root"

$SecretsFile = Join-Path $Root "config\secrets.env"
if (Test-Path $SecretsFile) {
    Get-Content $SecretsFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $parts = $line.Split("=", 2)
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if ($key -and -not [Environment]::GetEnvironmentVariable($key, "Process")) {
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "PLAN_C_SECRETS_ENV_LOADED"
}

if ($env:GROK_API_KEY -and -not $env:XAI_API_KEY) {
    $env:XAI_API_KEY = $env:GROK_API_KEY
}
if ($env:XAI_API_KEY -and -not $env:GROK_API_KEY) {
    $env:GROK_API_KEY = $env:XAI_API_KEY
}

Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($listener in $listeners) {
    if ($listener.OwningProcess) {
        Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

& $Python -m py_compile `
    src\ulp_project\plan_c_yolo.py `
    src\ulp_project\plan_c_ai_core_consensus.py `
    src\ulp_project\plan_c_processor.py `
    src\ulp_project\plan_c_geometry.py `
    src\ulp_project\plan_c_yolo_compatible_renderer.py `
    src\ulp_project\plan_c_routes.py `
    scripts\plan_c_smoke.py `
    scripts\plan_c_ai_backend_smoke.py `
    scripts\run_plan_c_server.py

& $Python scripts\plan_c_smoke.py
& $Python scripts\plan_c_ai_backend_smoke.py

$LogDir = Join-Path $Root "data\runtime\plan_c\server_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$OutLog = Join-Path $LogDir "plan_c_server_stdout.log"
$ErrLog = Join-Path $LogDir "plan_c_server_stderr.log"

$argsList = @(
    "scripts\run_plan_c_server.py",
    "--host", $HostAddress,
    "--port", [string]$Port
)
$server = Start-Process -FilePath $Python -ArgumentList $argsList -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru

$localUrl = "http://127.0.0.1:$Port/plan-c"
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri $localUrl -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        if ($server.HasExited) {
            break
        }
    }
}

if (-not $ready) {
    Write-Host "PLAN_C_LOCAL_ROUTE_NOT_READY"
    Write-Host "stdout: $OutLog"
    Write-Host "stderr: $ErrLog"
    if (-not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

Write-Host "PLAN C server ready"
Write-Host "Laptop: $localUrl"

$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrok) {
    Write-Host "NGROK_NOT_FOUND"
    Write-Host "Jalankan manual: ngrok http $Port"
    exit 0
}

$ngrokLog = Join-Path $LogDir "ngrok.log"
Start-Process -FilePath $ngrok.Source -ArgumentList @("http", [string]$Port) -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $ngrokLog -RedirectStandardError $ngrokLog | Out-Null
Start-Sleep -Seconds 4

try {
    $tunnel = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5
    $publicUrl = ($tunnel.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
    if ($publicUrl) {
        Write-Host "BUKA DI HP: $publicUrl/plan-c"
    } else {
        Write-Host "NGROK_TUNNEL_URL_NOT_READY"
        Write-Host "Cek manual: http://127.0.0.1:4040"
    }
} catch {
    Write-Host "NGROK_TUNNEL_STATUS_UNAVAILABLE"
    Write-Host "Cek manual: http://127.0.0.1:4040"
}
