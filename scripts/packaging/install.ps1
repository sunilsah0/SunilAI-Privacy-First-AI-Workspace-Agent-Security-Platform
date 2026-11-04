# SunilAI installer for Windows. Run it from this folder:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
# Options: -SkipModels   -Domain name -Email address   -Preset file
param(
  [switch]$SkipModels,
  [string]$Domain = "",
  [string]$Email = "",
  [string]$Preset = ".env.template"
)
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker is not installed. Install Docker Desktop, start it, then run this again."
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
  throw "Docker is installed but not running. Start Docker Desktop and try again."
}
if ($Domain -and -not $Email) { throw "-Domain also needs -Email" }

# Random secrets come from the operating system's cryptographic random source.
function New-Secret([int]$Bytes) {
  $buffer = New-Object byte[] $Bytes
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $rng.GetBytes($buffer)
  $rng.Dispose()
  return (($buffer | ForEach-Object { $_.ToString("x2") }) -join "")
}

$script:inviteCode = ""
if (Test-Path ".env") {
  Write-Host ".env already exists, so I am keeping your existing settings and secrets."
} else {
  if (-not (Test-Path $Preset)) { throw "$Preset is missing from this folder." }
  $lines = @(Get-Content $Preset | ForEach-Object {
    if ($_ -match '^(?<key>[A-Z_]+)=CHANGE_ME\s*$') {
      $key = $Matches['key']
      if ($key -eq 'INVITE_CODE') {
        $script:inviteCode = New-Secret 12
        "INVITE_CODE=$($script:inviteCode)"
      } else {
        "$key=$(New-Secret 32)"
      }
    } else {
      $_
    }
  })
  if ($Domain) {
    $lines += "SITE_ADDRESS=$Domain"
    $lines += "ACME_EMAIL=$Email"
  }
  # Plain ASCII text. Other encodings can make the file unreadable for Docker.
  Set-Content -Path ".env" -Value $lines -Encoding ascii
  try { icacls ".env" /inheritance:r /grant:r "$($env:USERNAME):(R,W)" *> $null } catch { }
  Write-Host "Created .env with fresh random secrets. Keep it private and back it up."
}

$files = @("-f", "docker-compose.release.yml")
if (Select-String -Path ".env" -Pattern '^SITE_ADDRESS=' -Quiet) {
  $files += @("-f", "docker-compose.https.yml")
}

docker compose @files up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose failed. Read the messages above." }

$demoAi = Select-String -Path ".env" -Pattern '^MODEL_PROVIDER=fake' -Quiet
if (-not $SkipModels -and -not $demoAi) {
  Write-Host "Downloading the AI models (this is the only step that uses the internet at run time)..."
  docker compose @files --profile setup run --rm model-puller
}

$site = ""
$match = Select-String -Path ".env" -Pattern '^SITE_ADDRESS=(.+)$'
if ($match) { $site = $match.Matches[0].Groups[1].Value.Trim() }
if ($site) {
  if ($site -like "http*") { $url = $site } else { $url = "https://$site" }
} else {
  $url = "http://localhost:8080"
}
Write-Host ""
Write-Host "SunilAI is starting. Open: $url"
if ($script:inviteCode) {
  Write-Host "Invite code for new accounts (share it only with people you trust): $($script:inviteCode)"
}
