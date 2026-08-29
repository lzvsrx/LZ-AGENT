param(
    [switch]$Watch,
    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$git = "C:\Program Files\Git\cmd\git.exe"
if (-not (Test-Path -LiteralPath $git)) { $git = "git" }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot ".git"))) {
    throw "A sincronização só pode executar na raiz verificada do repositório."
}

function Invoke-SafeSync {
    Push-Location $projectRoot
    try {
        $tracked = @(& $git diff --name-only)
        $untracked = @(& $git ls-files --others --exclude-standard)
        $paths = @($tracked + $untracked | Where-Object { $_ } | Sort-Object -Unique)
        if ($paths.Count -eq 0) { return }

        $blockedName = '(?i)(^|/)(\.env($|\.)|.*secret.*|.*token.*|.*credential.*|.*password.*|data/backups/|.*\.db($|-|\.)|.*\.pfx$|.*\.keystore$)'
        $blockedContent = '(?i)(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+|sk-[A-Za-z0-9_-]{20,})'
        foreach ($relativePath in $paths) {
            if ($relativePath -match $blockedName) {
                throw "Sincronização bloqueada por arquivo sensível: $relativePath"
            }
            $absolutePath = Join-Path $projectRoot $relativePath
            if (Test-Path -LiteralPath $absolutePath -PathType Leaf) {
                if ((Get-Item -LiteralPath $absolutePath).Length -gt 25MB) {
                    throw "Sincronização bloqueada por arquivo maior que 25 MB: $relativePath"
                }
                $match = $false
                if ($relativePath -ne "scripts/safe-github-sync.ps1") {
                    $match = Select-String -LiteralPath $absolutePath -Pattern $blockedContent -Quiet -ErrorAction SilentlyContinue
                }
                if ($match) { throw "Possível segredo detectado em: $relativePath" }
            }
        }

        & .\.venv\Scripts\python.exe -m ruff check .
        if ($LASTEXITCODE -ne 0) { throw "Ruff falhou; nada foi enviado." }
        & .\.venv\Scripts\python.exe -m pytest
        if ($LASTEXITCODE -ne 0) { throw "Testes falharam; nada foi enviado." }
        if (Test-Path -LiteralPath "apps/web/static/app.js") {
            & node --check apps/web/static/app.js
            if ($LASTEXITCODE -ne 0) { throw "JavaScript inválido; nada foi enviado." }
        }

        & $git add -- $paths
        if ($LASTEXITCODE -ne 0) { throw "Não foi possível preparar os arquivos seguros." }
        & $git diff --cached --quiet
        if ($LASTEXITCODE -eq 0) { return }
        $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
        & $git commit -m "chore: safe automatic sync $stamp"
        if ($LASTEXITCODE -ne 0) { throw "O commit automático falhou." }
        $branch = (& $git branch --show-current).Trim()
        if (-not $branch) { throw "Branch atual não identificada." }
        & $git push origin $branch
        if ($LASTEXITCODE -ne 0) { throw "O push automático falhou; o commit permanece local." }
    }
    finally {
        Pop-Location
    }
}

if ($Watch) {
    while ($true) {
        try { Invoke-SafeSync } catch { Write-Error $_ -ErrorAction Continue }
        Start-Sleep -Seconds ([Math]::Max($IntervalSeconds, 15))
    }
} else {
    Invoke-SafeSync
}
