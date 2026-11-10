param(
    [string]$Target = "",
    [string]$Project = "",
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$SkillName = "claude-account-safety"
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Project) {
    $Target = Join-Path $Project ".agents\skills"
}
if (-not $Target) {
    $Target = ".\.agents\skills"
}

if ((Split-Path -Leaf $Target) -eq $SkillName) {
    $Dest = $Target
} else {
    $Dest = Join-Path $Target $SkillName
}

if (-not (Test-Path (Join-Path $SourceDir "SKILL.md"))) {
    throw "SKILL.md not found in $SourceDir"
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
    Write-Host "secret scan: $SourceDir"
    & python (Join-Path $SourceDir "scripts\secret_check.py") --root $SourceDir
    if ($LASTEXITCODE -ne 0) {
        throw "secret-like content found; refusing to install. Move real links/tokens to a password manager and keep only op:// / env: / keychain: references."
    }
} else {
    Write-Warning "python not found; skipping secret scan."
}

Write-Host "source: $SourceDir"
Write-Host "dest:   $Dest"

if (Test-Path $Dest) {
    if (-not $Force) {
        throw "target exists. Re-run with -Force to back it up and replace."
    }
    $Backup = "$Dest.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Write-Host "backup: $Backup"
    if (-not $DryRun) {
        Move-Item -LiteralPath $Dest -Destination $Backup
    }
}

if ($DryRun) {
    Write-Host "[dry-run] would copy $SourceDir -> $Dest"
    exit 0
}

$Parent = Split-Path -Parent $Dest
if ($Parent) {
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
}
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

$Robocopy = Get-Command robocopy -ErrorAction SilentlyContinue
if ($Robocopy) {
    & robocopy $SourceDir $Dest /E /XD dist .git __pycache__ /XF secrets.env machine-profile.json egress.json setup-report.md profile.yaml | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
} else {
    Write-Warning "robocopy not found; copying everything (review for secrets before sharing)."
    Copy-Item -Path (Join-Path $SourceDir "*") -Destination $Dest -Recurse -Force
}

if (-not (Test-Path (Join-Path $Dest "SKILL.md"))) {
    throw "install verification failed; $Dest\SKILL.md missing"
}

Write-Host "installed: $Dest"
Write-Host ""
Write-Host "Next:"
Write-Host "  python `"$Dest\scripts\doctor.py`" --summary"
Write-Host "  Read `"$Dest\references\09-new-machine.md`""
Write-Host "  Invoke the skill from your agent (e.g. `$claude-account-safety)."
