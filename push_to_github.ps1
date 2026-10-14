# Pushing IntelliCluster to GitHub
$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Pushing IntelliCluster to GitHub" -ForegroundColor Cyan
Write-Host "  Remote: https://github.com/AkashS-0107/Intellicluster.git" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

# Check if git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git is not installed or not in PATH. Please install Git from https://git-scm.com/"
    exit 1
}

# 1. Initialize Git
if (-not (Test-Path ".git")) {
    Write-Host "[1/5] Initializing Git repository..." -ForegroundColor Yellow
    git init
} else {
    Write-Host "[1/5] Git repository already initialized." -ForegroundColor Green
}

# 2. Main branch
Write-Host "[2/5] Setting main branch..." -ForegroundColor Yellow
git branch -M main

# 3. Remote URL
Write-Host "[3/5] Setting remote origin..." -ForegroundColor Yellow
$remotes = git remote
if ($remotes -contains "origin") {
    git remote set-url origin "https://github.com/AkashS-0107/Intellicluster.git"
} else {
    git remote add origin "https://github.com/AkashS-0107/Intellicluster.git"
}

# 4. Add & Commit
Write-Host "[4/5] Staging files and creating initial commit..." -ForegroundColor Yellow
git add .
$status = git status --porcelain
if ($status) {
    git commit -m "Initial commit: IntelliCluster ML-driven cloud workload orchestration"
} else {
    Write-Host "No new changes to commit." -ForegroundColor Green
}

# 5. Push
Write-Host "[5/5] Pushing to GitHub (origin main)..." -ForegroundColor Yellow
try {
    git push -u origin main
    Write-Host "`nSuccessfully pushed to https://github.com/AkashS-0107/Intellicluster" -ForegroundColor Green
} catch {
    Write-Host "`nPush was rejected or remote has commits. Attempting rebase..." -ForegroundColor Yellow
    git pull origin main --rebase
    git push -u origin main
    Write-Host "`nSuccessfully rebased and pushed!" -ForegroundColor Green
}
