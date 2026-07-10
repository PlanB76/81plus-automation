@echo off
REM ============================================================
REM  GENERA I TOKEN YOUTUBE 81+ (token unico a 3 scope per canale)
REM  Metti il file client_secret_*.json in QUESTA cartella, poi lancia.
REM  Crea: token_sicurissimo.json  e  token_destino.json
REM  Poi incolli il contenuto nei secret GitHub (istruzioni a schermo).
REM ============================================================
setlocal
cd /d "%~dp0"
echo [1/3] Installo le dipendenze...
python -m pip install --quiet --upgrade google-auth-oauthlib google-api-python-client

echo.
echo [2/3] Genero il token per @sicurissimo
echo      -> nel browser accedi con l'account che gestisce @sicurissimo.
python genera_token_youtube.py "" token_sicurissimo.json
echo.
echo Fatto @sicurissimo. Ora @destinorandagio.
pause

echo.
echo [3/3] Genero il token per @destinorandagio
echo      -> nel browser accedi con l'account che gestisce @destinorandagio.
python genera_token_youtube.py "" token_destino.json

echo.
echo ============================================================
echo  FATTO. Ora apri i due file e incolla il contenuto nei secret:
echo   token_sicurissimo.json  -> secret  YOUTUBE_TOKEN_JSON
echo   token_destino.json      -> secret  YOUTUBE_TOKEN_JSON_DESTINO
echo  (GitHub: PlanB76/81plus-automation ^> Settings ^> Secrets ^> Actions)
echo ============================================================
pause
