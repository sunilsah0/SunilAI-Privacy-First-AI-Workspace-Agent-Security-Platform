# Run from the project folder in an ADMINISTRATOR PowerShell.
$ErrorActionPreference = "Stop"
$venvPython = (Resolve-Path ".\.venv\Scripts\python.exe").Path
$basePython = (& $venvPython -c "import sys; print(sys._base_executable)").Trim()
foreach ($exe in (@($venvPython, $basePython) | Select-Object -Unique)) {
    New-NetFirewallRule -DisplayName "VerityAI offline block - $exe" `
        -Direction Outbound -Program $exe -RemoteAddress Internet -Action Block | Out-Null
    Write-Host "Blocked internet access for: $exe"
}
Write-Host "Done. pip install will fail until you run scripts\offline-off.ps1"