@echo off
REM ===== BLOG81+ / PACK81+ — un clic: articolo del giorno + ciclo pack + iniezione index =====
REM Da fondere in AVVIA_81_GLOBALE.bat. Per pubblicare sui canali: aggiungi --send
cd /d "%~dp0"
python engine\scheduler.py
echo.
echo Fatto: blog81.html + promo\ + articolo aggiornati. (per pubblicare: python engine\scheduler.py --send)
pause
