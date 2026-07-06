@echo off
REM ============================================================
REM  PROVA SICURIX - test locale: genera 3 pagine + rende 3 immagini WEBP
REM  La API key NON e' nel file: viene letta da 81plus_secrets.env (che compili tu).
REM  Riga richiesta nel file:  OPENAI_API_KEY=sk-....
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

if not exist "81plus_secrets.env" (
  echo [!] Manca 81plus_secrets.env . Copia 81plus_secrets.env.TEMPLATE in 81plus_secrets.env e incolla la tua OPENAI_API_KEY.
  pause & exit /b 1
)

REM carica OPENAI_API_KEY dal file secret (senza mostrarla)
for /f "usebackq tokens=1,* delims==" %%a in ("81plus_secrets.env") do (
  if /i "%%a"=="OPENAI_API_KEY" set "OPENAI_API_KEY=%%b"
  if /i "%%a"=="OPENAI_IMAGE_MODEL" set "OPENAI_IMAGE_MODEL=%%b"
)
if "%OPENAI_API_KEY%"=="" (
  echo [!] OPENAI_API_KEY non trovata dentro 81plus_secrets.env
  pause & exit /b 1
)
if "%OPENAI_IMAGE_MODEL%"=="" set "OPENAI_IMAGE_MODEL=gpt-image-1"

echo [SICURIX] Installo Pillow (se serve)...
python -m pip install --quiet pillow

echo [SICURIX] 1) Genero 3 pagine di prova...
python cloud\sicurix_gen_daily.py 3
if errorlevel 1 ( echo [!] Errore generazione & pause & exit /b 1 )

echo [SICURIX] 2) Rendo 3 immagini WEBP con %OPENAI_IMAGE_MODEL% ...
python cloud\render_images.py 3
if errorlevel 1 ( echo [!] Errore render immagini & pause & exit /b 1 )

echo.
echo [OK] Fatto. Apro la cartella immagini di prova...
start "" "%~dp0cloud\out\img"
echo [i] Controlla che lo stile SICURIX (mattoncini, nero/bianco/arancione, logo 81+, PERICOLO/METODO81+) sia giusto.
pause
endlocal
