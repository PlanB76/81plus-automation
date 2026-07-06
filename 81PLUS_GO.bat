@echo off
cd /d "%~dp0"
echo ==================================================
echo   81PLUS GO - comando globale unico (SICURIX)
echo ==================================================
echo.
where git >nul 2>&1
if errorlevel 1 (
  echo [X] Git non installato. Scarica: https://git-scm.com/download/win
  pause
  exit /b
)
echo [1] Salvo tutte le modifiche...
git add -A
git commit -m "81PLUS GO: deploy globale SICURIX"
echo.
echo [2] Allineo col cloud...
git pull --no-rebase --no-edit origin main
if errorlevel 1 (
  echo [!] Conflitto sugli output: tengo la versione cloud e proseguo...
  git checkout --theirs cloud/out cloud/data/sicurix_gen_state.json cloud/data/sicurix_tg_state.json 2>nul
  git add -A
  git commit -m "81PLUS GO: risolvo conflitti output" --no-edit
)
echo.
echo [3] Carico su GitHub (attiva la cloud H24: fumetto+immagine+feed+Telegram ogni 10 min)...
git push origin main
echo.
echo [4] Pubblico il sito con il ticker SICURIX su Hostinger...
if exist "%~dp0..\0-81PLUS.NET\DEPLOY81_FTP.bat" (
  call "%~dp0..\0-81PLUS.NET\DEPLOY81_FTP.bat"
) else (
  echo [i] DEPLOY81_FTP.bat non trovato: salto il deploy sito.
)
echo.
echo [OK] FATTO TUTTO. Cloud SICURIX attiva H24 + sito aggiornato col ticker.
pause
