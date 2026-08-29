[CmdletBinding()]
param([switch]$Strict)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$baseline = Get-Content -LiteralPath (Join-Path $root 'versions/technology-baseline.json') -Raw | ConvertFrom-Json
$results = [System.Collections.Generic.List[object]]::new()

function Add-Check([string]$Name, [string]$Expected, [string]$Actual, [bool]$Required) {
    $matches = $Actual -eq $Expected -or $Actual.StartsWith("$Expected.") -or $Actual.StartsWith("$Expected-")
    $results.Add([pscustomobject]@{Technology=$Name; Expected=$Expected; Actual=$Actual; Required=$Required; Matches=$matches})
}

$python = & (Join-Path $root '.venv\Scripts\python.exe') --version 2>&1
Add-Check 'python' $baseline.versions.python (($python -split ' ')[1]) $true
$dotnet = & 'C:\Program Files\dotnet\dotnet.exe' --version
Add-Check 'dotnet_sdk' $baseline.versions.dotnet_sdk $dotnet $true
$git = & 'C:\Program Files\Git\cmd\git.exe' --version
Add-Check 'git' $baseline.versions.git (($git -split ' ')[2]) $true

$ffmpegCommand = Get-Command ffmpeg -ErrorAction SilentlyContinue
$ffmpegFallback = Get-ChildItem -LiteralPath "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter ffmpeg.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
$ffmpegExecutable = if ($ffmpegCommand) { $ffmpegCommand.Source } elseif ($ffmpegFallback) { $ffmpegFallback.FullName } else { $null }
$ffmpeg = if ($ffmpegExecutable) { (& $ffmpegExecutable -version 2>&1 | Select-Object -First 1) } else { 'missing' }
$ffmpegVersion = if ($ffmpeg -match 'ffmpeg version ([^ ]+)') { $Matches[1] } else { 'missing' }
Add-Check 'ffmpeg' $baseline.versions.ffmpeg $ffmpegVersion $false

$jdk = Get-ChildItem -LiteralPath 'C:\Program Files\Microsoft' -Filter java.exe -Recurse -ErrorAction SilentlyContinue | Where-Object FullName -Match 'jdk-17' | Select-Object -First 1
$javaLine = if ($jdk) { (& $jdk.FullName --version | Select-Object -First 1) } else { 'missing' }
$javaVersion = if ($javaLine -match 'openjdk ([^ ]+)') { $Matches[1] } else { 'missing' }
Add-Check 'jdk' $baseline.versions.jdk $javaVersion $false

$rustc = 'C:\Users\valen\.cargo\bin\rustc.exe'
$rustLine = if (Test-Path -LiteralPath $rustc) { & $rustc --version } else { 'missing' }
$rustVersion = if ($rustLine -match 'rustc ([^ ]+)') { $Matches[1] } else { 'missing' }
Add-Check 'rust' $baseline.versions.rust $rustVersion $false

$results | Format-Table -AutoSize
$failed = @($results | Where-Object { -not $_.Matches -and ($_.Required -or $Strict) })
if ($failed.Count -gt 0) { throw "Stack divergiu do baseline em $($failed.Count) item(ns)." }
