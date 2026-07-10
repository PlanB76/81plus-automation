@echo off
REM ============================================================
REM  Mette i 2 token YouTube nei secret GitHub, DAI FILE (nessun
REM  copia-incolla del valore). Repo: PlanB76/81plus-automation
REM ============================================================
setlocal
cd /d "%~dp0"
set "REPO=PlanB76/81plus-automation"

echo [1/4] Controllo GitHub CLI (gh)...
where gh >nul 2>nul
if errorlevel 1 (
  echo   gh non trovato: lo installo con winget...
  winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
  echo   Se l'installazione e' andata a buon fine, CHIUDI e rilancia questo file.
  pause
  exit /b
)

echo [2/4] Controllo login gh...
gh auth status >nul 2>nul
if errorlevel 1 (
  echo   Non sei loggato in gh. Parte il login nel browser: scegli GitHub.com, HTTPS, e autorizza.
  gh auth login -h github.com -p https -w
)

echo [3/4] Setto YOUTUBE_TOKEN_JSON (@sicurissimo)...
gh secret set YOUTUBE_TOKEN_JSON --repo %REPO% < token_sicurissimo.json && echo   OK sicurissimo

echo [4/4] Setto YOUTUBE_TOKEN_JSON_DESTINO (@destinorandagio)...
gh secret set YOUTUBE_TOKEN_JSON_DESTINO --repo %REPO% < token_destino.json && echo   OK destino

echo.
echo ============================================================
echo  FATTO. I due token sono nei secret di %REPO%.
echo  Ora lancia PUBBLICA_AUTOMAZIONI_GITHUB.bat per il push.
echo ============================================================
pause
