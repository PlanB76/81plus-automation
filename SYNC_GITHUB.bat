@echo off
cd /d "%~dp0"
echo ============================================
echo   ATTIVA SICURIX H24 - sync su GitHub
echo ============================================
echo.
where git >nul 2>&1
if errorlevel 1 (
  echo [X] Git non installato. Scarica: https://git-scm.com/download/win
  pause
  exit /b
)
echo [1] Salvo le modifiche locali...
git add -A
git commit -m "SICURIX H24: fix key strip + 1 ogni 10 min"
echo.
echo [2] Allineo col cloud (merge)...
git pull --no-rebase --no-edit origin main
if errorlevel 1 (
  echo [!] Conflitto sugli output: tengo la versione del cloud e proseguo...
  git checkout --theirs cloud/out cloud/data/sicurix_gen_state.json cloud/data/sicurix_tg_state.json 2>nul
  git add -A
  git commit -m "SICURIX: risolvo conflitti output" --no-edit
)
echo.
echo [3] Carico su GitHub...
git push origin main
echo.
echo [OK] Fatto. Il workflow SICURIX ora gira ogni 10 minuti (1 immagine).
pause
