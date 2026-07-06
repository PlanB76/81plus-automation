@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo ==========================================================
echo    ACCENDI SICURIX  -  un solo click accende tutto H24
echo ==========================================================
echo.

REM --- 0) prerequisiti ---
where gh >nul 2>&1
if errorlevel 1 (
  echo [!] Manca GitHub CLI. Installalo UNA volta con:
  echo       winget install --id GitHub.cli
  echo    poi:  gh auth login   (scegli GitHub.com, HTTPS, login browser)
  echo    Poi rilancia questo file.
  pause & exit /b
)
gh auth status >nul 2>&1
if errorlevel 1 ( echo [i] Devo autenticare gh (si apre il browser una volta)... & gh auth login )

if not exist "81plus_secrets.env" (
  echo [!] Manca 81plus_secrets.env . Copia 81plus_secrets.env.TEMPLATE in 81plus_secrets.env,
  echo     incolla dentro YOUTUBE_API_KEY e TELEGRAM_BOT_TOKEN, salva, e rilancia.
  pause & exit /b
)

REM --- 1) OAuth YouTube (token) se manca ---
if not exist "youtube_token.json" (
  echo [i] Genero il token YouTube (accetta il consenso Google nel browser)...
  if exist "auth_youtube.py" ( python auth_youtube.py ) else ( echo [!] auth_youtube.py non trovato: salto - l'evergreen/riciclo restera' in DRY-RUN )
)

REM --- 2) leggo i segreti dal file locale e li carico su GitHub (gh) ---
for /f "usebackq tokens=1,* delims==" %%A in ("81plus_secrets.env") do (
  set "K=%%A" & set "V=%%B"
  echo !K! | findstr /b "#" >nul || (
    if /I "!K!"=="TG_CHANNEL" ( gh variable set !K! --body "!V!" >nul 2>&1 & echo   var !K! ok
    ) else if /I "!K!"=="YT_CHANNEL_ID" ( gh variable set !K! --body "!V!" >nul 2>&1 & echo   var !K! ok
    ) else if /I "!K!"=="TALES_DRIVE_FOLDER" ( gh variable set !K! --body "!V!" >nul 2>&1 & echo   var !K! ok
    ) else if not "!V!"=="" ( echo !V!| gh secret set !K! >nul 2>&1 & echo   secret !K! ok )
  )
)
if exist "youtube_token.json" ( type youtube_token.json | gh secret set YOUTUBE_TOKEN_JSON >nul 2>&1 & echo   secret YOUTUBE_TOKEN_JSON ok )

REM --- 3) pubblico tutto su GitHub ---
echo [i] Pubblico su GitHub...
git add -A
git commit -m "accendi sicurix %date% %time%" >nul 2>&1
git pull --no-rebase --no-edit origin main >nul 2>&1
git push origin main

REM --- 4) avvio i workflow ---
echo [i] Avvio le automazioni...
for %%W in (sicurix_daily.yml kie_shorts.yml ytcashcow81.yml sicurix_tales_ateco.yml fliki_daily.yml tales_optimize.yml matrix_backup.yml omnipresence.yml) do (
  gh workflow run %%W >nul 2>&1 & echo   run %%W
)

echo.
echo [OK] FATTO. Il canale @sicurissimo e i social ora girano H24 7/7.
echo    Restano solo (se non gia' fatti): verifica canale su youtube.com/verify per le thumbnail custom.
echo    Ogni mattina trovi i 3 video del giorno in: OGGI_SICURIX.md
start "" https://github.com/PlanB76/81plus-automation/actions
pause
