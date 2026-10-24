Get-NetFirewallRule -DisplayName "VerityAI offline block*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
Write-Host "Offline block removed. Internet access restored for Python."