[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root 'apps\web\static\logo.svg'
$brand = Join-Path $root 'assets\brand'
$windows = Join-Path $root 'apps\windows\Assets'
$magick = 'C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe'
if (-not (Test-Path -LiteralPath $magick)) { throw 'ImageMagick 7.1.2 não encontrado.' }

New-Item -ItemType Directory -Force -Path $brand | Out-Null

& $magick -background none $source -resize '1024x1024' (Join-Path $brand 'lz-agent-icon-1024.png')
& $magick -background none $source -define 'icon:auto-resize=256,128,64,48,32,24,16' (Join-Path $windows 'AppIcon.ico')
& $magick -background none $source -resize '88x88' (Join-Path $windows 'Square44x44Logo.scale-200.png')
& $magick -background none $source -resize '48x48' (Join-Path $windows 'Square44x44Logo.targetsize-24_altform-unplated.png')
& $magick -background none $source -resize '96x96' (Join-Path $windows 'Square44x44Logo.targetsize-48_altform-lightunplated.png')
& $magick -background none $source -resize '300x300' (Join-Path $windows 'Square150x150Logo.scale-200.png')
& $magick -background none $source -resize '100x100' (Join-Path $windows 'StoreLogo.png')
& $magick -background none $source -resize '96x96' (Join-Path $windows 'LockScreenLogo.scale-200.png')
& $magick -background '#07121f' $source -resize '240x240' -gravity center -extent '620x300' (Join-Path $windows 'Wide310x150Logo.scale-200.png')
& $magick -background '#07121f' $source -resize '280x280' -gravity center -extent '1240x600' (Join-Path $windows 'SplashScreen.scale-200.png')

Write-Output "Assets canônicos gerados a partir de $source"
