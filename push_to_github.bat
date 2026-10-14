@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   Pushing IntelliCluster to GitHub
echo   Remote: https://github.com/AkashS-0107/Intellicluster.git
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in PATH!
    echo Please install Git from https://git-scm.com/ and try again.
    pause
    exit /b 1
)

:: 2. Initialize git if not already initialized
if not exist ".git" (
    echo [1/5] Initializing Git repository...
    git init
    if %errorlevel% neq 0 (
        echo [ERROR] git init failed.
        pause
        exit /b %errorlevel%
    )
) else (
    echo [1/5] Git repository already initialized.
)

:: 3. Set branch to main
echo [2/5] Setting main branch...
git branch -M main

:: 4. Configure remote origin
echo [3/5] Setting remote origin...
git remote get-url origin >nul 2>nul
if %errorlevel% equ 0 (
    git remote set-url origin https://github.com/AkashS-0107/Intellicluster.git
) else (
    git remote add origin https://github.com/AkashS-0107/Intellicluster.git
)

:: 5. Stage files and commit
echo [4/5] Staging files and committing...
git add .
git commit -m "Initial commit: IntelliCluster ML-driven cloud workload orchestration"

:: 6. Push to GitHub
echo [5/5] Pushing to GitHub (origin main)...
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo --------------------------------------------------------
    echo If push was rejected because remote has existing commits
    echo (e.g. an existing README/LICENSE created on GitHub):
    echo Trying to rebase and push...
    echo --------------------------------------------------------
    git pull origin main --rebase
    git push -u origin main
)

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   Successfully pushed to GitHub!
    echo   https://github.com/AkashS-0107/Intellicluster
    echo ========================================================
) else (
    echo.
    echo [NOTICE] Push encountered an issue. Please verify your GitHub
    echo login / credentials or check error messages above.
)

echo.
pause
