$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")

$PythonBin = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$HostName = if ($env:CLOUDSAVER_HOST) { $env:CLOUDSAVER_HOST } else { "127.0.0.1" }
$Port = if ($env:CLOUDSAVER_PORT) { $env:CLOUDSAVER_PORT } else { "8765" }

if (-not $env:PYTHON -and (Test-Path $VenvPython)) {
  $PythonBin = $VenvPython
}

Set-Location $RepoRoot

Write-Host "Starting CloudSaver at http://${HostName}:$Port"
& $PythonBin -m cloudsaver.web_server --host $HostName --port $Port
