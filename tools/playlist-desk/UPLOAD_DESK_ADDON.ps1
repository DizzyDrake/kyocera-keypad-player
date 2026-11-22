# Adds only the desktop companion, its source-check workflow, the public README,
# and the add-on guide to an EXISTING Dumbplayer DEV17 GitHub repository.
# Changes are presented for review and never force-pushed.
param([Parameter(Mandatory=$true)][string]$RepositoryUrl)
$ErrorActionPreference = 'Stop'
if ($RepositoryUrl -notmatch '^https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:[.]git)?/?$') {
    throw 'Provide the HTTPS URL of your existing GitHub repository.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {throw 'Git for Windows was not found.'}
$repoSource = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$files = @('README.md', 'PLAYLIST_DESK_ADDON_READ_FIRST.md', '.github\workflows\playlist-desk-source-checks.yml')
foreach ($file in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoSource $file))) { throw "Missing overlay file: $file" }
}
$desk = Join-Path $repoSource 'tools\playlist-desk'
foreach ($file in @('src\launch_windows.cmd','src\launch_linux.sh','VERIFY_INTEGRATED_SOURCE.py')) {
    if (-not (Test-Path -LiteralPath (Join-Path $desk $file))) { throw "Missing Playlist Desk file: $file" }
}
$tempDir = Join-Path $env:LOCALAPPDATA 'Temp'
if ([IO.Path]::GetPathRoot($tempDir).TrimEnd('\') -ieq 'F:') {throw 'Choose a system temporary location away from the protected drive.'}
$clone = Join-Path $tempDir ('dumbplayer-playlist-desk-overlay-' + [guid]::NewGuid().ToString('N'))
Write-Host "Cloning into $clone"
& git clone --depth 1 $RepositoryUrl $clone
if ($LASTEXITCODE -ne 0) {throw 'Git clone failed; no repository was changed.'}
if (-not (Test-Path -LiteralPath (Join-Path $clone '.github\workflows\dev17-unsigned-local-sign.yml'))) {
    throw "The cloned repository has no DEV17 workflow. Check the repository URL. Clone retained at $clone"
}
foreach ($relative in $files) {
    $target = Join-Path $clone $relative
    $parent = Split-Path -Parent $target
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $repoSource $relative) -Destination $target -Force
}
$sourceRoot = (Resolve-Path -LiteralPath $desk).Path.TrimEnd('\')
$targetRoot = Join-Path $clone 'tools\playlist-desk'
Get-ChildItem -LiteralPath $sourceRoot -Recurse -Force -File | ForEach-Object {
    $relative = $_.FullName.Substring($sourceRoot.Length).TrimStart('\', '/')
    if ($relative -match '(^|[\\/])(__pycache__|\.git|\.pytest_cache)([\\/]|$)' -or $relative -match '\.(pyc|pyo)$') {return}
    $target = Join-Path $targetRoot $relative
    $parent = Split-Path -Parent $target
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $target -Force
}
& git -C $clone add -- README.md PLAYLIST_DESK_ADDON_READ_FIRST.md .github/workflows/playlist-desk-source-checks.yml tools/playlist-desk
if ($LASTEXITCODE -ne 0) {throw "Staging failed; inspect $clone"}
Write-Host 'Playlist Desk overlay changes:'
& git -C $clone diff --cached --stat
& git -C $clone diff --cached --name-only
& git -C $clone diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host 'These files are already in the repository; no update needed.'; exit 0 }
Write-Host 'Please review the changes above.'
$ok = Read-Host 'Commit and push this desktop companion update? Type yes to confirm'
if ($ok -cne 'yes') { Write-Host "No push made. Local clone: $clone"; exit 0 }
& git -C $clone commit -m 'Add Playlist Desk Windows and Linux companion'
if ($LASTEXITCODE -ne 0) {throw "Commit failed; inspect $clone"}
& git -C $clone push
if ($LASTEXITCODE -ne 0) {throw "Push failed; committed clone retained at $clone"}
Write-Host 'Playlist Desk companion pushed. The existing Android source and build workflow were untouched.'
