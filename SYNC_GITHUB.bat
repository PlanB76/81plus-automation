@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===== SYNC 81plus-automation -> GitHub (PlanB76) =====
git add -A
git commit -m "sync %date% %time%"
git push
echo.
echo Se chiede login: usa il tuo token GitHub. Fatto.
pause
