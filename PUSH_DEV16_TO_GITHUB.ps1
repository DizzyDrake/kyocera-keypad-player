# Dumbplayer DEV16 source uploader. Deliberately no force push, branch deletion,
# database/data deletion, keystore handling, device operation, or GitHub actions trigger.
param([Parameter(Mandatory=$true)][string]$RepositoryUrl)
$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($RepositoryUrl -notmatch '^https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:[.]git)?/?$') {
    throw 'Enter an HTTPS GitHub repository URL: https://github.com/owner/repo.git'
}
$gitCommand = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCommand) { throw 'Git for Windows was not found in PATH.' }
foreach ($must in @('settings.gradle','app\build.gradle','.github\workflows\dev16-unsigned-local-sign.yml','SOURCE_MANIFEST.json')) {
    if (-not (Test-Path -LiteralPath (Join-Path $source $must))) { throw "Missing source file: $must" }
}
$destination = Join-Path $env:TEMP ('dumbplayer-dev16-github-' + [guid]::NewGuid().ToString('N'))
Write-Host "Cloning $RepositoryUrl into temporary folder $destination"
& git clone --depth 1 $RepositoryUrl $destination
if ($LASTEXITCODE -ne 0) { throw 'Git clone failed; no files were copied.' }
$sourceRoot = (Resolve-Path -LiteralPath $source).Path.TrimEnd('\')
$count = 0
Get-ChildItem -LiteralPath $sourceRoot -Force -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($sourceRoot.Length).TrimStart('\','/')
    # Ignore local build/test artifacts if the script is rerun from an extracted tree.
    if ($relative -match '(^|[\\/])(?:\.git|\.gradle|__pycache__|\.build[^\\/]*|build)(?:[\\/]|$)' -or $relative -match '\.(apk|aab|jks|keystore|p12|pyc|class)$') { return }
    $target = Join-Path $destination $relative
    $parent = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    $script:count++
}
Write-Host "Copied $count source / project files."
Write-Host 'Changes to the temporary clone:'
& git -C $destination status --short
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect Git status.' }
& git -C $destination add -A
if ($LASTEXITCODE -ne 0) { throw 'Git stage failed.' }
& git -C $destination diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host 'Repository already contains these files. Nothing to commit.'; exit 0 }
Write-Host ''
Write-Host 'No remote changes have been made yet.'
$reply = Read-Host 'Commit and push exactly the staged updates to your existing GitHub branch? (yes/no)'
if ($reply -ne 'yes') { Write-Host "Not pushed. Files remain in $destination"; exit 0 }
& git -C $destination commit -m 'Consolidate Dumbplayer DEV16 source and Android build workflow'
if ($LASTEXITCODE -ne 0) { throw "Git commit failed; working copy remains at $destination" }
& git -C $destination push
if ($LASTEXITCODE -ne 0) { throw "Git push failed; committed working copy remains at $destination" }
Write-Host 'Pushed successfully. In GitHub Actions select Dumbplayer DEV16 unsigned candidate (local signing required).'
