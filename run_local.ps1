# Local stack without Docker: SQLite + API + Vite admin
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Push-Location $Backend
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python venv..."
    python -m venv .venv
}
Write-Host "pip install (backend)..."
& .\.venv\Scripts\pip.exe install -q -r requirements.txt
Pop-Location

Push-Location $Frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "npm install (frontend)..."
    npm install
}
Pop-Location

$dbUrl = "sqlite:///./parking.db"
$py = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "Starting API: http://127.0.0.1:8010  (DATABASE_URL=$dbUrl)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location `"$Backend`"; `$env:PYTHONPATH='$Backend'; `$env:DATABASE_URL='$dbUrl'; & `"$py`" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010"
)

Write-Host "Starting admin UI: http://127.0.0.1:5173" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location `"$Frontend`"; npx vite --host 127.0.0.1 --port 5173"
)

Write-Host ""
Write-Host "Opened two windows (API + Vite). SQLite file: backend\parking.db" -ForegroundColor Green
Write-Host "LiqPay: copy backend\.env.example -> backend\.env and set LIQPAY_PUBLIC_KEY / LIQPAY_PRIVATE_KEY" -ForegroundColor DarkGray
Write-Host "Default seed accounts after first start: admin@parking.local / admin123" -ForegroundColor Green
Write-Host "Flutter web (LiqPay return → /payment-success): cd flutter_client; flutter run -d chrome --web-port=8080 --dart-define=USE_MOCK=false --dart-define=API_BASE_URL=http://127.0.0.1:8010/api" -ForegroundColor DarkGray
Write-Host "LiqPay: APP_PUBLIC_API_URL must be reachable from the internet for the card step (use ngrok for local API)." -ForegroundColor DarkGray
