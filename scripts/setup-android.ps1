[CmdletBinding()]
param([switch]$SkipLicenses)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$sdk = Join-Path $root ".toolchains\android-sdk"
$manager = Join-Path $sdk "cmdline-tools\latest\bin\sdkmanager.bat"
$jdk = "C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot"

if (-not (Test-Path -LiteralPath $manager)) {
    throw "Android Command-line Tools ausente. Consulte docs/development/android-vscode.md."
}
if (-not (Test-Path -LiteralPath $jdk)) {
    throw "JDK 17 ausente. Instale Microsoft.OpenJDK.17 com winget."
}

$env:JAVA_HOME = $jdk
if (-not $SkipLicenses) {
    1..20 | ForEach-Object { "y" } | & $manager --sdk_root=$sdk --licenses | Out-Host
}
& $manager --sdk_root=$sdk "platform-tools" "platforms;android-36" "build-tools;36.0.0"
if ($LASTEXITCODE -ne 0) { throw "Falha ao preparar o SDK Android." }

$localProperties = Join-Path $root "apps\android\local.properties"
$escaped = $sdk.Replace("\", "\\").Replace(":", "\:")
[IO.File]::WriteAllText($localProperties, "sdk.dir=$escaped`n", [Text.UTF8Encoding]::new($false))
Write-Host "Android SDK pronto em $sdk"
