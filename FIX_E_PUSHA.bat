@echo off
REM Commit + push in un clic del repo automazione (per applicare le fix su GitHub).
cd /d C:\81PLUS_GLOBAL_MASTER\81plus.net\GITHUB_81PLUS_AUTOMATION
echo === Aggiungo tutte le modifiche ===
git add -A
set /p MSG=Messaggio commit (INVIO per default): 
if "%MSG%"=="" set MSG=fix automazione SICURIX
git commit -m "%MSG%"
echo === Pull (evito conflitti) ===
git pull --rebase
echo === Push su GitHub ===
git push
echo.
echo FATTO. Ora vai su GitHub Actions e fai Run/Re-run del workflow.
pause
