# Windows one-click start (API 8000 + Web 5173)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$ApiPort = if ($env:DPI_API_PORT) { $env:DPI_API_PORT } else { "8000" }
$WebPort = if ($env:DPI_WEB_PORT) { $env:DPI_WEB_PORT } else { "5173" }

Write-Host "[dpi] root: $Root"

# Backend
Set-Location (Join-Path $Root "backend")
if (-not (Test-Path ".venv")) {
  Write-Host "[dpi] creating venv..."
  python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
Write-Host "[dpi] starting backend on 0.0.0.0:$ApiPort ..."
Start-Process -FilePath ".\.venv\Scripts\uvicorn.exe" `
  -ArgumentList @("app.main:app", "--host", "0.0.0.0", "--port", $ApiPort) `
  -RedirectStandardOutput (Join-Path $LogDir "api.log") `
  -RedirectStandardError (Join-Path $LogDir "api.err.log") `
  -WindowStyle Hidden

# Frontend
Set-Location (Join-Path $Root "frontend")
if (-not (Test-Path "node_modules")) {
  Write-Host "[dpi] npm install..."
  npm install
}
Write-Host "[dpi] starting frontend on 0.0.0.0:$WebPort ..."
Start-Process -FilePath "npm.cmd" `
  -ArgumentList @("run", "dev", "--", "--host", "0.0.0.0", "--port", $WebPort) `
  -RedirectStandardOutput (Join-Path $LogDir "web.log") `
  -RedirectStandardError (Join-Path $LogDir "web.err.log") `
  -WindowStyle Hidden

Write-Host "[dpi] ready"
Write-Host "[dpi]   UI : http://127.0.0.1:$WebPort"
Write-Host "[dpi]   API: http://127.0.0.1:$ApiPort/api/health"
Write-Host "[dpi]   logs: $LogDir"
