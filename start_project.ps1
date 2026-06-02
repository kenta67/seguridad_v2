$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BackendEnv = Join-Path $Backend ".env"
$FrontendEnv = Join-Path $Frontend ".env"
$BackendLog = "C:\tmp\seguridad_backend.log"
$BackendErr = "C:\tmp\seguridad_backend_error.log"

function Assert-FileValue {
    param(
        [string]$Path,
        [string]$Name
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "No existe $Path"
    }
    $Line = Get-Content -LiteralPath $Path | Where-Object { $_ -like "$Name=*" } | Select-Object -First 1
    if (-not $Line -or $Line -match "TU-|TU_" -or $Line.EndsWith("=")) {
        throw "Configura $Name en $Path antes de iniciar."
    }
}

function Stop-Port {
    param([int]$Port)
    $Ids = netstat -ano |
        Select-String ":$Port" |
        ForEach-Object { ($_ -split "\s+")[-1] } |
        Where-Object { $_ -match "^\d+$" -and $_ -ne "0" } |
        Sort-Object -Unique

    foreach ($ProcessId in $Ids) {
        Stop-Process -Id ([int]$ProcessId) -Force -ErrorAction SilentlyContinue
    }
}

Assert-FileValue -Path $BackendEnv -Name "SUPABASE_URL"
Assert-FileValue -Path $BackendEnv -Name "SUPABASE_SERVICE_ROLE_KEY"
Assert-FileValue -Path $FrontendEnv -Name "VITE_SUPABASE_URL"
Assert-FileValue -Path $FrontendEnv -Name "VITE_SUPABASE_ANON_KEY"
Assert-FileValue -Path $FrontendEnv -Name "VITE_API_URL"

Stop-Port -Port 8001
Stop-Port -Port 5173

$PortStillBusy = netstat -ano | Select-String ":8001"
if ($PortStillBusy) {
    # Some Python child processes launched by uvicorn can survive with a stale PID on Windows.
    # If the API port is still busy here, close loose Python 3.12 children before starting cleanly.
    cmd /c "taskkill /IM python3.12.exe /F /T >nul 2>nul"
    Start-Sleep -Seconds 1
}

Start-Process `
    -WindowStyle Hidden `
    -FilePath (Join-Path $Backend ".venv\Scripts\python.exe") `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001" `
    -WorkingDirectory $Backend `
    -RedirectStandardOutput $BackendLog `
    -RedirectStandardError $BackendErr

$BackendReady = $false
for ($i = 0; $i -lt 90; $i++) {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -TimeoutSec 2 | Out-Null
        $BackendReady = $true
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $BackendReady) {
    Write-Host "Backend no inicio. Ultimos errores:"
    if (Test-Path -LiteralPath $BackendErr) {
        Get-Content -LiteralPath $BackendErr -Tail 30
    }
    throw "No se pudo iniciar FastAPI en 8001."
}

Start-Process `
    -WindowStyle Hidden `
    -FilePath "npm.cmd" `
    -ArgumentList "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173" `
    -WorkingDirectory $Frontend

Write-Host ""
Write-Host "Proyecto iniciado correctamente."
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend:  http://127.0.0.1:8001"
Write-Host ""
