[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl,

    [string]$Branch = "main",

    [string]$CommitMessage = "feat: publish boardroom ai project"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    & git -C $projectRoot @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git -C `"$projectRoot`" $($Args -join ' ')"
    }
}

Write-Host "Preparing standalone GitHub push from: $projectRoot"

if (-not (Test-Path (Join-Path $projectRoot ".git"))) {
    throw "No .git directory found in $projectRoot. Initialize the repo first."
}

Invoke-Git -Args @("add", ".")

$status = (& git -C $projectRoot status --short).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read git status."
}

if ($status) {
    Invoke-Git -Args @("commit", "-m", $CommitMessage)
}
else {
    Write-Host "No new changes to commit. Continuing with remote setup and push."
}

Invoke-Git -Args @("branch", "-M", $Branch)

$hasOrigin = $false
$remoteOutput = & git -C $projectRoot remote
if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect git remotes."
}

if ($remoteOutput -contains "origin") {
    $hasOrigin = $true
}

if ($hasOrigin) {
    Invoke-Git -Args @("remote", "set-url", "origin", $RepoUrl)
}
else {
    Invoke-Git -Args @("remote", "add", "origin", $RepoUrl)
}

Invoke-Git -Args @("push", "-u", "origin", $Branch)

Write-Host ""
Write-Host "Push complete."
Write-Host "Repo URL: $RepoUrl"
Write-Host "Branch: $Branch"
