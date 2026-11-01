[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$backend = Join-Path $PSScriptRoot "backend"
$frontend = Join-Path $PSScriptRoot "frontend"
$python = Join-Path $backend "venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Backend Python was not found at $python."
}
foreach ($artifact in @("faiss.index", "chunks.json")) {
    if (-not (Test-Path -LiteralPath (Join-Path $backend "data\index\$artifact") -PathType Leaf)) {
        throw "Missing $artifact. Run scripts/build_index.py from backend first."
    }
}

$listeners = @(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)
if ($listeners.Count -gt 0) {
    throw "Port 8000 is already in use. Stop the old VERITAS backend with Ctrl+C, then run this launcher again. No process was stopped automatically."
}

Get-Command npm.cmd -ErrorAction Stop | Out-Null
$previousApiUrl = [Environment]::GetEnvironmentVariable("VITE_API_URL", "Process")
try {
    Set-Location -LiteralPath $frontend
    # Compile API calls relative to the same origin that serves the website.
    $env:VITE_API_URL = "/"
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend build failed. Fix the errors above before starting the server."
    }
}
finally {
    [Environment]::SetEnvironmentVariable("VITE_API_URL", $previousApiUrl, "Process")
}

Set-Location -LiteralPath $backend
Write-Host ""
Write-Host "After Application startup complete, open http://127.0.0.1:8000"
Write-Host "This one server runs the website and API. Keep this terminal open."
Write-Host "Python code changes reload automatically. Restart this launcher after UI changes or index rebuilds."
Write-Host ""
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
if ($LASTEXITCODE -ne 0) {
    throw "VERITAS stopped with an error. Review the server output above."
}
