@echo off
cd /d "%~dp0"
echo ============================================
echo   SYNC 81plus-automation su GitHub (PlanB76)
echo ============================================
echo.
where git >nul 2>&1
if errorlevel 1 (
  echo [X] Git non e' installato o non e' nel PATH.
  echo     Installa Git: https://git-scm.com/download/win  poi rilancia.
  pause
  exit /b
)
echo [1] Salvo le modifiche locali...
git add -A
git commit -m "sync 81plus"
echo.
echo [2] Scarico dal cloud (merge)...
git pull --no-rebase --no-edit origin main
echo.
echo [3] Carico su GitHub...
git push origin main
echo.
echo Fatto. Se chiede login usa il tuo account GitHub.
pause
